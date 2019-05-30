import base64
import hashlib
import hmac
import os
import random
import re
import string
from datetime import datetime, timedelta
import pytz
from flask import request
from todoist import TodoistAPI


def process_webhook(req, user):
    api = initiate_api(user.access_token)
    local_time = str(get_now_user_timezone(api))

    if req['event_name'] == 'item:completed':
        item_id = int(req['event_data']['id'])
        if api.items.get_by_id(item_id) is not None:
            item = api.items.get_by_id(item_id)
            content = item['content']
            # Avoiding duplicates: if webhook callback content matches api content
            if req['event_data']['content'] == content:
                task_complete(api, item_id)
    if req['event_name'] == 'item:uncompleted':
        item_id = int(req['event_data']['id'])
        if api.items.get_by_id(item_id) is not None:
            item = api.items.get_by_id(item_id)
            content = item['content']
            # Avoiding duplicates: if webhook callback content matches api content
            if req['event_data']['content'] == content:
                task_uncomplete(api, item_id)
    if req['event_name'] == 'reminder:fired':
        item_id = int(req['event_data']['item_id'])
        if api.items.get_by_id(item_id) is not None:
            task = api.items.get_by_id(item_id)
            print(local_time + ': Reminder fired: ' + task['content'])
            reminder_fired(api, item_id)
    if req['event_name'] == 'item:updated':
        item_id = int(req['event_data']['id'])
        if api.items.get_by_id(item_id) is not None:
            item = api.items.get_by_id(item_id)
            content = item['content']
            task_updated(api, item_id)
            item = api.items.get_by_id(item_id)
            content = item['content']
    if req['event_name'] == 'item:added':
        item_id = int(req['event_data']['id'])
        if api.items.get_by_id(item_id) is not None:
            item = api.items.get_by_id(item_id)
            content = item['content']
            task_added(api, item_id)
    api.commit()


def convert_time_str_datetime(time_str, user_timezone):
    """Parse time string, convert to datetime object in user's timezone"""

    try:
        # In format Fri 23 Nov 2018 18:00:00 +0000
        datetime_obj = datetime.strptime(time_str, '%a %d %b %Y %H:%M:%S %z')
    except ValueError or TypeError: return None
    dt_local = datetime_obj.astimezone(user_timezone)
    return dt_local


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


def task_updated(api, task_id):
    """TODO: Add logic for finding <> and replacing due time"""
    task = api.items.get_by_id(task_id)
    if task["due_date_utc"] and is_recurrence_diff(task['content']):
        new_due_time = is_recurrence_diff(task["content"]).group(1)
        new_due_date_utc = replace_due_date_time(new_due_time, task["due_date_utc"], get_user_timezone(api))
        new_due_date_utc_str = convert_datetime_str(new_due_date_utc)
        task.update(content=re.sub(is_recurrence_diff(task["content"]).group(0), '', task["content"]))
        task.update(due_date_utc=new_due_date_utc_str)

    ##TODO: Extend feature to others
    if api['user']['email'] == 'brian.e.k@gmail.com':
        if api.state['user']['is_premium']:
            if task["due_date_utc"] != None :
                if 'P4' not in task['content']:
                    if 'last_due_date' in api.activity.get(object_id=task['id'], limit=1)[0]['extra_data']:
                        if api.activity.get(object_id=task['id'], limit=1)[0]['extra_data']['last_due_date'] == None:
                            task.update(priority=3)
                else :
                    content_no_P4 = task['content'].replace('P4', '')
                    task.update(content=content_no_P4)


def is_recurrence_diff(task_content):
    """Find hours, minutes and, optionally, seconds"""
    return re.search(r'<(\d+:\d+:*\d*)*>', task_content)


def replace_due_date_time(new_due_time, due_date_utc, user_timezone):
    """Replace with the user-entered hour, minute and, optionally, second, and convert to utc datetime object"""
    due_date_localtz_date = convert_time_str_datetime(due_date_utc, user_timezone)
    if(new_due_time):
        new_due_time_split = new_due_time.split(":")
        new_due_date_localtz_date = due_date_localtz_date.replace(hour=int(new_due_time_split[0]),
                                                              minute=int(new_due_time_split[1]),
                                                              second= int(0))
    else:
        new_due_date_localtz_date = due_date_localtz_date.replace(hour=23, minute=23, second= 59)
    new_due_date_utc_date = new_due_date_localtz_date.astimezone(pytz.utc)
    return new_due_date_utc_date


def task_complete(api, task_id):
    task = api.items.get_by_id(int(task_id))
    if task is not None:
        if api.state['user']['is_premium'] and task['date_string'] is not None:
            if check_recurring_task(api, task) and check_regular_intervals(task['date_string']): check_activity_log(api, task)
        increment_streak(task)

        # Turn on OOO
        if task['content'] == 'ooo mode' and api.projects.get_by_id(task['project_id'])['name'] == 'crt' :
            for filter in api.filters.state['filters'] :
                if filter['name'] == 'Level 1' : filter.update(query = '(overdue | (due after: tod 23:59 & due before: tom 00:00)) & !(##work & P4)')
                elif filter['name'] == 'Level 2' : filter.update(query = 'search:_____ | overdue | (due after: tod 23:59 & due before: tom 00:00) | (@tDE & ! no due date) | (tom & @t2D) | (next 5 days & @t5D) | (next 8 days & @tW) | (next 32 days & @tM) & !##work')


def task_uncomplete(api, task_id):
    task = api.items.get_by_id(int(task_id))
    # Turn on OOO
    if task['content'] == 'ooo mode' and api.projects.get_by_id(task['project_id'])['name'] == 'crt':
        for filter in api.filters.state['filters']:
            if filter['name'] == 'Level 1': filter.update(
                query='overdue | (due after: tod 23:59 & due before: tom 00:00)')
            elif filter['name'] == 'Level 2': filter.update(
                query='search:_____ | overdue | (due after: tod 23:59 & due before: tom 00:00) | (@tDE & ! no due date) | (tom & @t2D) | (next 5 days & @t5D) | (next 8 days & @tW) | (next 32 days & @tM)')


def increment_streak(task):
    """If a task is a habit, increase the streak by +1"""
    content = task['content']
    if is_habit(content):
        habit = is_habit(content)
        streak = int(habit.group(1)) + 1
        update_streak(task, streak)


def check_recurring_task(api, task):
    """Check if it is a recurring task: if not able to parse date string into a date, then it is a recurring task"""
    if not(
    convert_time_str_datetime(task['date_string'], get_user_timezone(api))): return 1


def check_regular_intervals(date_str):
    """If a recurring task that repeats at regular intervals from the original task date is completed, it will not have an '!'"""
    if '!' not in date_str : return 1


def check_activity_log(api, task):
    """Look back through the activity log to see if the current time is before the original due date. If so, skip the next occurence."""
    # Find last 2 completed objects in activity log, including this one
    completed_logs = api.activity.get(object_type='item', event_type='completed', object_id=task['id'], limit=2)

    # Catch timeout error
    i = 1
    while completed_logs == '<html><head><title>Timeout</title></head><body><h1>Timeout</h1></body></html>':
        print("Completed logs TIMEOUT error, retry #", i)
        i += 1
        completed_logs = api.activity.get(object_type='item', event_type='completed', object_id=task['id'], limit=2)

    # If there's only one record of completion (the one that caused this webhook to fire)
    if len(completed_logs) == 1:
        update_logs = api.activity.get(object_type='item', event_type='updated', object_id=task['id'], limit=100)
        date_update_logs = [update_log for update_log in update_logs if 'last_due_date' in update_log['extra_data']]
        # If there was a modification to a date
        if(date_update_logs):
            # Get the last due date in the regular cycle
            if date_update_logs[-1]['extra_data']['last_due_date'] is not None:
                last_regular_due_date_str = date_update_logs[-1]['extra_data']['last_due_date']
                last_regular_due_date = convert_time_str_datetime(last_regular_due_date_str, pytz.utc)
                if datetime.now(tz=get_user_timezone(api)).date() < last_regular_due_date.date():
                    task.close()
    # Otherwise if there is more than one completion
    elif len(completed_logs) > 1:
        last_complete_date = convert_time_str_datetime(completed_logs[-1]['event_date'], pytz.utc)
        last_completed_date_str = convert_datetime_str(last_complete_date)
        # Get all changes to this task since the last completion time
        update_logs = api.activity.get(object_type='item', event_type='updated', object_id=task['id'], since=last_completed_date_str, limit=100)
        date_update_logs = [update_log for update_log in update_logs if 'last_due_date' in update_log['extra_data']]
        if(date_update_logs):
            # Get the last due date in the regular cycle
            last_regular_due_date_str = date_update_logs[-1]['extra_data']['last_due_date']
            last_regular_due_date = convert_time_str_datetime(last_regular_due_date_str, get_user_timezone(api))
            if datetime.now(tz=get_user_timezone(api)).date() < last_regular_due_date.date():
                task.close()


def check_if_due_today(date, api):
    """Check if the task is due today"""
    if date.date() == get_now_user_timezone(api): return 1


def task_added(api, task_id):
    task = api.items.get_by_id(int(task_id))
    if api.state['user']['is_premium']:
        content = task['content']
        if '{' in content and '}' in content:
            comment = re.findall('\{.*\}', content)[0]
            content_no_comment = content.replace(comment, '')
            task.update(content=content_no_comment)
            api.notes.add(task_id, comment[1:-1])

    ##TODO: Extend feature to others
    if api['user']['email'] == 'brian.e.k@gmail.com':
        if task['due_date_utc'] != None :
            if 'P4' not in task['content']:
                task.update(priority=3)
            else:
                content_no_P4 = task['content'].replace('P4', '')
                task.update(content=content_no_P4)


def reminder_fired(api, task_id):
    task = api.items.get_by_id(task_id)
    now_date = get_now_user_timezone(api)
    now_date_all_day = update_to_all_day(now_date)
    now_string_all_day = convert_datetime_str(now_date_all_day)
    print('Reminder - updating task from ', task['due_date_utc'], ' to ', now_string_all_day)
    task.update(due_date_utc=now_string_all_day)


def daily():
    """Identify overdue streaks, reset the streak, and schedule them for all day"""
    print('Timer on main called')
    # now = get_now_user_timezone(api)
    # tasks = api.state['items']
    # for task in tasks:
    #     due_date_utc = task["due_date_utc"]
    #     if due_date_utc:
    #         due_date = convert_time_str_datetime(due_date_utc, user_timezone)
    #         # If the task is due yesterday and it is a habit
    #         if is_habit(task['content']) and is_due_yesterday(due_date, now):
    #             update_streak(task, 0)
    #             task.update(due_date_utc=update_to_all_day(now))
    #             task.update(date_string=task['date_string'] + ' starting tod')
    #             print(task['date_string'])
    #             api.commit()


def is_due_yesterday(due_date, now):
    """If the due date is yesterday"""
    yesterday = now - timedelta(1)
    yesterday.strftime('%m-%d-%y')
    if due_date.strftime('%m-%d-%y') == yesterday.strftime('%m-%d-%y') : return 1