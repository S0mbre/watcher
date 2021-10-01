# watcher
### Watching for filesystem events with email notification and more
`Watcher` is a convenient and easy to use python tool to watch for changes in directories (creation, modification, deletion and movement of files and subdirectories) and handle these events in a customizable way. The tool is based on the excellent [watchdog](https://python-watchdog.readthedocs.io/en/stable/index.html) library.

## Usage

### Clone repo and install required packages
```bash
git clone https://github.com/S0mbre/watcher.git
python -m pip install -r requirementstxt
```

### Configure watched directories and events in `config.json`
`config.json` is used to set the `Watcher` configuration:
```python
{
"watchers": [ # list of watched objects (=directories)
{
  "path": "C:\\", # path to root directory to watch
  "recursive": true, # recurse in subdirs
  "types": ["*"], # list of file extensions to watch (masks)
  "ignore_types": null, # list of ignored types (if 'types' is null)
  "ignore_dirs": false, # list of ignored subdirs
  "case_sensitive": false, # case-sensitive mask matching
  "handlers": [ # list of event handlers
  {
    "active": false, # whether this handler is active
    "events": ["cre", "del", "mod", "mov"], # events to handle (created, deleted, modified, moved/renamed)
    "type": "email", # handler type = email (notify by email)
    "from": "", # outbound email
    "to": null, # list of recipient emails
    "subject": "WATCHER NOTIFICATION - {path}", # subject template ('path' will be resolved as root watched path)
    "smtp": # email SMTP settings
    {
      "server": "", # SMTP server (host)
      "login": "", # SMTP login
      "password": "", # SMTP password
      "protocol": "SSL", # protocol (SSL or TLS)
      "port": 465 # SMTP port (465 = SSL)
    }
  },
  {
    "active": true, # another handler = active
    "events": ["cre", "del", "mod", "mov"],
    "type": "popup", # system popup (push notification)
    "subject": "WATCHER NOTIFICATION - {path}", # title (see 'subject' in email handler)
    "timeout": 5, # timeout to hide popup
    "icon": "auto", # icon file to use in popup ('auto' = guess by event type from <project>/img/*.ico)
    "ticker": "WATCHER NOTIFICATION - {path}" # ticker (tray) message
  }
  ]
}
],
"poll_interval": 5, # watch polling interval (seconds)
"logging": # event logging settings
{
  "log": true, # logging is ON
  "file": null, # log file (null = STDOUT console)
  "verbose": false, # verbose logging (includes debug messages)
  "send": # option to send log file to email at regular intervals
  {
    "active": false, # turn log emails ON
    "interval": 20, # send every 20 seconds
    "from": "", # outbound email
    "to": null, # list of recipient emails
    "subject": "WATCHER LOG [{dt}]", # subject template ('dt' will be resolved as current date & time)
    "smtp": # SMTP settings - see above in 'email' handler
    {
      "server": "",
      "login": "",
      "password": "",
      "protocol": "SSL",
      "port": 465
    },
    "zipped": true # whether to send log file in a zip archive
  }
},
"proxy": # network proxy settings
{
  "useproxy": true, # proxy is OFF
  "server": null, # proxy server (host) -- leave null to use system settings
  "port": null, # proxy port (integer) -- leave null to use system settings
  "type": "HTTP", # proxy type ('HTTP', 'SOCKS4' or 'SOCKS5')
  "username": null, # proxy username (null = no authentication)
  "password": null # proxy password (null = no authentication)
}
}
```

### Run the watcher
```bash
python watcher.py [path-to-condig.json]
```
If ommitted, `path-to-condig.json` will be resolved as `<project>/config.json`. Otherwise, a valid path to a JSON config file (as shown above) must be supplied.