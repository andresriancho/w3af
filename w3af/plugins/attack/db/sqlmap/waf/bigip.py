#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import re

from lib.core.enums import HTTP_HEADER
from lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "BIG-IP Application Security Manager (F5 Networks)"

def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        page, headers, code = get_page(get=vector)
        retval = headers.get("X-Cnection", "").lower() == "close"
        retval |= re.search(r"\ATS[a-zA-Z0-9]{3,6}=", headers.get(HTTP_HEADER.SET_COOKIE, ""), re.I) is not None
        retval |= re.search(r"BigIP|BIGipServer", headers.get(HTTP_HEADER.SERVER, ""), re.I) is not None
        if retval:
            break

    return retval
