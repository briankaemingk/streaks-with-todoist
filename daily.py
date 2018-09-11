import app
from datetime import datetime, timedelta


# Identify overdue streaks, reset the streak, and schedule them for all day
def main(api, user_timezone):
    now = app.get_now_user_timezone(api)
    tasks = api.state['items']
    for task in tasks:
        due_date_utc = task["due_date_utc"]
        if due_date_utc:
            due_date = app.convert_time_str_datetime(due_date_utc, user_timezone)
            # If the task is due yesterday and it is a habit
            if app.is_habit(task['content']) and is_due_yesterday(due_date, now):
                app.update_streak(task, 0)
                task.update(due_date_utc=app.update_to_all_day(now))
                task.update(date_string=task['date_string'] + ' starting tod')
                print(task['date_string'])
                api.commit()


# If the due date is yesterday
def is_due_yesterday(due_date, now):
    yesterday = now - timedelta(1)
    yesterday.strftime('%m-%d-%y')
    if due_date.strftime('%m-%d-%y') == yesterday.strftime('%m-%d-%y') : return 1


