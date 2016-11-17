# -*- coding: utf-8 -*-

"""
非常简单的日志模块

@author: X0Leon
@version: 0.3
"""

import logging

def setup_logger(filename=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if filename is not None:
        file_handler = logging.FileHandler('log.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

