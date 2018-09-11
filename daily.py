import app
import pytz
from dateutil.parser import parse
from datetime import datetime, timedelta


# Identify overdue streaks, reset the streak, and schedule them for all day
def main(api, user_timezone):
    now = datetime.now(tz=user_timezone)
    tasks = api.state['items']
    for task in tasks:
        due_date_utc = task["due_date_utc"]
        if due_date_utc:
            due_date = convert_time_str_datetime(due_date_utc, user_timezone)
            # If the task is due yesterday and it is a habit
            if app.is_habit(task['content']) and is_due_yesterday(due_date, now):
                app.update_streak(task, 0)
                task.update(due_date_utc=update_to_all_day(now))
                task.update(date_string=task['date_string'] + ' starting tod')
                print(task['date_string'])
                api.commit()


# Parse time string, convert to datetime object in user's timezone
def convert_time_str_datetime(time_str, user_timezone):
    return parse(time_str).astimezone(user_timezone)


# If the due date is yesterday
def is_due_yesterday(due_date, now):
    yesterday = now - timedelta(1)
    yesterday.strftime('%m-%d-%y')
    if due_date.strftime('%m-%d-%y') == yesterday.strftime('%m-%d-%y') : return 1


# Update due date to end of today (default for all day tasks)
def update_to_all_day(now):
    new_due_date = datetime(year=now.year,
                            month=now.month,
                            day=now.day,
                            hour=23,
                            minute=59,
                            second=59).astimezone(pytz.utc)
    return new_due_date
