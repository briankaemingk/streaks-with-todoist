import app

def main(api, task_id):
    task = api.items.get_by_id(task_id)
    increment_streak(task)
    if check_recurring_task(api, task) and check_regular_intervals(task['date_string']): check_activity_log(api, task)


# If a task is a habit, increase the streak by +1
def increment_streak(task):
    content = task['content']
    if app.is_habit(content):
        habit = app.is_habit(content)
        streak = int(habit.group(1)) + 1
        app.update_streak(task, streak)

# Check if it is a recurring task: if not able to parse date string into a date, then it is a recurring task
def check_recurring_task(api, task):
    if not(app.convert_time_str_datetime(task['date_string'], app.get_user_timezone(api))): return 1


# If a recurring task that repeats at regular intervals from the original task date is completed, it will not have an '!'
def check_regular_intervals(date_str):
    if '!' not in date_str : return 1


# TODO: Add exceptions if task completion list isn't 2
# look back through the activity log to see if the current time is before the original due date. If so, skip the next occurence.
def check_activity_log(api, task):
    # Find last 2 completed objects in activity log, including this one
    completed_logs = api.activity.get(object_type=['item'], event_type = ['complete'], object_id=[task['id']], limit=2)
    # Find the last time that the item was completed and convert it to a date object
    last_complete_date = app.convert_time_str_datetime(completed_logs[1]['event_date'], app.pytz.utc)
    # Formatted as 2016-06-28T12:00.
    last_complete_date = convert_datetime_str(last_complete_date)
    # Find updated events to those that took place since the last completed task
    update_logs = api.activity.get(object_type=['item'], event_type = ['updated'], object_id=[task['id']], since=last_complete_date, limit=100)
    # Filter to logs involving due-date updates
    filtered_update_logs = [update_log for update_log in update_logs if 'last_due_date' in update_log['extra_data']]
    # Find the first time the date was changed since the last completion, which is the last regularily cycle due-date
    last_regular_due_date = filtered_update_logs[-1]['extra_data']['last_due_date']
    print(last_regular_due_date)

    # [{'parent_project_id': 2164239297, 'event_type': 'updated', 'object_type': 'item', 'object_id': 2810317507,
    #   'initiator_id': None, 'parent_item_id': None, 'event_date': 'Tue 11 Sep 2018 23:35:07 +0000',
    #   'extra_data': {'content': 'TT', 'due_date': 'Thu 13 Sep 2018 06:59:59 +0000',
    #                  'last_due_date': 'Fri 14 Sep 2018 06:59:59 +0000', 'client': 'Mozilla/5.0; Todoist/913'},
    #   'id': 4699573747} ]


# Convert a datetime object into the todoist due date string format
def convert_datetime_str(date):
    return date.strftime('%Y-%m-%dT%H:%M')