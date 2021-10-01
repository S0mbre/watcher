# -*- coding: utf-8 -*-
import os, sys, json, logging

CONFIG_FILE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'config.json')
if not os.path.isfile(CONFIG_FILE):
    raise Exception('No config file found!')

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = json.load(f)

LOG = ('logging' in CONFIG) and CONFIG['logging'].get('log', False)
if LOG:
    logging.basicConfig(filename=CONFIG['logging'].get('file', None), encoding='utf-8', level=logging.DEBUG if CONFIG['logging'].get('verbose', False) else logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S')

DEFAULT_POLL_SECONDS = 10

# ============================================================= #

