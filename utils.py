# -*- coding: utf-8 -*-
import logging, os, datetime, zipfile, uuid, time, glob
from logging.handlers import TimedRotatingFileHandler
try:
    import zlib
    ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
except:
    ZIP_COMPRESSION = zipfile.ZIP_STORED
from plyer import notification

from globals import ROOT_DIR, CONFIG

# ============================================================= #

EXTRA_PARAMS = ['watched_path', 'event', 'source', 'destination']

# ============================================================= #

class TRFHandler(TimedRotatingFileHandler):

    def __init__(self, filename, when='h', interval=1, on_rollover=None, backupCount=1, utc=False, atTime=None):
        self.on_rollover = on_rollover
        super().__init__(filename, when, interval, backupCount, 'utf-8', True, utc, atTime)

    def doRollover(self):
        if self.on_rollover:
            self.on_rollover(self)
        super().doRollover()

# ============================================================= #

def generate_uuid():
    return uuid.uuid4().hex

def sleep(sec=1.0):
    time.sleep(sec)

def root_logger():
    return logging.getLogger()

def get_logger(name=None, logfile=None, level='info', rotate_interval=0, on_rollover=None, 
               when='s', keep_backups=1, at_time=None, utc=False):
    logger = logging.getLogger(name)
    
    if name is None:
        logger.setLevel(logging.DEBUG if CONFIG['logging'].get('verbose', False) else logging.INFO)
    else:
        logger.setLevel(level.upper())
    
    fmt = CONFIG['logging'].get('format', None)
    if fmt:
        fmap = {'time': 'asctime', 'logger': 'name', 'path': 'watched_path', 'level': 'levelname'}
        fields = fmt.get('fields', ['{asctime}', '[{name}]', '[{levelname}]', '>>> {watched_path}', ':: {event}',  '>> {message}'])
        fields_ = []
        for f in fields:
            for k, v in fmap.items():
                f = f.replace(k, v)
            fields_.append(f)
        fields = fields_
        if fmt.get('csv', False):
            fields = [f'"{f}"' for f in fields]
            str_fmt = ';'.join(fields)
        else:
            str_fmt = ' '.join(fields)
        time_fmt = fmt.get('timeformat', '%m/%d/%Y %I:%M:%S')
    else:
        str_fmt = '{asctime} [{name}] [{levelname}] >>> {watched_path} :: {event} >> {message}'
        time_fmt = '%m/%d/%Y %I:%M:%S' 
    
    formatter = logging.Formatter(str_fmt, time_fmt, '{')

    if (name is None) and ('logging' in CONFIG) and CONFIG['logging'].get('log', False):         
        file_ = CONFIG['logging'].get('file', None)
        handler = logging.FileHandler(file_, mode=('w' if CONFIG['logging'].get('restart', True) else 'a'), encoding='utf-8', delay=True) if file_ else logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    if not logfile:
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    if not rotate_interval:
        handler = logging.FileHandler(logfile, mode='w', encoding='utf-8', delay=True)
    else:
        handler = TRFHandler(logfile, when, rotate_interval, on_rollover, keep_backups, utc, at_time)

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def abspath(path, root=None):
    if root is None: root = ROOT_DIR
    root = os.path.abspath(root)
    return os.path.join(root, path)

def log(what, logger=None, how='info', **kwargs):
    logger = logger or root_logger()
    if not logger: return
    if not kwargs:
        kwargs = {e: '' for e in EXTRA_PARAMS}
    else:
        for k in EXTRA_PARAMS:
            if (not k in kwargs) or (not kwargs[k]):
                kwargs[k] = ''
    if how == 'info':
        logger.info(what, extra=kwargs)
    elif how == 'warn':
        logger.warning(what, extra=kwargs)
    elif how == 'error':
        logger.error(what, extra=kwargs)
    elif how == 'debug':
        logger.debug(what, extra=kwargs)
    elif how == 'critical':
        logger.critical(what, extra=kwargs)
    elif how == 'exception':
        logger.exception(what, extra=kwargs)

def sys_notify(title, message, timeout=10, ticker='', icon=''):
    notification.notify(title, message, 'Watcher', icon, timeout, ticker)

def get_now():
    return datetime.datetime.now()

def get_timedelta(last_time):
    tdelta = datetime.datetime.now() - last_time
    return tdelta.total_seconds()

def span_to_seconds(value, unit='s'):
    unit = unit.lower()
    if unit == 's':
        return datetime.timedelta(seconds=value).total_seconds()
    elif unit == 'm':
        return datetime.timedelta(minutes=value).total_seconds()
    elif unit == 'h':
        return datetime.timedelta(hours=value).total_seconds()
    elif unit == 'd':
        return datetime.timedelta(days=value).total_seconds()
    elif unit == 'w':
        return datetime.timedelta(weeks=value).total_seconds()
    raise Exception(f'Wrong unit: {unit}!')

def zipfiles(files, destination):
    with zipfile.ZipFile(destination, 'w') as z:
        for file in files:                  
            z.write(file, os.path.basename(file), compress_type=ZIP_COMPRESSION, compresslevel=9)

def list_files(mask='*.*', root=None):
    if not root:
        root = os.path.dirname(__file__)
    yield from glob.glob(os.path.join(root, mask))