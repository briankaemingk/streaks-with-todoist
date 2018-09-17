from todoist.api import TodoistAPI
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os, requests, string, random, hmac, base64, hashlib, logging, atexit, pytz, daily, task_complete, re
import pytz
import reminder_fired
import task_updated
from dateutil.parser import parse
from datetime import datetime
import time

app = Flask(__name__)

# Index page initiates a user's token
@app.route('/')
def index():
    # Generate 6 random digits
    os.environ['STATE'] = (''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
    url = 'https://todoist.com/oauth/authorize?state=' + os.getenv('STATE') + '&client_id=' + os.getenv('CLIENT_ID') + '&scope=data:read_write'
    return 'Streaks with Todoist: Click <a href=' + url + '>here</a> to connect your account.'


# Callback set on the management console authorizes a user
@app.route('/oauth_callback')
def oauth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if state != os.getenv('STATE') or request.args.get('error'):
        return 'Request for Streaks with Todoist not authorized, exiting. Go <a href=' + "/" + '>back</a>'
    initialize_token(code)
    api = initiate_api()
    initialize_cron_job(api)
    return 'Complete'


# Routes webhooks to various actions
@app.route('/webhook_callback', methods=['POST'])
def webhook_callback():
    event_id = request.headers.get('X-Todoist-Delivery-ID')
    if compute_hmac(event_id):
        api = initiate_api()
        if request.json['event_name'] == 'item:completed':
            task_complete.main(api, int(request.json['event_data']['id']))
        if request.json['event_name'] == 'reminder:fired':
            reminder_fired.main(api, int(request.json['event_data']['item_id']))
        if request.json['event_name'] == 'item:updated':
            task_updated.main(api, int(request.json['event_data']['id']))
        api.commit()
        return jsonify({'status': 'accepted', 'request_id': event_id}), 200
    else:
        return jsonify({'status': 'rejected',
                        'reason': 'malformed request'}), 400


# Gets the authorization code from the oauth callback and routes it to get the access token
def initialize_token(code):
    data = {'client_id' : os.getenv('CLIENT_ID'), 'client_secret' : os.getenv('CLIENT_SECRET'), 'code' : code}
    # sending post request and saving response as response object
    r = requests.post(url='https://todoist.com/oauth/access_token?', data=data)
    # extracting response text
    content = r.json()
    access_token = content['access_token']
    #TODO: Change this from environment variable to database
    os.environ["TODOIST_APIKEY"] = access_token


# TODO: Test the reset streak in prod on server
# Create scheduled job to run after app token is initialized
def initialize_cron_job(api):
    scheduler = BackgroundScheduler(timezone=get_user_timezone(api))
    scheduler.add_job(daily.main, 'cron', args=[api, get_user_timezone(api)], hour=0, minute=0)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())


# Get user's Todoist API Key
def get_token():
    token = os.getenv('TODOIST_APIKEY')
    return token

# Initiate and sync Todoist API
def initiate_api():
    TODOIST_APIKEY = get_token()
    if not TODOIST_APIKEY:
        logging.warning('Please set the API token in environment variable.')
        exit()
    api = TodoistAPI(TODOIST_APIKEY)
    api.sync()
    return api


# Take payload and compute hmac--check if user-agent matches to todoist webhooks
def compute_hmac(event_id):
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
        return parse(time_str).astimezone(user_timezone)
    except ValueError: return None

# Get user's timezone
def get_user_timezone(api):
    return pytz.timezone(api.state["user"]["tz_info"]["timezone"])


# Get current time in user's timezone
def get_now_user_timezone(api):
    user_timezone = get_user_timezone(api)
    return datetime.now(tz=user_timezone)


# Convert a datetime object into the todoist due date string format
def convert_datetime_str(date):
    return date.strftime('%Y-%m-%dT%H:%M:%S')


if __name__ == '__main__':
    app.run()
