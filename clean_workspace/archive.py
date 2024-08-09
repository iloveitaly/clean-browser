import datetime
import os
from todoist_api_python.api import TodoistAPI

def archive_old_tasks():
    key = os.environ.get("TODOIST_API_KEY", None)
    assert key is not None
    api = TodoistAPI(key)

    tasks = api.get_tasks()
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    archived_content = ""

    for task in tasks:
        task_date = datetime.datetime.strptime(task.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        if task_date < one_year_ago:
            task_content = f"# {task_date.strftime('%Y-%m-%d')}\n\n{task.content}"
            archived_content += task_content + "\n\n"
            api.close_task(task.id)

    if archived_content:
        print(archived_content)
