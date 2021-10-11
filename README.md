# watcher
### Watching for filesystem events with email notification and more
`Watcher` is a convenient and easy to use python tool to watch for changes in directories (creation, modification, deletion and movement of files and subdirectories) and handle these events in a customizable way. The tool is based on the excellent [watchdog](https://python-watchdog.readthedocs.io/en/stable/index.html) library.

## Usage

### Clone repo and install required packages
```bash
git clone https://github.com/S0mbre/watcher.git
python -m pip install -r requirements.txt
```

### Configure watched directories and events in `config.yaml`
`config.yaml` is used to set the `Watcher` configuration:
```yaml
# DIRECTORY POLLING INTERVAL (SECONDS)
poll_interval: 5
# WATCHED OBJECTS (FILESYSTEM DIRECTORIES)
watchers:
  - path: C:\                   # path to root directory to watch
    recursive: true             # recurse in subdirs
    types:                      # list of file extensions to watch (masks)
      - '*'
    ignore_types: null          # list of ignored types (if 'types' is null)
    ignore_dirs: null           # list of ignored subdirs
    case_sensitive: false       # case-sensitive mask matching
    handlers:                   # list of event handlers
      - active: true            # whether this handler is active
        events:                 # events to handle (created, deleted, modified, moved/renamed)
          - cre                 # created event
          - del                 # deleted event
          - mod                 # modified event
          - mov                 # moved/renamed
        type: email             # handler type = email (notify by email)
        emit:                   # handler emit interval (will be triggered every ... units)
          interval: 1           # inerval (integer)
          unit: m               # unit: s = seconds, m = minutes, h = hours, d = days, w = weeks
        from: ''                # outbound email address
        to: []                  # list of recipient emails (will be put in BCC field)
        subject: WATCHER NOTIFICATION - {path} # subject template (supports placeholders in curly brackets: path, dt, events, type, event, message)
        smtp:                   # email SMTP settings
          server: ''            # SMTP server (host)
          login: ''             # SMTP login
          password: ''          # SMTP password
          protocol: SSL         # protocol (SSL or TLS)
          port: 465             # SMTP port (465 = SSL)
        attachment: false       # whether to send log as attachment
        zipped: false           # whether to send attached log in a ZIP archive
      - active: false           # another handler...
        events:
          - cre
          - del
          - mod
          - mov
        type: popup             # handler type = system popup (push notification)
        emit:
          interval: 0
          unit: s
        subject: WATCHER NOTIFICATION - {path} # popup title (supports placeholders: see 'subject' in email handler)
        timeout: 5              # timeout to hide popup (sec)
        icon: auto              # icon file to use in popup ('auto' = guess by event type from <project>/img/*.ico)
        ticker: WATCHER NOTIFICATION - {path} # ticker (tray) message (supports placeholders: see 'subject' in email handler)
# EVENT LOGGING SETTINGS     
logging:
  log: true                     # logging is ON
  file: null                    # log file (null = STDOUT console)
  restart: true                 # whether to rewrite the existing log file (false = append)
  verbose: false                # verbose logging is OFF (includes debug messages)
  format:                       # log record formatting
    fields:                     # fields in each log record: supports placeholders in curly brackets as detailed below
      - '{time}'                # current date and time (see 'timeformat' below)
      - '{logger}'              # ID of logger
      - '{path}'                # watched directory path
      - '{event}'               # watched event (see 'events' property in a handler)
      - '{level}'               # message logging level: DEBUG, ERROR, EXCEPTION, CRITICAL, INFO, WARN
      - '{message}'             # body of the log message
      - '{source}'              # source path (for any event)
      - '{destination}'         # destination path (non-empty only for move / rename events)
    csv: true                   # output log records in CSV format (fields are quoted and separated by ';')
    timeformat: '%m/%d/%Y %I:%M:%S' # date/time format template (see Python docs for placeholder reference)
  handlers:                     # list of handlers to handle the root log file (e.g. send by email) -- see watchers > handlers above
    - active: false
      type: email
      emit:
        interval: 1
        unit: h
      from: ''
      to: []
      subject: WATCHER LOG [{dt}]
      smtp:
        server: ''
        login: ''
        password: ''
        protocol: SSL
        port: 465
      attachment: true
      zipped: true
# PROXY SETTINGS (FOR EMAILING)
proxy:
  useproxy: false               # proxy is OFF
  server: null                  # proxy server (host) -- leave null to use system settings
  port: null                    # proxy port (integer) -- leave null to use system settings 
  type: HTTP                    # proxy type ('HTTP', 'SOCKS4' or 'SOCKS5')
  username: null                # proxy username (null = no authentication)
  password: null                # proxy password (null = no authentication)
```

### Run the watcher
```bash
python watcher.py [path-to-condig.yaml]
```
If omitted, `path-to-condig.yaml` will be resolved as `<project>/config.yaml`. Otherwise, a valid path to a YAML config file (as shown above) must be supplied.

## Credits
Icons made by [Freepik](https://www.freepik.com) from [Flaticon](https://www.flaticon.com/).