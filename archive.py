import plistlib
import os
import sys

from ScriptingBridge import *

def export_to_todoist(content, description):
  # TODO should also support .env here as well
  import dotenv
  dotenv.load_dotenv(".envrc")

  # extract todoist api key from environment without throwing an exception
  todoist_api_key = os.environ.get('TODOIST_API_KEY', None)

  if not todoist_api_key:
    print("todoist api key not found in environment")
    return

  print("todoist api key found, adding to todoist")

  from todoist_api_python.api import TodoistAPI
  import datetime

  api = TodoistAPI(todoist_api_key)

  # find a label called "web-archive" or create it
  labels = api.get_labels()
  label_matches = [label for label in labels if label.name == "web-archive"]

  if len(label_matches) == 0:
    # https://developer.todoist.com/rest/v1/#create-a-new-label
    print("could not find web-archive label, creating it")
    label = api.add_label(name="web-archive")
  else:
    label = label_matches[0]

  # https://developer.todoist.com/rest/v2#create-a-new-task
  response = api.add_task(
    # set content to "web archive CURRENT_DAY" using format YYYY-MM-DD
    content="{}web archive {}".format(tab_description, datetime.datetime.now().strftime("%Y-%m-%d")),
    description=todoist_content,
    due_string="today",
    labels=["web-archive"],
  )

def main():
  # TODO maybe optionally collect via applescript input dialog? We'd need to develop a proper interface for the CLI at that point.
  # get first CLI argument if it exists
  if len(sys.argv) > 1 and sys.argv[1].strip():
    tab_description = sys.argv[1].strip() + " "
  else:
    tab_description = ''

  safari = SBApplication.applicationWithBundleIdentifier_("com.apple.safari")
  safari_urls = []

  for window in safari.windows():
      for tab in window.tabs():
          safari_urls.append((tab.URL(), tab.name()))
          # it doesn't look possible to close out the tabs with SBApplication :/
          # instead we just close out the whole application below

  # if page is blank, there is no url
  safari_urls = [x for x in safari_urls if x[0] is not None]

  # remove duplicates
  safari_urls = list(set(safari_urls))

  # sort (in place) list of urls by domain name of url
  safari_urls.sort(key=lambda x: x[0].split('/')[2])

  # strip all anchors from the urls
  safari_urls = [(url.split('#')[0], name) for url, name in safari_urls]

  # read all safari bookmarks, don't include these in the printout
  with open(os.path.expanduser("~") + '/Library/Safari/Bookmarks.plist', 'rb') as f:
    bookmarks_plist = plistlib.load(f)

    """
    In [31]: [bookmark["Title"] for bookmark in bookmarks["Children"]]
    Out[31]: ['History', 'BookmarksBar', 'BookmarksMenu', 'com.apple.ReadingList']
    """

    bookmarks = [child for child in bookmarks_plist["Children"] if child["Title"] == "BookmarksBar"][0]["Children"]
    bookmarks_urls = [bookmark['URLString'] for bookmark in bookmarks]
    bookmarks_urls_without_anchors = [bookmark.split('#')[0] for bookmark in bookmarks_urls]

  # user configurable blacklist for urls you don't want to archive
  url_blacklist = []
  with open('blacklist_urls.txt', 'r') as f:
    url_blacklist = f.read().splitlines()

  domain_blacklist = []
  with open('blacklist_domains.txt', 'r') as f:
    domain_blacklist = f.read().splitlines()

  # TODO output skipped domains
  # TODO support wildcard subdomains
  # filter all urls with blacklisted domains
  safari_urls = [x for x in safari_urls if x[0].split('/')[2] not in domain_blacklist]

  # join url and name with "-" and print to stdout
  todoist_content = ""
  for url_with_name in safari_urls:
    if url_with_name[0] not in bookmarks_urls_without_anchors and url_with_name[0] not in url_blacklist:
      todoist_content += "* " + " - ".join(url_with_name) + "\n"
    else:
      print(f"skipping url\t{url_with_name[0]}")

  if not todoist_content.strip():
    print("no urls to add, exiting")
    sys.exit()

  print(f"\n{todoist_content}\n")

  # since we've archived all content we can now close out safari
  os.system('osascript -e \'quit app "Safari"\'')

  export_to_todoist(todoist_content, tab_description)

if __name__ == "__main__":
  main()