import app

def main(api, task_id):
    task = api.items.get_by_id(task_id)
    increment_streak(task)
    if check_recurring_task(api, task) and check_regular_intervals(task['date_string']): check_activity_log(task)


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


# TODO: Look back through activity log
# look back through the activity log to see if the current time is before the original due date. If so, skip the next occurence.
def check_activity_log(task):
    print(task['date_string'])


    # [{'parent_project_id': 2164239297, 'event_type': 'updated', 'object_type': 'item', 'object_id': 2810317507,
    #   'initiator_id': None, 'parent_item_id': None, 'event_date': 'Tue 11 Sep 2018 23:35:07 +0000',
    #   'extra_data': {'content': 'TT', 'due_date': 'Thu 13 Sep 2018 06:59:59 +0000',
    #                  'last_due_date': 'Fri 14 Sep 2018 06:59:59 +0000', 'client': 'Mozilla/5.0; Todoist/913'},
    #   'id': 4699573747} ]