import settings
from todoist.api import TodoistAPI
from flask import jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os, requests, string, random, hmac, base64, hashlib, logging, atexit, pytz, daily, task_complete, re
import pytz
import reminder_fired
import task_updated
import task_added
from dateutil.parser import parse
from datetime import datetime
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

# Generate 6 random digits
state = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
url = 'https://todoist.com/oauth/authorize?state=' + state + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from models import User

# Index page initiates a user's token
@app.route('/')
def index():
    return 'Streaks with Todoist: Click <a href=' + url + '>here</a> to connect your account.<br><br>Visit our <a href=https://github.com/briankaemingk/streaks-with-todoist>Github page</a> for more info or to submit a bug.'


# Callback set on the management console authorizes a user
@app.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state and code:
        if state != state:
            return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'
        access_token = initialize_token(code)
        api = initiate_api(access_token)
        user_id = api.state['user']['id']
        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar() is not None
        if not user_exists:
            u = User(user_id, access_token)
            db.session.add(u)
            db.session.commit()
            initialize_cron_job(api)
            return 'Complete'
        else:
            u = User.query.filter_by(id=user_id).first()
            u.access_token = access_token
            db.session.commit()
            return 'Streaks with Todoist re-authorized.'
    else: return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'


# Routes webhooks to various actions
@app.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    event_id = request.headers.get('X-Todoist-Delivery-ID')
    if event_id is not None and compute_hmac():
        user_id = request.json['user_id']
        user_exists = db.session.query(User.id).filter_by(id=user_id).scalar() is not None
        if user_exists:
            user = User.query.get(user_id)
            api = initiate_api(user.access_token)
            local_time = str(get_now_user_timezone(api))

            if request.json['event_name'] == 'item:completed':
                print(request.headers)
                print(request.json)
                item_id = int(request.json['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    # Avoiding duplicates: if webhook callback content matches api content
                    if request.json['event_data']['content'] == content:
                        print(local_time + ': Task complete: ' + content)
                        task_complete.main(api, item_id)
                        item = api.items.get_by_id(item_id)
                        content = item['content']
                        print(local_time + ': After task complete: ' + content)
            if request.json['event_name'] == 'reminder:fired':
                item_id = int(request.json['event_data']['item_id'])
                if api.items.get_by_id(item_id) is not None:
                    task = api.items.get_by_id(item_id)
                    print(local_time + ': Reminder fired: ' + task['content'])
                    reminder_fired.main(api, item_id)
            if request.json['event_name'] == 'item:updated':
                item_id = int(request.json['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    print(local_time + ': Task updated: ' + content)
                    task_updated.main(api, item_id)
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    print(local_time + ': After task updated: ' + content)
            if request.json['event_name'] == 'item:added':
                item_id = int(request.json['event_data']['id'])
                if api.items.get_by_id(item_id) is not None:
                    item = api.items.get_by_id(item_id)
                    content = item['content']
                    print(local_time + ': Task added: ' + content)
                    task_added.main(api, item_id)
            api.commit()
            return jsonify({'status': 'accepted', 'request_id': event_id}), 200
        else:
            return jsonify({'status': 'rejected',
                            'reason': 'malformed request'}), 400
    else:
        return jsonify({'status': 'rejected',
                        'reason': 'malformed request'}), 400

### END POINTS FOR DB TESTING
@app.route('/createuser')
def createuser():
    id = request.args.get('id', None)
    token = request.args.get('access_token', None)
    u = User(id, token)
    db.session.add(u)
    db.session.commit()
    return 'user {} created'.format(id)

@app.route('/listusers')
def listusers():
    user_list = User.query.order_by(User.id).all()
    if user_list:
        return_string = 'All users: '
        for u in user_list:
            return_string += '{}, {};'.format(u.id, u.access_token)
    else:
        return_string = 'No Users in Database'

    return return_string


# Gets the authorization code from the oauth callback and routes it to get the access token
def initialize_token(code):
    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url='https://todoist.com/oauth/access_token?', data=data)
    # extracting response text
    content = r.json()
    access_token = content['access_token']
    return access_token


# Create scheduled job to run after app token is initialized
def initialize_cron_job(api):
    scheduler = BackgroundScheduler(timezone=get_user_timezone(api))
    scheduler.add_job(daily.main, 'cron', args=[api, get_user_timezone(api)], hour=0, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


# Initiate and sync Todoist API
def initiate_api(access_token):
    api = TodoistAPI(access_token)
    api.sync()
    return api


# Take payload and compute hmac--check if user-agent matches to todoist webhooks
def compute_hmac():
    if request.headers.get('USER-AGENT') == 'Todoist-Webhooks':
        request_hmac = request.headers.get('X-Todoist-Hmac-SHA256')
        calculated_hmac = base64.b64encode(hmac.new(bytes(os.getenv('CLIENT_SECRET'), encoding='utf-8'), msg=request.get_data(), digestmod=hashlib.sha256).digest()).decode("utf-8")
        if request_hmac == calculated_hmac: return 1
        else: return 0


# Determine if text has content text[streak n]
def is_habit(text):
    return re.search(r'\[streak\s(\d+)\]', text)


# Update streak contents from text [streak n] to text [streak n+1]
def update_streak(task, streak):
    streak_num = '[streak {}]'.format(streak)
    new_content = re.sub(r'\[streak\s(\d+)\]', streak_num, task['content'])
    task.update(content=new_content)


# Update due date to end of today (default for all day tasks)
def update_to_all_day(now):
    new_due_date = datetime(year=now.year,
                            month=now.month,
                            day=now.day,
                            hour=23,
                            minute=59,
                            second=59).astimezone(pytz.utc)
    return new_due_date

# Parse time string, convert to datetime object in user's timezone
def convert_time_str_datetime(time_str, user_timezone):

    try:
        # In format Fri 23 Nov 2018 18:00:00 +0000
        datetime_obj = datetime.strptime(time_str, '%a %d %b %Y %H:%M:%S %z')
    except ValueError or TypeError: return None
    dt_local = datetime_obj.astimezone(user_timezone)
    return dt_local

# Get user's timezone
def get_user_timezone(api):
    todoist_tz = api.state["user"]["tz_info"]["timezone"]
    match = re.search("GMT( ((\+|\-)(\d+)))?", todoist_tz)

    if match:
        if match.group(3) == '+': operation = '-'
        else: operation = '+'
        GMT_tz = 'Etc/GMT' + operation + match.group(4)
        return pytz.timezone(GMT_tz)

    else: return pytz.timezone(api.state["user"]["tz_info"]["timezone"])


# Get current time in user's timezone
def get_now_user_timezone(api):
    user_timezone = get_user_timezone(api)
    return datetime.now(tz=user_timezone)


# Convert a datetime object into the todoist due date string format
def convert_datetime_str(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')


if __name__ == '__main__':
    app.run()
