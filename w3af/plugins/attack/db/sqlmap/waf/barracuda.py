#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from lib.core.enums import HTTP_HEADER
from lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "Barracuda Web Application Firewall (Barracuda Networks)"


def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        _, headers, _ = get_page(get=vector)
        retval = re.search(
            r"\Abarra_counter_session=",
            headers.get(
                HTTP_HEADER.SET_COOKIE,
                ""),
            re.I) is not None
        retval |= re.search(
            r"(\A|\b)barracuda_",
            headers.get(
                HTTP_HEADER.SET_COOKIE,
                ""),
            re.I) is not None
        if retval:
            break

    return retval
