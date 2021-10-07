# -*- coding: utf-8 -*-
import os, sys
from ruamel.yaml import YAML

# ============================================================= #

CONFIG_FILE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'config.yaml')

if not os.path.isfile(CONFIG_FILE):
    raise Exception('No config file found!')
    
with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = YAML().load(f)

DEFAULT_POLL_SECONDS = 10

# ============================================================= #

