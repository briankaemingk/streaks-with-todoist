import app

def main(api, task_id):
    now_date_user_time = app.get_now_user_timezone(api)
    print('Reminder - Now user time: ', str(now_date_user_time))
    task = api.items.get_by_id(task_id)
    print('Reminder - Task: ', task)
    now_date = app.datetime.utcnow()
    print('Reminder - Now date utc: ', now_date)
    now_date_user_time = app.get_now_user_timezone(api)
    now_date_all_day = app.update_to_all_day(now_date)
    print('Reminder - Now date all day: ', now_date_all_day)
    now_string_all_day = app.convert_datetime_str(now_date_all_day)
    print('Reminder - updating task from ', task['due_date_utc'], ' to ', now_string_all_day)
    task.update(due_date_utc=now_string_all_day)
