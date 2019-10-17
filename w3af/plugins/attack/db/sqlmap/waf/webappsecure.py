#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

__product__ = "webApp.secure (webScurity)"


def detect(get_page):
    _, _, code = get_page()
    if code == 403:
        return False
    _, _, code = get_page(get="nx=@@")
    return code == 403
