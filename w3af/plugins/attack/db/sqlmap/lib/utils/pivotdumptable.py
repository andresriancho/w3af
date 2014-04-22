#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import re

from extra.safe2bin.safe2bin import safechardecode
from lib.core.agent import agent
from lib.core.bigarray import BigArray
from lib.core.common import Backend
from lib.core.common import isNoneValue
from lib.core.common import isNumPosStrValue
from lib.core.common import singleTimeWarnMessage
from lib.core.common import unArrayizeValue
from lib.core.common import unsafeSQLIdentificatorNaming
from lib.core.data import conf
from lib.core.data import logger
from lib.core.data import queries
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
        query = whereQuery(query)
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
        if any(re.search(r"(.+\.)?%s" % conf.pivotColumn, _, re.I) for _ in colList):
            infoMsg = "using column '%s' as a pivot " % conf.pivotColumn
            infoMsg += "for retrieving row data"
            logger.info(infoMsg)

            validPivotValue = True
            colList.remove(conf.pivotColumn)
            colList.insert(0, conf.pivotColumn)
        else:
            warnMsg = "column '%s' not " % conf.pivotColumn
            warnMsg += "found in table '%s'" % table
            logger.warn(warnMsg)

    if not validPivotValue:
        for column in colList:
            infoMsg = "fetching number of distinct "
            infoMsg += "values for column '%s'" % column
            logger.info(infoMsg)

            query = dumpNode.count2 % (column, table)
            query = whereQuery(query)
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

    try:
        for i in xrange(count):
            if breakRetrieval:
                break

            for column in colList:
                def _(pivotValue):
                    if column == colList[0]:
                        query = dumpNode.query.replace("'%s'", "%s") % (agent.preprocessField(table, column), table, agent.preprocessField(table, column), unescaper.escape(pivotValue, False))
                    else:
                        query = dumpNode.query2.replace("'%s'", "%s") % (agent.preprocessField(table, column), table, agent.preprocessField(table, colList[0]), unescaper.escape(pivotValue, False))

                    query = whereQuery(query)

                    return unArrayizeValue(inject.getValue(query, blind=blind, time=blind, union=not blind, error=not blind))

                value = _(pivotValue)
                if column == colList[0]:
                    if isNoneValue(value):
                        for pivotValue in filter(None, ("  " if pivotValue == " " else None, "%s%s" % (pivotValue[0], unichr(ord(pivotValue[1]) + 1)) if len(pivotValue) > 1 else None, unichr(ord(pivotValue[0]) + 1))):
                            value = _(pivotValue)
                            if not isNoneValue(value):
                                break
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

                lengths[column] = max(lengths[column], len(value) if value else 0)
                entries[column].append(value)

    except KeyboardInterrupt:
        warnMsg = "user aborted during enumeration. sqlmap "
        warnMsg += "will display partial output"
        logger.warn(warnMsg)

    except SqlmapConnectionException, e:
        errMsg = "connection exception detected. sqlmap "
        errMsg += "will display partial output"
        errMsg += "'%s'" % e
        logger.critical(errMsg)

    return entries, lengths

def whereQuery(query):
    if conf.dumpWhere and query:
        prefix, suffix = query.split(" ORDER BY ") if " ORDER BY " in query else (query, "")

        if "%s)" % conf.tbl.upper() in prefix.upper():
            prefix = re.sub(r"(?i)%s\)" % conf.tbl, "%s WHERE %s)" % (conf.tbl, conf.dumpWhere), prefix)
        elif re.search(r"(?i)\bWHERE\b", prefix):
            prefix += " AND %s" % conf.dumpWhere
        else:
            prefix += " WHERE %s" % conf.dumpWhere

        query = "%s ORDER BY %s" % (prefix, suffix) if suffix else prefix

    return query
