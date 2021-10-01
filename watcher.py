# -*- coding: utf-8 -*-
import os
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import (PatternMatchingEventHandler, 
                             EVENT_TYPE_MOVED, EVENT_TYPE_DELETED, EVENT_TYPE_CREATED, EVENT_TYPE_MODIFIED)

from globals import *
import utils
import networking                        

# ============================================================= #

class Watcher:

    def __init__(self):
        self.observer: Observer = None
        self._count = 0

    def __del__(self):
        self.stop()

    @staticmethod
    def event_handler(handlers, watched_path):
        def wrapped_handler(event):
            if not handlers: return
            fdir = 'DIRECTORY' if event.is_directory else 'FILE'
            msg = ''
            evt = ''
            if event.event_type == EVENT_TYPE_CREATED:
                # created
                msg = f'CREATED {fdir} "{event.src_path}"'
                evt = 'cre'
            elif event.event_type == EVENT_TYPE_MODIFIED:
                # modified
                msg = f'MODIFIED {fdir} "{event.src_path}"'
                evt = 'mod'
            elif event.event_type == EVENT_TYPE_MOVED:
                # moved
                if os.path.dirname(event.src_path) == os.path.dirname(event.dest_path):
                    msg = f'RENAMED {fdir} "{event.src_path}" ==> "{os.path.basename(event.dest_path)}"'
                    evt = 'ren'
                else:
                    msg = f'MOVED {fdir} "{event.src_path}" ==> "{event.dest_path}"'
                    evt = 'mov'
            elif event.event_type == EVENT_TYPE_DELETED:
                # deleted
                msg = f'DELETED {fdir} "{event.src_path}"'
                evt = 'del'
            else:
                return
            if not msg: return

            utils.log('>>> ' + msg)

            for handler in handlers:
                if not handler.get('active', False): continue
                events = handler.get('events', [])
                if not events: continue
                if not any(['cre' in events and evt == 'cre', 'mod' in events and evt == 'mod',
                            'mov' in events and evt in ('mov', 'ren'), 'del' in events and evt == 'del']):
                    continue

                utils.log(f"=== Handling '{evt}' event with {handler['type']} type handler...")

                if handler['type'] == 'email':
                    utils.log('--- Sending email to: ' + '; '.join(handler['to']))
                    networking.send_email(msg, handler['subject'].format(path=watched_path), handler['from'], handler['to'], handler['smtp'])

                elif handler['type'] == 'popup':
                    ico = handler.get('icon', '')
                    if ico: ico = utils.abspath(f'img/ico_{evt}.ico') if ico == 'auto' else os.path.abspath(ico)
                    if not os.path.isfile(ico): ico = ''
                    utils.sys_notify(handler['subject'].format(path=watched_path), msg, handler.get('timeout', 10), (handler.get('ticker', '') or '').format(path=watched_path), ico)

        return wrapped_handler

    def run(self):
        if not self.observer and not self.schedule_watchers():
            return

        try:
            utils.log(f"Starting observer with {self._count} watchers (polling every {self.observer.timeout} sec) ...")
            self.observer.start()
            while True:
                pass

        except KeyboardInterrupt:
            utils.log("User interrupt", how='warning')
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

            except Exception as err:
                utils.log(err, how='exception')

            self._count = 0
            utils.log(f"Observer stopped")
            self.observer = None

    def schedule_watchers(self):
        self._count = 0

        if not CONFIG.get('watchers', None):
            utils.log('No watchers set in config file!', how='warning')
            return 0

        self.stop()        
        self.observer = Observer(CONFIG.get('poll_interval', DEFAULT_POLL_SECONDS))

        j = 0
        for i, w in enumerate(CONFIG['watchers']):
            path = w.get('path', '')
            if path: path = os.path.abspath(path)
            if not os.path.isdir(path):
                utils.log(f'No path set for watcher {i}', how='warning')
                continue

            if not w.get('handlers', None):
                utils.log(f'No handlers set for watcher {i}', how='warning')
                continue

            print(w.get('types', ['*']))
            handler = PatternMatchingEventHandler(w.get('types', ['*']), w.get('ignore_types', None), w.get('ignore_dirs', None), w.get('case_sensitive', False))
            handler.on_any_event = Watcher.event_handler(w['handlers'], path)

            self.observer.schedule(handler, path, recursive=w.get('recursive', True))
            j += 1

        self._count = j
        return self._count
        

# ============================================================= #

def main():
    watcher = Watcher()
    watcher.run()

# ============================================================= #

if __name__ == '__main__':
    main()