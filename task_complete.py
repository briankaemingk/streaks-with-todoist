import app

# If a task is a habit, increase the streak by +1
def main(api, task_id):
    task = api.items.get_by_id(task_id)
    content = task['content']
    if app.is_habit(content):
        habit = app.is_habit(content)
        streak = int(habit.group(1)) + 1
        app.update_streak(task, streak)



