import app

def main(api, task_id):
    task = api.items.get_by_id(task_id)
    due_date_utc = task["due_date_utc"]
    due_date = app.convert_time_str_datetime(due_date_utc, app.get_user_timezone(api))
    now = app.get_now_user_timezone(api)

    # If the task is due today and it is due in the past
    if due_date <= now and due_date.date() == now.date():
        task.update(due_date_utc=app.update_to_all_day(now))
