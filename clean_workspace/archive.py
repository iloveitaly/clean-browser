import datetime
import os

from todoist_api_python.api import TodoistAPI

from .utils import _get_labels, _get_project, _todoist_api_key, only_one


def _create_filter(project_name: str, label: str) -> str:
    filter_str = f"#{project_name}"
    if label:
        filter_str += f" & @{label}"
    return filter_str


def _task_to_markdown(task, task_date):
    markdown = f"# {task.content}\n\n"
    markdown += f"{task.description}\n\n"

    return markdown


def archive_old_tasks(
    todoist_project: str,
    todoist_label: str,
    archive_threshold_days: int = 360,
    markdown_path: str = None,
):
    dry_run = False

    key = _todoist_api_key()
    if not key:
        print("Todoist API key not found in environment")
        return

    if not markdown_path and not dry_run:
        raise ValueError("markdown_path must be provided if dry_run is False")

    api = TodoistAPI(key)
    project = _get_project(api, todoist_project)
    labels = _get_labels(api, todoist_label)

    filter_str = _create_filter(project.name, only_one(labels))

    tasks = api.get_tasks(filter=filter_str)

    threshold_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=archive_threshold_days
    )

    archived_count = 0
    markdown_content = ""

    for task in tasks:
        task_date = datetime.datetime.fromisoformat(task.created_at).replace(
            tzinfo=datetime.timezone.utc
        )

        if task_date > threshold_date:
            continue

        markdown_content += _task_to_markdown(task, task_date)

        if dry_run:
            print(f"Would archive task: {task.content} (created on {task_date.date()})")
        else:
            print(f"Archiving task: {task.content} (created on {task_date.date()})")
            api.close_task(task_id=task.id)

        archived_count += 1

    if markdown_path and markdown_content:
        with open(markdown_path, "a") as f:
            f.write(markdown_content)

        print(f"Appended archived tasks to {markdown_path}")
    else:
        print(
            f"No tasks were archived or no markdown path was provided. {markdown_content}"
        )

    if dry_run:
        print(f"Dry run complete. {archived_count} tasks would be archived.")
    else:
        print(f"Task archiving complete. {archived_count} tasks archived.")
