# Clean Workspace: Archive Web Browser Tabs

I've been experimenting with how to make my mornings more productive. One glitch I've found in my mind is I can easily
get distracted by open tabs on my browser, especially if I'm trying to write or read something which I want to give
my full attention to. I've found that if I close all my tabs (similar idea to [shrinking context size](http://mikebian.co/improve-motivation-and-focus-with-small-contexts/)), I can focus better on the task at hand. However, I don't
want to lose any interesting tabs so I never actually do that.

This is simple utility to automate this process. It will close all your tabs (in both Safari & Chrome), and send them to [todoist](https://mikebian.co/todoist) (and output) them to the terminal.

We'll see if this actually helps!

## Installation

```shell
poetry install
poetry run clean-workspace
```

## Usage

- Add your todoist token to `.envrc` and `direnv allow .`
- Customize the url and domain blacklist

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

- https://gist.github.com/aleks-mariusz/cc27b21f2c5b91fbd285
- https://github.com/tominsam/shelf-python/blob/f357d9b147fa651034b71501edabf65f59d5befa/extractors/ComAppleSafari.py#L11

## TODO

- [ ] Indicate in python config that this is macOS only in poetry config?
- [ ] move blacklist files into example area of repo
