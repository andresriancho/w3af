#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import re

from extra.safe2bin.safe2bin import safechardecode
from lib.core.agent import agent
from lib.core.bigarray import BigArray
from lib.core.common import Backend
from lib.core.common import getUnicode
from lib.core.common import isNoneValue
from lib.core.common import isNumPosStrValue
from lib.core.common import singleTimeWarnMessage
from lib.core.common import unArrayizeValue
from lib.core.common import unsafeSQLIdentificatorNaming
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import queries
from lib.core.dicts import DUMP_REPLACEMENTS
from lib.core.enums import CHARSET_TYPE
from lib.core.enums import EXPECTED
from lib.core.exception import SqlmapConnectionException
from lib.core.exception import SqlmapNoneDataException
from lib.core.settings import MAX_INT
from lib.core.unescaper import unescaper
from lib.request import inject

def pivotDumpTable(table, colList, count=None, blind=True):
    lengths = {}
    entries = {}

    dumpNode = queries[Backend.getIdentifiedDbms()].dump_table.blind

    validColumnList = False
    validPivotValue = False

    if count is None:
        query = dumpNode.count % table
        query = agent.whereQuery(query)
        count = inject.getValue(query, union=False, error=False, expected=EXPECTED.INT, charsetType=CHARSET_TYPE.DIGITS) if blind else inject.getValue(query, blind=False, time=False, expected=EXPECTED.INT)

    if isinstance(count, basestring) and count.isdigit():
        count = int(count)

    if count == 0:
        infoMsg = "table '%s' appears to be empty" % unsafeSQLIdentificatorNaming(table)
        logger.info(infoMsg)

        for column in colList:
            lengths[column] = len(column)
            entries[column] = []

        return entries, lengths

    elif not isNumPosStrValue(count):
        return None

    for column in colList:
        lengths[column] = 0
        entries[column] = BigArray()

    colList = filter(None, sorted(colList, key=lambda x: len(x) if x else MAX_INT))

    if conf.pivotColumn:
        for _ in colList:
            if re.search(r"(.+\.)?%s" % re.escape(conf.pivotColumn), _, re.I):
                infoMsg = "using column '%s' as a pivot " % conf.pivotColumn
                infoMsg += "for retrieving row data"
                logger.info(infoMsg)

                colList.remove(_)
                colList.insert(0, _)

                validPivotValue = True
                break

        if not validPivotValue:
            warnMsg = "column '%s' not " % conf.pivotColumn
            warnMsg += "found in table '%s'" % table
            logger.warn(warnMsg)

    if not validPivotValue:
        for column in colList:
            infoMsg = "fetching number of distinct "
            infoMsg += "values for column '%s'" % column
            logger.info(infoMsg)

            query = dumpNode.count2 % (column, table)
            query = agent.whereQuery(query)
            value = inject.getValue(query, blind=blind, union=not blind, error=not blind, expected=EXPECTED.INT, charsetType=CHARSET_TYPE.DIGITS)

            if isNumPosStrValue(value):
                validColumnList = True

                if value == count:
                    infoMsg = "using column '%s' as a pivot " % column
                    infoMsg += "for retrieving row data"
                    logger.info(infoMsg)

                    validPivotValue = True
                    colList.remove(column)
                    colList.insert(0, column)
                    break

        if not validColumnList:
            errMsg = "all column name(s) provided are non-existent"
            raise SqlmapNoneDataException(errMsg)

        if not validPivotValue:
            warnMsg = "no proper pivot column provided (with unique values)."
            warnMsg += " It won't be possible to retrieve all rows"
            logger.warn(warnMsg)

    pivotValue = " "
    breakRetrieval = False

    def _(column, pivotValue):
        if column == colList[0]:
            query = dumpNode.query.replace("'%s'", "%s") % (agent.preprocessField(table, column), table, agent.preprocessField(table, column), unescaper.escape(pivotValue, False))
        else:
            query = dumpNode.query2.replace("'%s'", "%s") % (agent.preprocessField(table, column), table, agent.preprocessField(table, colList[0]), unescaper.escape(pivotValue, False))

        query = agent.whereQuery(query)
        return unArrayizeValue(inject.getValue(query, blind=blind, time=blind, union=not blind, error=not blind))

    try:
        for i in xrange(count):
            if breakRetrieval:
                break

            for column in colList:
                value = _(column, pivotValue)
                if column == colList[0]:
                    if isNoneValue(value):
                        try:
                            for pivotValue in filter(None, ("  " if pivotValue == " " else None, "%s%s" % (pivotValue[0], unichr(ord(pivotValue[1]) + 1)) if len(pivotValue) > 1 else None, unichr(ord(pivotValue[0]) + 1))):
                                value = _(column, pivotValue)
                                if not isNoneValue(value):
                                    break
                        except ValueError:
                            pass

                    if isNoneValue(value):
                        breakRetrieval = True
                        break
                    pivotValue = safechardecode(value)

                if conf.limitStart or conf.limitStop:
                    if conf.limitStart and (i + 1) < conf.limitStart:
                        warnMsg = "skipping first %d pivot " % conf.limitStart
                        warnMsg += "point values"
                        singleTimeWarnMessage(warnMsg)
                        break
                    elif conf.limitStop and (i + 1) > conf.limitStop:
                        breakRetrieval = True
                        break

                value = "" if isNoneValue(value) else unArrayizeValue(value)

                lengths[column] = max(lengths[column], len(DUMP_REPLACEMENTS.get(getUnicode(value), getUnicode(value))))
                entries[column].append(value)

    except KeyboardInterrupt:
        kb.dumpKeyboardInterrupt = True

        warnMsg = "user aborted during enumeration. sqlmap "
        warnMsg += "will display partial output"
        logger.warn(warnMsg)

    except SqlmapConnectionException, e:
        errMsg = "connection exception detected. sqlmap "
        errMsg += "will display partial output"
        errMsg += "'%s'" % e
        logger.critical(errMsg)

    return entries, lengths
