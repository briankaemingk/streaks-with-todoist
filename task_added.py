import re


def main(api, task_id):
    task = api.items.get_by_id(int(task_id))
    content = task['content']
    if '{' in content and '}' in content:
        comment = re.findall('\{.*\}', content)[0]
    content_no_comment = content.replace(comment, '')
    task.update(content=content_no_comment)
    api.notes.add(task_id, comment) 
