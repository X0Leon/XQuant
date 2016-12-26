# -*- coding: utf-8 -*-

import logging
import os

# OUT_PATH = os.path.join(os.path.dirname(__file__), 'out')
OUT_PATH = os.path.join(os.path.expanduser("~"))

LOG = {'ROOT_LEVEL': logging.INFO,
       'CONSOLE_LEVEL': logging.INFO,
       'FILE_LEVEL': logging.INFO,
       'TO_FILE': False}
