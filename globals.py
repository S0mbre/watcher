# -*- coding: utf-8 -*-
import os, sys
from ruamel.yaml import YAML

# ============================================================= #

ROOT_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))

config_file_ = sys.argv[1] if len(sys.argv) > 1 else 'config.yaml'
if not os.path.isabs(config_file_):
    config_file_ = os.path.join(ROOT_DIR, config_file_)

if not os.path.isfile(config_file_):
    raise Exception('No config file found!')

CONFIG_FILE = config_file_

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    CONFIG = YAML().load(f)

DEFAULT_POLL_SECONDS = 10

# ============================================================= #