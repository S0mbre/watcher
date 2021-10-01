# -*- coding: utf-8 -*-
import logging, os, datetime, zipfile
try:
    import zlib
    ZIP_COMPRESSION = zipfile.ZIP_DEFLATED
except:
    ZIP_COMPRESSION = zipfile.ZIP_STORED
from plyer import notification

from globals import LOG

# ============================================================= #

def abspath(path, root=None):
    if not root:
        root = os.path.dirname(__file__)
    root = os.path.abspath(root)
    return os.path.join(root, path)

def log(what, *args, how='info', **kwargs):
    if not LOG: return
    if how == 'info':
        logging.info(what, *args, **kwargs)
    elif how == 'warn':
        logging.warning(what, *args, **kwargs)
    elif how == 'error':
        logging.error(what, *args, **kwargs)
    elif how == 'debug':
        logging.debug(what, *args, **kwargs)
    elif how == 'critical':
        logging.critical(what, *args, **kwargs)
    elif how == 'exception':
        logging.exception(what, *args, **kwargs)

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