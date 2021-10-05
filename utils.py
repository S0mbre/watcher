# -*- coding: utf-8 -*-
import logging, os, datetime, zipfile, uuid
from logging.handlers import TimedRotatingFileHandler
try:
    import zlib
    ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
except:
    ZIP_COMPRESSION = zipfile.ZIP_STORED
from plyer import notification

from globals import CONFIG, LOG, LOGGER

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

def get_logger(name='app', logfile=None, level='info', rotate_interval=0, on_rollover=None, 
               when='s', keep_backups=0, at_time=None, utc=False):
    global LOGGER
    logger = logging.getLogger(name)

    if (not LOGGER) and (name == 'app'):
        logger.setLevel(logging.DEBUG if CONFIG['logging'].get('verbose', False) else logging.INFO)
    else:
        logger.setLevel(level.upper())

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%m/%d/%Y %I:%M:%S')

    if (LOGGER is None) and (name == 'app') and ('logging' in CONFIG) and CONFIG['logging'].get('log', False): 
        file_ = CONFIG['logging'].get('file', None)
        handler = logging.FileHandler(file_, encoding='utf-8', delay=True) if file_ else logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        LOGGER = logger

    if not logfile:
        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    if not rotate_interval:
        handler = logging.FileHandler(logfile, encoding='utf-8', delay=True)
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

def log(what, logger=LOGGER, how='info', **kwargs):
    if not logger: return
    if how == 'info':
        logging.info(what, **kwargs)
    elif how == 'warn':
        logging.warning(what, **kwargs)
    elif how == 'error':
        logging.error(what, **kwargs)
    elif how == 'debug':
        logging.debug(what, **kwargs)
    elif how == 'critical':
        logging.critical(what, **kwargs)
    elif how == 'exception':
        logging.exception(what, **kwargs)

def sys_notify(title, message, timeout=10, ticker='', icon=''):
    notification.notify(title, message, 'Watcher', icon, timeout, ticker)

def get_now():
    return datetime.datetime.now()

def get_timedelta(last_time):
    tdelta = datetime.datetime.now() - last_time
    return tdelta.total_seconds()

def zipfiles(files, destination):
    # try:
    #     os.remove(destination)
    # except:
    #     pass
    with zipfile.ZipFile(destination, 'w') as z:
        for file in files:                  
            z.write(file, os.path.basename(file), compress_type=ZIP_COMPRESSION, compresslevel=9)