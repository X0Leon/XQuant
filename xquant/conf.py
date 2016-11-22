# -*- coding: utf-8 -*-

import logging
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), 'out')

LOG = {'ROOT_LEVEL': logging.INFO,
       'CONSOLE_LEVEL': logging.INFO,
       'FILE_LEVEL': logging.INFO,
       'TO_FILE': False}
