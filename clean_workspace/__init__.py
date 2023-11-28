import datetime
import os
import plistlib
import re
import sys
import typing as t
from functools import lru_cache

import chrome_bookmarks
import click
from ScriptingBridge import SBApplication
from todoist_api_python.api import TodoistAPI


# https://github.com/Doist/todoist-api-python/issues/38
# backoff 5xx errors
def patch_todoist_api():
    import backoff
    import requests
    import todoist_api_python.http_requests

    patch_targets = ["delete", "get", "json", "post"]
    for target in patch_targets:
        original_function = getattr(todoist_api_python.http_requests, target)

        setattr(
            todoist_api_python.http_requests,
            f"original_{target}",
            original_function,
        )

        patched_function = backoff.on_exception(
            backoff.expo, requests.exceptions.HTTPError
        )(original_function)

        setattr(
            todoist_api_python.http_requests,
            target,
            patched_function,
        )


patch_todoist_api()


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


def only_one(comprehension):
    if len(comprehension) != 1:
        raise Exception("Expected to find exactly one matching item")

    return comprehension[0]


@lru_cache(maxsize=None)
def _get_project(api, project_name):
    projects = api.get_projects()
    return only_one([project for project in projects if project.name == project_name])


def _extract_urls_from_markdown(markdown):
    url_regex = r"https?://[^\s)\]]+"
    return re.findall(url_regex, markdown)


def export_to_todoist(task_description, description, todoist_project, todoist_label):
    key = _todoist_api_key()
    # trunk-ignore(bandit/B101)
    assert key is not None
    api = TodoistAPI(key)

    project = _get_project(api, todoist_project)
    labels = _get_labels(api, todoist_label)

    task_content = "_".join(
        filter(
            None,
            [description, "web archive", datetime.datetime.now().strftime("%Y-%m-%d")],
        )
    )

    # https://developer.todoist.com/rest/v2#create-a-new-task
    api.add_task(
        # set content to "web archive CURRENT_DAY" using format YYYY-MM-DD
        content=task_content,
        description=task_description,
        # date is serialized in the task description, no need for a due date
        due_string="no date",
        # confusing, but labels are strings not IDs
        labels=labels,
        project_id=project.id if project else None,
    )


def get_browser_urls() -> t.List[str]:
    browser_urls = []
    chrome = SBApplication.applicationWithBundleIdentifier_("com.google.Chrome")

    for window in chrome.windows():
        for tab in window.tabs():
            browser_urls.append((tab.URL(), tab.name()))

    safari = SBApplication.applicationWithBundleIdentifier_("com.apple.safari")

    for window in safari.windows():
        for tab in window.tabs():
            browser_urls.append((tab.URL(), tab.name()))
            # it doesn't look possible to close out the tabs with SBApplication :/
            # instead we just close out the whole application below

    return browser_urls


def get_bookmarks_urls() -> t.List[str]:
    raw_bookmark_urls = [bookmark.url for bookmark in chrome_bookmarks.urls]

    # read all safari bookmarks, don't include these in the printout
    with open(os.path.expanduser("~") + "/Library/Safari/Bookmarks.plist", "rb") as f:
        bookmarks_plist = plistlib.load(f)

        """
        In [31]: [bookmark["Title"] for bookmark in bookmarks["Children"]]
        Out[31]: ['History', 'BookmarksBar', 'BookmarksMenu', 'com.apple.ReadingList']
        """

        safari_bookmarks = [
            child
            for child in bookmarks_plist["Children"]
            if child["Title"] == "BookmarksBar"
        ][0]["Children"]

        raw_safari_bookmark_urls = [
            bookmark["URLString"] for bookmark in safari_bookmarks
        ]

        raw_bookmark_urls.extend(raw_safari_bookmark_urls)

    return [bookmark.split("#")[0] for bookmark in raw_bookmark_urls]


# TODO trunk ignore should be cleaner
def restart_application(app_name: str) -> None:
    # trunk-ignore-begin(bandit)
    os.system(
        f"""
    osascript -e '
    tell application "{app_name}" to quit
    delay 1
    tell application "{app_name}" to activate
    '
    """
    )
    # trunk-ignore-end(bandit)


def quit_browsers():
    restart_application("Safari")
    restart_application("Chrome")


# the syntax we use is starting and ending with `/`, like sed
def _is_regex_entry(entry: str):
    return entry.startswith("/") and entry.endswith("/")


# assume `regex_blacklist` contains the raw regex strings (starting & ending with /)
def _in_regex_blacklist(regex_blacklist, url):
    for regex in regex_blacklist:
        if re.search(regex[1:-1], url):
            return True

    return False


def _extract_host(url):
    return url.split("/")[2]


def _get_existing_web_archive_links(todoist_project, todoist_label):
    # TODO should probably refactor to DRY this up
    key = _todoist_api_key()
    assert key is not None
    api = TodoistAPI(key)

    project = _get_project(api, todoist_project)
    labels = _get_labels(api, todoist_label)

    # filter by label + project to find all of the existing links and construct an 'already archived' link DB
    filter = f"#{project.name}"
    if labels:
        filter += f" & @{labels[0]}"

    all_web_archive_tasks = api.get_tasks(filter=filter)
    all_web_archive_links = [
        _extract_urls_from_markdown(task.description) for task in all_web_archive_tasks
    ]
    all_web_archive_links = [
        item for sublist in all_web_archive_links for item in sublist
    ]

    return all_web_archive_links


def clean_workspace(
    tab_description,
    blacklist_domains_file_path,
    blacklist_urls_file_path,
    todoist_project,
    todoist_label,
):
    browser_urls = get_browser_urls()

    # if page is blank, there is no url or string does not contain http
    browser_urls = [x for x in browser_urls if x[0] is not None and "http" in x[0]]

    # sort (in place) list of urls by domain name of url
    browser_urls.sort(key=lambda x: _extract_host(x[0]))

    # strip all anchors from the urls
    browser_urls = [(url.split("#")[0], name) for url, name in browser_urls]

    # remove duplicates
    browser_urls = list(set(browser_urls))

    # user configurable blacklist for urls you don't want to archive
    url_blacklist = []
    with open(blacklist_urls_file_path, "r") as f:
        url_blacklist = f.read().splitlines()

    # split url_blacklist into regex_blacklist and url_blacklist
    # we could use `itertools.partion` here to do this more efficiently, but it's not worth the extra complexity
    url_regex_blacklist = [entry for entry in url_blacklist if _is_regex_entry(entry)]
    url_blacklist = [entry for entry in url_blacklist if not _is_regex_entry(entry)]

    domain_blacklist = []
    with open(blacklist_domains_file_path, "r") as f:
        domain_blacklist = f.read().splitlines()

        domain_regex_blacklist = [
            domain for domain in domain_blacklist if _is_regex_entry(domain)
        ]

        # filter out all regex entries
        domain_blacklist = [
            domain for domain in domain_blacklist if not _is_regex_entry(domain)
        ]

        # add a `www.` prefix to each domain in the blacklist and merge it with the existing list
        domain_blacklist = domain_blacklist + [
            "www." + domain
            for domain in domain_blacklist
            if not _is_regex_entry(domain)
        ]

    bookmark_urls = get_bookmarks_urls()

    # TODO output skipped domains if verbose flag is set

    browser_urls = [
        x for x in browser_urls if _extract_host(x[0]) not in domain_blacklist
    ]

    browser_urls = [
        x
        for x in browser_urls
        if not _in_regex_blacklist(domain_regex_blacklist, _extract_host(x[0]))
    ]

    browser_urls = [x for x in browser_urls if x[0] not in url_blacklist]

    # regex url blacklist is separate from the url blacklist
    browser_urls = [
        x for x in browser_urls if not _in_regex_blacklist(url_regex_blacklist, x[0])
    ]

    # now do the regular url blacklist
    browser_urls = [x for x in browser_urls if x[0] not in url_blacklist]

    # if the url is in the bookmark list of chrome or safari, skip it
    browser_urls = [x for x in browser_urls if x[0] not in bookmark_urls]

    existing_archived_links = _get_existing_web_archive_links(
        todoist_project, todoist_label
    )

    # filter out all urls that have already been archived
    browser_urls = [x for x in browser_urls if x[0] not in existing_archived_links]

    if not browser_urls:
        print("no urls to add, exiting")
        # still could be urls we don't care about and over time this could junk up browser processes in my experience
        quit_browsers()
        sys.exit()

    task_description = _generate_todoist_content(browser_urls)
    print(task_description)

    export_to_todoist(
        task_description,
        tab_description,
        todoist_project,
        todoist_label,
    )

    # since we've archived all content we can now close out Safari & Chrome
    quit_browsers()


# join url and name with "-" and print to stdout, use markdown list format for each entry
def _generate_todoist_content(browser_urls):
    todoist_content = ""
    for url_with_name in browser_urls:
        todoist_content += "* " + " - ".join(url_with_name) + "\n"

    return todoist_content


@click.command()
@click.option("--blacklist-domains", type=click.Path(), default=None)
@click.option("--blacklist-urls", type=click.Path(), default=None)
@click.option("--tab-description", default="", help="Description for tab")
@click.option(
    "--todoist-label",
    default="web-archive",
    show_default=True,
    help="label in todoist for all created tasks",
)
@click.option(
    "--todoist-project",
    default="Web Archive",
    show_default=True,
    help="project in todoist for all created tasks",
)
def main(
    tab_description, blacklist_domains, blacklist_urls, todoist_label, todoist_project
):
    if not is_internet_connected():
        print("internet is not connected")
        return

    if not _todoist_api_key():
        print("todoist api key not found in environment")
        return

    home_dir = os.path.expanduser("~")

    if blacklist_domains is None:
        default_domains_path = os.path.join(
            home_dir, ".config", "clean-workspace", "blacklist_domains.txt"
        )
        blacklist_domains = (
            default_domains_path
            if os.path.exists(default_domains_path)
            else "blacklist_domains.txt"
        )

    if blacklist_urls is None:
        default_urls_path = os.path.join(
            home_dir, ".config", "clean-workspace", "blacklist_urls.txt"
        )

        blacklist_urls = (
            default_urls_path
            if os.path.exists(default_urls_path)
            else "blacklist_urls.txt"
        )

    clean_workspace(
        tab_description,
        blacklist_domains,
        blacklist_urls,
        todoist_project,
        todoist_label,
    )


def is_internet_connected():
    import socket

    s = socket.socket(socket.AF_INET)
    try:
        s.connect(("google.com", 80))
        return True
    except socket.error:
        return False
