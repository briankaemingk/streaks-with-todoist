import atexit
import base64
import hashlib
import hmac
import os
import random
import re
import string
from datetime import datetime

import pytz
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from todoist import TodoistAPI

from app.extensions import db
from app.user.models import User
from flask import jsonify, request
import task_complete, reminder_fired, task_updated, task_added

def process_webhook(event_id, req):
    if event_id is not None and compute_hmac():
        user_id = req['user_id']
        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar() is not None
        if user_exists:
            user = User.query.get(user_id)
            api = initiate_api(user.access_token)
            local_time = str(get_now_user_timezone(api))

            if req['event_name'] == 'item:completed':
                item_id = int(req['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    # Avoiding duplicates: if webhook callback content matches api content
                    if req['event_data']['content'] == content:
                        task_complete.main(api, item_id)
                        item = api.items.get_by_id(item_id)
                        content = item['content']
            if req['event_name'] == 'reminder:fired':
                item_id = int(req['event_data']['item_id'])
                if api.items.get_by_id(item_id) is not None:
                    task = api.items.get_by_id(item_id)
                    print(local_time + ': Reminder fired: ' + task['content'])
                    reminder_fired.main(api, item_id)
            if req['event_name'] == 'item:updated':
                item_id = int(req['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    task_updated.main(api, item_id)
                    item = api.items.get_by_id(item_id)
                    content = item['content']
            if req['event_name'] == 'item:added':
                item_id = int(req['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    task_added.main(api, item_id)
            api.commit()
            return jsonify({'status': 'accepted', 'request_id': event_id}), 200
        else:
            return jsonify({'status': 'rejected',
                            'reason': 'malformed request'}), 400
    else:
        return jsonify({'status': 'rejected',
                        'reason': 'malformed request'}), 400


def convert_time_str_datetime(time_str, user_timezone):
    """Parse time string, convert to datetime object in user's timezone"""

    try:
        # In format Fri 23 Nov 2018 18:00:00 +0000
        datetime_obj = datetime.strptime(time_str, '%a %d %b %Y %H:%M:%S %z')
    except ValueError or TypeError: return None
    dt_local = datetime_obj.astimezone(user_timezone)
    return dt_local


# Determine if text has content text[streak n]
def is_habit(text):
    return re.search(r'\[streak\s(\d+)\]', text)


def update_streak(task, streak):
    """Update streak contents from text [streak n] to text [streak n+1]"""
    streak_num = '[streak {}]'.format(streak)
    new_content = re.sub(r'\[streak\s(\d+)\]', streak_num, task['content'])
    task.update(content=new_content)


def get_now_user_timezone(api):
    """Get current time in user's timezone"""
    user_timezone = get_user_timezone(api)
    return datetime.now(tz=user_timezone)


def initiate_api(access_token):
    """Initiate and sync Todoist API"""
    api = TodoistAPI(access_token)
    api.sync()
    return api


def compute_hmac():
    """Take payload and compute hmac--check if user-agent matches to todoist webhooks"""
    if request.headers.get('USER-AGENT') == 'Todoist-Webhooks':
        request_hmac = request.headers.get('X-Todoist-Hmac-SHA256')
        calculated_hmac = base64.b64encode(hmac.new(bytes(os.getenv('CLIENT_SECRET'), encoding='utf-8'), msg=request.get_data(), digestmod=hashlib.sha256).digest()).decode("utf-8")
        if request_hmac == calculated_hmac: return 1
        else: return 0


def update_to_all_day(now):
    """Update due date to end of today (default for all day tasks)"""
    new_due_date = datetime(year=now.year,
                            month=now.month,
                            day=now.day,
                            hour=23,
                            minute=59,
                            second=59).astimezone(pytz.utc)
    return new_due_date


def get_user_timezone(api):
    """Get user's timezone"""
    todoist_tz = api.state["user"]["tz_info"]["timezone"]
    match = re.search("GMT( ((\+|\-)(\d+)))?", todoist_tz)

    if match:
        if match.group(3) == '+': operation = '-'
        else: operation = '+'
        GMT_tz = 'Etc/GMT' + operation + match.group(4)
        return pytz.timezone(GMT_tz)

    else: return pytz.timezone(api.state["user"]["tz_info"]["timezone"])


def convert_datetime_str(date):
    """Convert a datetime object into the todoist due date string format"""
    return date.strftime('%Y-%m-%dT%H:%M:%S')


def create_url():
    # Generate 6 random digits
    state = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    url = 'https://todoist.com/oauth/authorize?state=' + state + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'
    return url


def initialize_token(code):
    """Gets the authorization code from the oauth callback and routes it to get the access token"""
    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url='https://todoist.com/oauth/access_token?', data=data)
    # extracting response text
    content = r.json()
    access_token = content['access_token']
    return access_token


def initialize_cron_job(api):
    """Create scheduled job to run after app token is initialized"""
    scheduler = BackgroundScheduler(timezone=get_user_timezone(api))
    scheduler.add_job(daily.main, 'cron', args=[api, get_user_timezone(api)], hour=0, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())