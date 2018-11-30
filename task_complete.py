import app, time
from datetime import timedelta

def main(api, task_id):
    task = api.items.get_by_id(int(task_id))
    if api.state['user']['is_premium'] and task is not None:
        if check_recurring_task(api, task) and check_regular_intervals(task['date_string']): check_activity_log(api, task)
    increment_streak(task)


# If a task is a habit, increase the streak by +1
def increment_streak(task):
    content = task['content']
    if app.is_habit(content):
        habit = app.is_habit(content)
        streak = int(habit.group(1)) + 1
        app.update_streak(task, streak)


# Check if it is a recurring task: if not able to parse date string into a date, then it is a recurring task
def check_recurring_task(api, task):
    if 'date_string' in task:
        if not(app.convert_time_str_datetime(task['date_string'], app.get_user_timezone(api))): return 1


# If a recurring task that repeats at regular intervals from the original task date is completed, it will not have an '!'
def check_regular_intervals(date_str):
    if '!' not in date_str : return 1


# Look back through the activity log to see if the current time is before the original due date. If so, skip the next occurence.
def check_activity_log(api, task):
    # Find last 2 completed objects in activity log, including this one
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
                last_regular_due_date = app.convert_time_str_datetime(last_regular_due_date_str, app.pytz.utc)
                if app.datetime.now(tz=app.get_user_timezone(api)).date() < last_regular_due_date.date():
                    task.close()
    # Otherwise if there is more than one completion
    elif len(completed_logs) > 1:
        last_complete_date = app.convert_time_str_datetime(completed_logs[-1]['event_date'], app.pytz.utc)
        last_completed_date_str = app.convert_datetime_str(last_complete_date)
        # Get all changes to this task since the last completion time
        update_logs = api.activity.get(object_type='item', event_type='updated', object_id=task['id'], since=last_completed_date_str, limit=100)
        date_update_logs = [update_log for update_log in update_logs if 'last_due_date' in update_log['extra_data']]
        if(date_update_logs):
            # Get the last due date in the regular cycle
            last_regular_due_date_str = date_update_logs[-1]['extra_data']['last_due_date']
            last_regular_due_date = app.convert_time_str_datetime(last_regular_due_date_str, app.get_user_timezone(api))
            if app.datetime.now(tz=app.get_user_timezone(api)).date() < last_regular_due_date.date():
                task.close()

# Check if the task is due today
def check_if_due_today(date, api):
    if date.date() == app.get_now_user_timezone(api): return 1
