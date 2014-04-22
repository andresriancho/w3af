#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

def cachedmethod(f, cache={}):
    """
    Method with a cached content

    Reference: http://code.activestate.com/recipes/325205-cache-decorator-in-python-24/
    """

    def _(*args, **kwargs):
        try:
            key = (f, tuple(args), frozenset(kwargs.items()))
        except:
            key = "".join(str(_) for _ in (f, args, kwargs))
        if key not in cache:
            cache[key] = f(*args, **kwargs)
        return cache[key]

    return _
