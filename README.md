<!-- trunk-ignore-all(trufflehog/GitHubOauth2) -->
<!-- trunk-ignore-all(markdownlint/MD041) -->

[![Release Notes](https://img.shields.io/github/release/iloveitaly/clean-browser)](https://github.com/iloveitaly/clean-browser/releases)
[![Downloads](https://static.pepy.tech/badge/clean-workspace/month)](https://pepy.tech/project/clean-workspace)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)

# Clean Workspace: Archive Web Browser Tabs

I love experimenting with productivity. One glitch I've found in my mind is I can easily
get distracted by open tabs on my browser, especially if I'm trying to write or read something which I want to give
my full attention to. I've found that if I close all my tabs (similar idea to [shrinking context size](http://mikebian.co/improve-motivation-and-focus-with-small-contexts/)), I can focus better on the task at hand. However, I don't
want to lose any interesting tabs so I never actually do that.

This is utility to fix this issue. It closes all your tabs (in both Safari & Chrome), sends them to [todoist](https://mikebian.co/todoist)
with a specified project + label, and outputs the list to the terminal (mostly for debugging).

This has seemed to really help my mind and make it easy for me to find interesting things I've run into in the past.

## Installation

```shell
pip install clean-workspace
```

- `TODOIST_API_KEY` has to exist in your shell environment for the tool to run.
  I recommend using [direnv](https://direnv.net/) to do this. Add your todoist token to `.envrc` and `direnv allow .`
- Customize the url and domain blacklist

## Usage

```shell
❯ clean-workspace --help
Usage: clean-workspace [OPTIONS]

Options:
  --blacklist-domains PATH
  --blacklist-urls PATH
  --tab-description TEXT    Description for tab
  --todoist-label TEXT      label in todoist for all created tasks  [default:
                            web-archive]
  --todoist-project TEXT    project in todoist for all created tasks
                            [default: Learning]
  --help                    Show this message and exit.
```

## Development

```shell
poetry install
poetry run clean-workspace
```

### Regex Entries

You can use regex matches in both the url and domain blacklist files. For example, if you want to blacklist all Zoom domains, you can use the following:

```shell
echo "/.*zoom\.us/" >> ~/.config/clean-workspace/blacklist-domains.txt
```

A regex entry starts & ends with `/`, like `sed`.

### Collecting Tab Description Via AppleScript

Here's a quick script you can use to collect a description of what you were working on via applescript:

```shell
dialogResult=$(
osascript <<EOT
set dialogResult to display dialog "What were you working on yesterday?" buttons {"OK"} default button "OK" giving up after 300 default answer ""
return text returned of dialogResult
EOT
)
```

Here's a [full example](https://github.com/iloveitaly/dotfiles/blob/648010ec9a9c8f1fb0aa70be138994689f3bbfb3/.config/focus/initial_wake.sh#L42-L53) of using this with [hyper-focus](https://www.raycast.com/iloveitaly/hyper-focus).

## Inspiration

- <https://gist.github.com/aleks-mariusz/cc27b21f2c5b91fbd285>
- <https://github.com/tominsam/shelf-python/blob/f357d9b147fa651034b71501edabf65f59d5befa/extractors/ComAppleSafari.py#L11>

## TODO

- [ ] Indicate in python config that this is macOS only in poetry config?
- [ ] move blacklist files into example area of repo
- [ ] look at previous tasks and see if links are contained there before including them again
- [ ] support google chrome canary
