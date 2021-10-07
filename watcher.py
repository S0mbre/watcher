# -*- coding: utf-8 -*-
import logging
import os
# from watchdog.observers import Observer # <-- this uses WinAPI implementation which generates duplicate events! See https://github.com/gorakhargosh/watchdog/issues/93
# TODO: consider switching to watchgod [https://github.com/samuelcolvin/watchgod]
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import (PatternMatchingEventHandler,
                             EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED)
import abc

from globals import *
import utils
import networking

# ============================================================= #

class BaseHandler(abc.ABC):

    def __init__(self, dict_handler=None, create_log=True, cleanup_log=True, watched_path=None,
                 on_before_emit='auto', on_after_emit=None,
                 msg_format='{path} >> {message}', root_logger=False):
        self.create_log = create_log
        self.cleanup_log = cleanup_log
        self.watched_path = watched_path
        self.msg_format = msg_format
        self.root_logger = root_logger
        self.on_before_emit = BaseHandler._default_before_emit if on_before_emit == 'auto' else on_before_emit
        self.on_after_emit = on_after_emit
        self.user_data = {}
        self._logger_uid = ''
        self._update(dict_handler)

    def __del__(self):
        # shutdown logger
        self.close_logger(self.cleanup_log)

    def _update(self, dict_handler=None):
        if not dict_handler:
            dict_handler = {}
        self.active = dict_handler.get('active', False)
        self.events = dict_handler.get('events', [])
        self.type = None
        self.emit = dict_handler.get('emit', {'interval': 0, 'unit': 's'})
        self.logger: logging.Logger = None
        self._logfile = ''
        if self.create_log: self._create_logger()

    def _on_rollover(self, trf_handler):
        if self.active:
            self.emit_log()

    def _create_logger(self):
        self._logger_uid = utils.generate_uuid()
        self._logfile = utils.abspath(f'{self._logger_uid}.log')
        if self.active:
            self.logger = utils.get_logger(self._logger_uid if not self.root_logger else None,
                                           self._logfile, 'info', self.emit['interval'],
                                           self._on_rollover if self.emit['interval'] > 0 else None, self.emit['unit'])

    def close_logger(self, delete_files=True):
        if not self.logger or not self._logfile:
            return
        for h in self.logger.handlers:
            try:
                h.close()
            except:
                continue
        if delete_files:
            for f in utils.list_files(f'{self._logger_uid}.*'):
                try:
                    os.remove(f)
                except:
                    pass

    def _format_str(self, s, event=None, message=None):
        return s.format(path=self.watched_path, dt=utils.get_now().strftime('%Y-%m-%d %H-%M-%S'),
                        events=', '.join(self.events), type=str(self.type), event=event, message=message)

    @staticmethod
    def _default_before_emit(obj, event, msg):
        if not any(['cre' in obj.events and event == 'cre', 'mod' in obj.events and event == 'mod',
                    'mov' in obj.events and event in ('mov', 'ren'), 'del' in obj.events and event == 'del']):
            return False
        utils.log(f"Handling '{event}' event with {obj} ...", how='debug', event=event, watched_path=obj.watched_path)
        return True

    def trigger(self, event, message, src_path, dest_path):
        if not self.active:
            return
        if self.on_before_emit and not self.on_before_emit(self, event, message):
            return
        if self.logger and not self.root_logger:
            utils.log(self._format_str(self.msg_format, message=message, event=event), self.logger,
                      event=event, watched_path=self.watched_path, source=src_path, destination=dest_path)
        if self.emit['interval'] <= 0:
            self.emit_msg(event, message, src_path, dest_path)
            if self.on_after_emit:
                self.on_after_emit(self, event, message)

    def __repr__(self):
        return f'Handler [{self.type}] (active = {self.active}, events = {self.events}, path = {self.watched_path}, log = {self._logfile})'

    def emit_msg(self, event, message, src_path, dest_path):
        if not self.active: return
        try:
            self._emit_msg(event, message, src_path, dest_path)
        except Exception as err:
            utils.log(err, how='exception', event=event, watched_path=self.watched_path, source=src_path, destination=dest_path)

    def emit_log(self, logfile=None):
        if not self.active: return
        dafile = logfile if not logfile is None else ((self._logfile if not self.root_logger else CONFIG['logging'].get('file', '')) or '')
        if not os.path.isfile(dafile): return
        try:
            self._emit_log(dafile)
        except Exception as err:
            utils.log(err, how='exception', watched_path=self.watched_path)

    @abc.abstractmethod
    def _emit_msg(self, event, message, src_path, dest_path):
        pass

    @abc.abstractmethod
    def _emit_log(self, logfile):
        pass

# ============================================================= #

class EmailHandler(BaseHandler):

    def _update(self, dict_handler=None):
        super()._update(dict_handler)
        self.type = dict_handler.get('type', 'email')
        self.sender = dict_handler.get('from', None)
        self.receivers = dict_handler.get('to', [])
        self.subject = dict_handler.get('subject', 'WATCHER NOTIFICATION - {path}')
        self.smtp = dict_handler.get('smtp', {})
        self.attachment = dict_handler.get('attachment', False)
        self.zipped = dict_handler.get('zipped', False)
        if not all([self.sender, self.receivers, self.smtp]):
            utils.log(f'The following parameters in Email handler must not be empty: "from", "to", "smtp"!', how='warning', watched_path=self.watched_path)
            self.active = False

    def _emit_msg(self, event, message, src_path, dest_path):
        networking.send_email(message, self._format_str(self.subject), self.sender, self.receivers, self.smtp)

    def _emit_log(self, logfile):
        dafile = logfile
        if self.attachment:
            if self.zipped:
                # zip log file
                zfile = os.path.splitext(dafile)[0] + '.zip'
                try:
                    utils.zipfiles((dafile,), zfile)
                    dafile = zfile
                except Exception as err:
                    utils.log(err, how='exception', watched_path=self.watched_path)
            networking.send_email(f'ATTACHED: {os.path.basename(dafile)}', self._format_str(self.subject),
                                      self.sender, self.receivers, self.smtp, attachments=(dafile,))
        else:
            msg = open(dafile, 'r').read().strip()
            if msg:
                networking.send_email(msg, self._format_str(self.subject), self.sender, self.receivers, self.smtp)

# ============================================================= #

class PopupHandler(BaseHandler):

    def _update(self, dict_handler=None):
        super()._update(dict_handler)
        self.type = dict_handler.get('type', 'popup')
        self.subject = dict_handler.get('subject', 'WATCHER NOTIFICATION - {path}')
        self.ticker = dict_handler.get('ticker', 'WATCHER NOTIFICATION - {path}')
        self.icon = dict_handler.get('icon', 'auto')
        self.timeout = dict_handler.get('timeout', 5)

    def _emit_msg(self, event, message, src_path, dest_path):
        ico = self.icon
        if ico:
            ico = utils.abspath(f'img/ico_{event}.ico') if ico == 'auto' else os.path.abspath(ico)
        if not os.path.isfile(ico):
            ico = ''
        utils.sys_notify(self._format_str(self.subject), message, self.timeout, self._format_str(self.ticker), ico)

    def _emit_log(self, logfile):
        # TODO: handle toaster activation event (click) to open log file
        msg = open(logfile, 'r').read().strip()
        if msg:
            utils.sys_notify(self._format_str(self.subject), msg, self.timeout, self._format_str(self.ticker), '')

# ============================================================= #

class BaseWatcher:

    MHDLR = {'email': EmailHandler, 'popup': PopupHandler}

    def __init__(self, data, handler_kwargs={}):
        self.handlers = []
        self._handler_kwargs = handler_kwargs.copy() if handler_kwargs else {}
        self._it = None
        self._update(data)

    def _update(self, data):
        self._spawn_handlers(data.get('handlers', []))

    def _spawn_handlers(self, handlers):
        self.handlers.clear()
        self.add_handlers(handlers)

    def add_handlers(self, handlers, handler_kwargs=None):
        if not handlers: return
        if handler_kwargs is None:
            handler_kwargs = self._handler_kwargs
        for h in handlers:
            cls_ = BaseWatcher.MHDLR.get(h.get('type', ''), None)
            if cls_:
                self.handlers.append(cls_(h, **handler_kwargs))

    def trigger_all(self, event, message, src_path, dest_path):
        for handler in self.handlers:
            handler.trigger(event, message, src_path, dest_path)

    @property
    def has_active_handlers(self):
        handlers = getattr(self, 'handlers', None)
        return (not handlers is None) and any(h.active for h in handlers)

    def __bool__(self):
        return self.has_active_handlers

    def __len__(self):
        return len(self.handlers)

    def __iter__(self):
        self._it = iter(self.handlers)
        return self._it

    def __next__(self):
        return next(self._it)

# ============================================================= #

class DirWatcher(BaseWatcher):

    @property
    def is_path_ok(self):
        path = getattr(self, 'path', '')
        return os.path.isdir(path)

    def _update(self, data):
        self.path = data.get('path', '')
        if os.path.isdir(self.path):
            self.path = os.path.abspath(self.path)
        else:
            utils.log(f'Empty or non-existent path: "{self.path}"!', how='warning')
            self.path = ''
        self._handler_kwargs['watched_path'] = self.path
        self.types =  data.get('types', ['*'])
        self.recursive =  data.get('recursive', True)
        self.ignore_types =  data.get('ignore_types', None)
        self.ignore_dirs =  data.get('ignore_dirs', None)
        self.case_sensitive =  data.get('case_sensitive', False)
        super()._update(data)
        self.handler = None
        if self.path:
            self.handler = PatternMatchingEventHandler(self.types, self.ignore_types, self.ignore_dirs, self.case_sensitive)
            self.handler.on_any_event = DirWatcher.event_handler(self, self.path)

    @staticmethod
    def event_handler(watcher: BaseWatcher, watched_path):
        def wrapped_handler(event):
            if not bool(watcher): return

            fdir = 'DIRECTORY' if event.is_directory else 'FILE'
            msg = ''
            evt = ''
            src_path = event.src_path[len(watched_path):] if event.src_path else ''
            dest_path = ''

            if event.event_type == EVENT_TYPE_CREATED:
                # created
                msg = f'CREATED {fdir} {src_path}'
                evt = 'cre'
            elif event.event_type == EVENT_TYPE_MODIFIED:
                # modified
                msg = f'MODIFIED {fdir} {src_path}'
                evt = 'mod'
            elif event.event_type == EVENT_TYPE_MOVED:
                # moved
                dest_path = event.dest_path[len(watched_path):]
                if os.path.dirname(event.src_path) == os.path.dirname(event.dest_path):
                    msg = f'RENAMED {fdir} {src_path} ==> {os.path.basename(dest_path)}'
                    evt = 'ren'
                else:
                    msg = f'MOVED {fdir} {src_path} ==> {dest_path}'
                    evt = 'mov'
            elif event.event_type == EVENT_TYPE_DELETED:
                # deleted
                msg = f'DELETED {fdir} {src_path}'
                evt = 'del'
            else:
                return
            if not msg: return

            utils.log(msg, event=evt, watched_path=watched_path, source=src_path, destination=dest_path)
            watcher.trigger_all(evt, msg, src_path, dest_path)

        return wrapped_handler

    def __bool__(self):
        return self.has_active_handlers and self.is_path_ok


# ============================================================= #

class Watcher:

    def __init__(self):
        self.logging_watcher: BaseWatcher = None
        self.observer: Observer = None
        self.watchers = []
        self._create_logs()
        self.schedule_watchers()

    def __del__(self):
        self.stop()

    def _create_logs(self):
        # root logger
        utils.get_logger()
        # logging watcher
        if 'logging' in CONFIG and CONFIG['logging'].get('log', False) and CONFIG['logging'].get('file', ''):
            self.logging_watcher = BaseWatcher(CONFIG['logging'], {'create_log': False})

    def schedule_watchers(self):
        self.watchers.clear()

        if not CONFIG.get('watchers', None):
            utils.log('No watchers set in config file!', how='warning')
            return 0

        self.stop()
        try:
            self.observer = Observer(CONFIG.get('poll_interval', DEFAULT_POLL_SECONDS))
        except Exception as err:
            utils.log(err, how='exception')
            return 0

        for w in CONFIG['watchers']:
            try:
                watcher = DirWatcher(w)
                if watcher:
                    self.observer.schedule(watcher.handler, watcher.path, watcher.recursive)
                    self.watchers.append(watcher)
            except Exception as err:
                utils.log(err, how='exception', watched_path=watcher.path)

        return len(self.watchers)

    def _check_send_log(self):
        if not self.logging_watcher: return
        dafile = CONFIG['logging'].get('file', '') or ''
        if not os.path.isfile(dafile):
            return
        if not getattr(self, '_last_mdtime', None):
            self._last_mdtime = os.path.getmtime(dafile)
            return
        if os.path.getmtime(dafile) > self._last_mdtime:
            b_emitted = False
            for h in self.logging_watcher:
                if not 'last_time' in h.user_data:
                    h.user_data['last_time'] = utils.get_now()
                else:
                    target_interval = utils.span_to_seconds(h.emit['interval'], h.emit['unit'])
                    current_interval = utils.get_timedelta(h.user_data['last_time'])
                    # print(f'Target interval = {int(target_interval)}, current passed = {int(current_interval)} sec.')
                    if current_interval >= target_interval:
                        # print(f'Emitting {h} ...')
                        h.emit_log(dafile)
                        h.user_data['last_time'] = utils.get_now()
                        b_emitted = True
            if b_emitted:
                self._last_mdtime = os.path.getmtime(dafile)

    def run(self):
        if not self.observer and not (self.watchers or self.schedule_watchers()):
            utils.log('No watchers!', how='error')
            return

        try:
            utils.log(f"Using config file: {CONFIG_FILE}")
            utils.log(f"Starting observer with {len(self)} watchers ({self._get_watcher_paths()}). Polling every {self.observer.timeout} sec ...")
            self.observer.start()
            while True:
                try:
                    self._check_send_log()
                except Exception as err:
                    utils.log(err, how='exception')
                utils.sleep()

        except KeyboardInterrupt:
            utils.log('User interrupt', how='warning')
            self.stop()

        except Exception as err:
            utils.log(err, how='exception')
            self.stop()

        self.stop()

    def stop(self):
        if self.observer:
            try:
                utils.log(f"Stopping observer ...")
                self.observer.stop()
                self.observer.join()

            except RuntimeError:
                pass

            except Exception as err:
                utils.log(err, how='exception')

            self.watchers.clear()
            utils.log('Observer stopped')
            self.observer = None

    def _get_watcher_paths(self):
        return '; '.join([w['path'] for w in CONFIG['watchers'] if 'path' in w] if 'watchers' in CONFIG else [])

    def __len__(self):
        return len(self.watchers)

# ============================================================= #

def main():
    watcher = Watcher()
    watcher.run()

# ============================================================= #

if __name__ == '__main__':
    main()