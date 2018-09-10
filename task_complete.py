from todoist.api import TodoistAPI
import re

# If a task is a habit, increase the streak by +1
def main(api, task_id):
    task = api.items.get_by_id(task_id)
    content = task['content']
    if is_habit(content):
        habit = is_habit(content)
        streak = int(habit.group(1)) + 1
        update_streak(task, streak)


# Update streak contents from text [streak n] to text [streak n+1]
def update_streak(task, streak):
    streak_num = '[streak {}]'.format(streak)
    new_content = re.sub(r'\[streak\s(\d+)\]', streak_num, task['content'])
    task.update(content=new_content)


# Determine if text has content text[streak n]
def is_habit(text):
    return re.search(r'\[streak\s(\d+)\]', text)

