#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import logging
import sys

from lib.core.enums import CUSTOM_LOGGING

logging.addLevelName(CUSTOM_LOGGING.PAYLOAD, "PAYLOAD")
logging.addLevelName(CUSTOM_LOGGING.TRAFFIC_OUT, "TRAFFIC OUT")
logging.addLevelName(CUSTOM_LOGGING.TRAFFIC_IN, "TRAFFIC IN")

LOGGER = logging.getLogger("sqlmapLog")

LOGGER_HANDLER = None
try:
    from thirdparty.ansistrm.ansistrm import ColorizingStreamHandler

    disableColor = False

    for argument in sys.argv:
        if "disable-col" in argument:
            disableColor = True
            break

    if disableColor:
        LOGGER_HANDLER = logging.StreamHandler(sys.stdout)
    else:
        LOGGER_HANDLER = ColorizingStreamHandler(sys.stdout)
        LOGGER_HANDLER.level_map[logging.getLevelName("PAYLOAD")] = (None, "cyan", False)
        LOGGER_HANDLER.level_map[logging.getLevelName("TRAFFIC OUT")] = (None, "magenta", False)
        LOGGER_HANDLER.level_map[logging.getLevelName("TRAFFIC IN")] = ("magenta", None, False)
except ImportError:
    LOGGER_HANDLER = logging.StreamHandler(sys.stdout)

FORMATTER = logging.Formatter("\r[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S")

LOGGER_HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(LOGGER_HANDLER)
LOGGER.setLevel(logging.WARN)
