import app, re, pytz

# TODO: Add logic for finding <> and replacing due time
def main(api, task_id):
    task = api.items.get_by_id(task_id)
    if task["due_date_utc"] and is_recurrence_diff(task['content']):
        new_due_time = is_recurrence_diff(task["content"]).group(1)
        new_due_date_utc = replace_due_date_time(new_due_time, task["due_date_utc"], app.get_user_timezone(api))
        new_due_date_utc_str = app.convert_datetime_str(new_due_date_utc)
        task.update(content=re.sub(is_recurrence_diff(task["content"]).group(0), '', task["content"]))
        task.update(due_date_utc=new_due_date_utc_str)


# Find hours, minutes and, optionally, seconds
def is_recurrence_diff(task_content):
    return re.search(r'<(\d+:\d+:*\d*)*>', task_content)

# Replace with the user-entered hour, minute and, optionally, second, and convert to utc datetime object
def replace_due_date_time(new_due_time, due_date_utc, user_timezone):
    due_date_localtz_date = app.convert_time_str_datetime(due_date_utc, user_timezone)
    if(new_due_time):
        new_due_time_split = new_due_time.split(":")
        new_due_date_localtz_date = due_date_localtz_date.replace(hour=int(new_due_time_split[0]),
                                                              minute=int(new_due_time_split[1]),
                                                              second= int(0))
    else:
        new_due_date_localtz_date = due_date_localtz_date.replace(hour=23, minute=23, second= 59)
    new_due_date_utc_date = new_due_date_localtz_date.astimezone(pytz.utc)
    return new_due_date_utc_date