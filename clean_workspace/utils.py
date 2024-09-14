import os
import re
from functools import lru_cache


def only_one(comprehension):
    if len(comprehension) != 1:
        raise Exception("Expected to find exactly one matching item")

    return comprehension[0]


def _todoist_api_key():
    return os.environ.get("TODOIST_API_KEY", None)


# totally unnecessary for the size of the project...
@lru_cache(maxsize=None)
def _get_labels(api, label_text):
    # allow empty labels as a valid value
    if not label_text:
        return []

    label_name = label_text
    labels = api.get_labels()
    label_matches = [label for label in labels if label.name == label_name]

    # create the label if it doesn't exist
    if len(label_matches) == 0:
        # https://developer.todoist.com/rest/v1/#create-a-new-label
        print(f"could not find {label_name} label, creating it")
        api.add_label(name=label_name)

    return [label_name]


@lru_cache(maxsize=None)
def _get_project(api, project_name):
    projects = api.get_projects()
    return only_one([project for project in projects if project.name == project_name])


def _extract_urls_from_markdown(markdown):
    url_regex = r"https?://[^\s)\]]+"
    return re.findall(url_regex, markdown)
