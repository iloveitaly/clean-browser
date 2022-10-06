import plistlib
import os

from ScriptingBridge import *

safari = SBApplication.applicationWithBundleIdentifier_("com.apple.safari")
safari_urls = []

for window in safari.windows():
    for tab in window.tabs():
        safari_urls.append((tab.URL(), tab.name()))
        # it doesn't look possible to close out the tabs with SBApplication :/
        # instead we just close out the whole application below

# if page is blank, there is no url
safari_urls = [x for x in safari_urls if x[0] is not None]

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
with open('blacklist.txt', 'r') as f:
  url_blacklist = f.read().splitlines()

# join url and name with "-" and print to stdout
todoist_content = ""
for url_with_name in safari_urls:
  if url_with_name[0] not in bookmarks_urls_without_anchors and url_with_name[0] not in url_blacklist:
    print(" - ".join(url_with_name))
    todoist_content += "* " + " - ".join(url_with_name)

# since we've archived all content we can now close out safari
os.system('osascript -e \'quit app "Safari"\'')

import dotenv
dotenv.load_dotenv(".envrc")

# extract todoist api key from environment without throwing an exception
todoist_api_key = os.environ.get('TODOIST_API_KEY', None)

if todoist_api_key:
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

  # https://developer.todoist.com/rest/v1/#create-a-new-task
  api.add_task(
    # set content to "web archive CURRENT_DAY" using format YYYY-MM-DD
    content="web archive {}".format(datetime.datetime.now().strftime("%Y-%m-%d")),
    description=todoist_content,
    due_string="today",
    label_ids=[label.id],
  )
