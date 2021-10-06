# -*- coding: utf-8 -*-
import logging, os, datetime, zipfile, uuid, time
from logging.handlers import TimedRotatingFileHandler
try:
    import zlib
    ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
except:
    ZIP_COMPRESSION = zipfile.ZIP_STORED
from plyer import notification

from globals import CONFIG

# ============================================================= #

class TRFHandler(TimedRotatingFileHandler):

    def __init__(self, filename, when='h', interval=1, on_rollover=None, backupCount=0, utc=False, atTime=None):
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
               when='s', keep_backups=0, at_time=None, utc=False):
    logger = logging.getLogger(name)
    
    if name is None:
        logger.setLevel(logging.DEBUG if CONFIG['logging'].get('verbose', False) else logging.INFO)
    else:
        logger.setLevel(level.upper())

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%m/%d/%Y %I:%M:%S')

    if (name is None) and ('logging' in CONFIG) and CONFIG['logging'].get('log', False):         
        file_ = CONFIG['logging'].get('file', None)
        handler = logging.FileHandler(file_, mode='w', encoding='utf-8', delay=True) if file_ else logging.StreamHandler()
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
    if not root:
        root = os.path.dirname(__file__)
    root = os.path.abspath(root)
    return os.path.join(root, path)

def log(what, logger=None, how='info', **kwargs):
    logger = logger or root_logger()
    if not logger: return
    if how == 'info':
        logger.info(what, **kwargs)
    elif how == 'warn':
        logger.warning(what, **kwargs)
    elif how == 'error':
        logger.error(what, **kwargs)
    elif how == 'debug':
        logger.debug(what, **kwargs)
    elif how == 'critical':
        logger.critical(what, **kwargs)
    elif how == 'exception':
        logger.exception(what, **kwargs)

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