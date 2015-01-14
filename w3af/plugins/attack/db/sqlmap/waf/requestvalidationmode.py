#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.settings import WAF_ATTACK_VECTORS

__product__ = "ASP.NET RequestValidationMode (Microsoft)"

def detect(get_page):
    retval = False

    for vector in WAF_ATTACK_VECTORS:
        page, headers, code = get_page(get=vector)
        retval = "ASP.NET has detected data in the request that is potentially dangerous" in page
        retval |= "Request Validation has detected a potentially dangerous client input value" in page
        if retval:
            break

    return retval
