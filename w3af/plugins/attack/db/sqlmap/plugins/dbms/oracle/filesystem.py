#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.exception import SqlmapUnsupportedFeatureException
from plugins.generic.filesystem import Filesystem as GenericFilesystem

class Filesystem(GenericFilesystem):
    def __init__(self):
        GenericFilesystem.__init__(self)

    def readFile(self, rFile):
        errMsg = "File system read access not yet implemented for "
        errMsg += "Oracle"
        raise SqlmapUnsupportedFeatureException(errMsg)

    def writeFile(self, wFile, dFile, fileType=None, forceCheck=False):
        errMsg = "File system write access not yet implemented for "
        errMsg += "Oracle"
        raise SqlmapUnsupportedFeatureException(errMsg)
