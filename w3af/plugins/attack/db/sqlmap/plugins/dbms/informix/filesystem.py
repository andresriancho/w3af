#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from plugins.generic.filesystem import Filesystem as GenericFilesystem


class Filesystem(GenericFilesystem):
    def __init__(self):
        GenericFilesystem.__init__(self)
