#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

from lib.core.common import filterPairValues
from lib.core.common import isTechniqueAvailable
from lib.core.common import randomStr
from lib.core.common import readInput
from lib.core.common import safeSQLIdentificatorNaming
from lib.core.common import unArrayizeValue
from lib.core.common import unsafeSQLIdentificatorNaming
from lib.core.data import conf
from lib.core.data import kb
from lib.core.data import logger
from lib.core.data import paths
from lib.core.data import queries
from lib.core.dicts import SYBASE_TYPES
from lib.core.enums import DBMS
from lib.core.enums import PAYLOAD
from lib.core.exception import SqlmapMissingMandatoryOptionException
from lib.core.exception import SqlmapNoneDataException
from lib.core.exception import SqlmapUserQuitException
from lib.core.settings import CURRENT_DB
from lib.utils.brute import columnExists
from lib.utils.pivotdumptable import pivotDumpTable
from plugins.generic.enumeration import Enumeration as GenericEnumeration


class Enumeration(GenericEnumeration):
    def __init__(self):
        GenericEnumeration.__init__(self)

    def getUsers(self):
        infoMsg = "fetching database users"
        logger.info(infoMsg)

        rootQuery = queries[DBMS.SYBASE].users

        randStr = randomStr()
        query = rootQuery.inband.query

        if any(
            isTechniqueAvailable(_) for _ in (
                PAYLOAD.TECHNIQUE.UNION,
                PAYLOAD.TECHNIQUE.ERROR,
                PAYLOAD.TECHNIQUE.QUERY)) or conf.direct:
            blinds = (False, True)
        else:
            blinds = (True,)

        for blind in blinds:
            retVal = pivotDumpTable(
                "(%s) AS %s" %
                (query, randStr), [
                    '%s.name' %
                    randStr], blind=blind)

            if retVal:
                kb.data.cachedUsers = retVal[0].values()[0]
                break

        return kb.data.cachedUsers

    def getPrivileges(self, *args):
        warnMsg = "on Sybase it is not possible to fetch "
        warnMsg += "database users privileges, sqlmap will check whether "
        warnMsg += "or not the database users are database administrators"
        logger.warn(warnMsg)

        users = []
        areAdmins = set()

        if conf.user:
            users = [conf.user]
        elif not len(kb.data.cachedUsers):
            users = self.getUsers()
        else:
            users = kb.data.cachedUsers

        for user in users:
            user = unArrayizeValue(user)

            if user is None:
                continue

            isDba = self.isDba(user)

            if isDba is True:
                areAdmins.add(user)

            kb.data.cachedUsersPrivileges[user] = None

        return (kb.data.cachedUsersPrivileges, areAdmins)

    def getDbs(self):
        if len(kb.data.cachedDbs) > 0:
            return kb.data.cachedDbs

        infoMsg = "fetching database names"
        logger.info(infoMsg)

        rootQuery = queries[DBMS.SYBASE].dbs
        randStr = randomStr()
        query = rootQuery.inband.query

        if any(
            isTechniqueAvailable(_) for _ in (
                PAYLOAD.TECHNIQUE.UNION,
                PAYLOAD.TECHNIQUE.ERROR,
                PAYLOAD.TECHNIQUE.QUERY)) or conf.direct:
            blinds = [False, True]
        else:
            blinds = [True]

        for blind in blinds:
            retVal = pivotDumpTable(
                "(%s) AS %s" %
                (query, randStr), [
                    '%s.name' %
                    randStr], blind=blind)

            if retVal:
                kb.data.cachedDbs = retVal[0].values()[0]
                break

        if kb.data.cachedDbs:
            kb.data.cachedDbs.sort()

        return kb.data.cachedDbs

    def getTables(self, bruteForce=None):
        if len(kb.data.cachedTables) > 0:
            return kb.data.cachedTables

        self.forceDbmsEnum()

        if conf.db == CURRENT_DB:
            conf.db = self.getCurrentDb()

        if conf.db:
            dbs = conf.db.split(',')
        else:
            dbs = self.getDbs()

        for db in dbs:
            dbs[dbs.index(db)] = safeSQLIdentificatorNaming(db)

        dbs = filter(None, dbs)

        infoMsg = "fetching tables for database"
        infoMsg += "%s: %s" % ("s" if len(dbs) > 1 else "",
                               ", ".join(
            db if isinstance(
                db,
                basestring) else db[0] for db in sorted(dbs)))
        logger.info(infoMsg)

        if any(
            isTechniqueAvailable(_) for _ in (
                PAYLOAD.TECHNIQUE.UNION,
                PAYLOAD.TECHNIQUE.ERROR,
                PAYLOAD.TECHNIQUE.QUERY)) or conf.direct:
            blinds = [False, True]
        else:
            blinds = [True]

        rootQuery = queries[DBMS.SYBASE].tables

        for db in dbs:
            for blind in blinds:
                randStr = randomStr()
                query = rootQuery.inband.query % db
                retVal = pivotDumpTable(
                    "(%s) AS %s" %
                    (query, randStr), [
                        '%s.name' %
                        randStr], blind=blind)

                if retVal:
                    for table in retVal[0].values()[0]:
                        if db not in kb.data.cachedTables:
                            kb.data.cachedTables[db] = [table]
                        else:
                            kb.data.cachedTables[db].append(table)
                    break

        for db, tables in kb.data.cachedTables.items():
            kb.data.cachedTables[db] = sorted(tables) if tables else tables

        return kb.data.cachedTables

    def getColumns(
            self,
            onlyColNames=False,
            colTuple=None,
            bruteForce=None,
            dumpMode=False):
        self.forceDbmsEnum()

        if conf.db is None or conf.db == CURRENT_DB:
            if conf.db is None:
                warnMsg = "missing database parameter. sqlmap is going "
                warnMsg += "to use the current database to enumerate "
                warnMsg += "table(s) columns"
                logger.warn(warnMsg)

            conf.db = self.getCurrentDb()

        elif conf.db is not None:
            if ',' in conf.db:
                errMsg = "only one database name is allowed when enumerating "
                errMsg += "the tables' columns"
                raise SqlmapMissingMandatoryOptionException(errMsg)

        conf.db = safeSQLIdentificatorNaming(conf.db)

        if conf.col:
            colList = conf.col.split(',')
        else:
            colList = []

        if conf.excludeCol:
            colList = [
                _ for _ in colList if _ not in conf.excludeCol.split(',')]

        for col in colList:
            colList[colList.index(col)] = safeSQLIdentificatorNaming(col)

        if conf.tbl:
            tblList = conf.tbl.split(',')
        else:
            self.getTables()

            if len(kb.data.cachedTables) > 0:
                tblList = kb.data.cachedTables.values()

                if isinstance(tblList[0], (set, tuple, list)):
                    tblList = tblList[0]
            else:
                errMsg = "unable to retrieve the tables "
                errMsg += "on database '%s'" % unsafeSQLIdentificatorNaming(
                    conf.db)
                raise SqlmapNoneDataException(errMsg)

        for tbl in tblList:
            tblList[tblList.index(tbl)] = safeSQLIdentificatorNaming(tbl)

        if bruteForce:
            resumeAvailable = False

            for tbl in tblList:
                for db, table, colName, colType in kb.brute.columns:
                    if db == conf.db and table == tbl:
                        resumeAvailable = True
                        break

            if resumeAvailable and not conf.freshQueries or colList:
                columns = {}

                for column in colList:
                    columns[column] = None

                for tbl in tblList:
                    for db, table, colName, colType in kb.brute.columns:
                        if db == conf.db and table == tbl:
                            columns[colName] = colType

                    if conf.db in kb.data.cachedColumns:
                        kb.data.cachedColumns[safeSQLIdentificatorNaming(
                            conf.db)][safeSQLIdentificatorNaming(tbl, True)] = columns
                    else:
                        kb.data.cachedColumns[safeSQLIdentificatorNaming(conf.db)] = {
                            safeSQLIdentificatorNaming(tbl, True): columns}

                return kb.data.cachedColumns

            message = "do you want to use common column existence check? [y/N/q] "
            choice = readInput(
                message, default='Y' if 'Y' in message else 'N').upper()

            if choice == 'N':
                return
            elif choice == 'Q':
                raise SqlmapUserQuitException
            else:
                return columnExists(paths.COMMON_COLUMNS)

        rootQuery = queries[DBMS.SYBASE].columns

        if any(
            isTechniqueAvailable(_) for _ in (
                PAYLOAD.TECHNIQUE.UNION,
                PAYLOAD.TECHNIQUE.ERROR,
                PAYLOAD.TECHNIQUE.QUERY)) or conf.direct:
            blinds = [False, True]
        else:
            blinds = [True]

        for tbl in tblList:
            if conf.db is not None and len(kb.data.cachedColumns) > 0 \
               and conf.db in kb.data.cachedColumns and tbl in \
               kb.data.cachedColumns[conf.db]:
                infoMsg = "fetched tables' columns on "
                infoMsg += "database '%s'" % unsafeSQLIdentificatorNaming(
                    conf.db)
                logger.info(infoMsg)

                return {conf.db: kb.data.cachedColumns[conf.db]}

            if dumpMode and colList:
                table = {}
                table[safeSQLIdentificatorNaming(tbl)] = dict(
                    (_, None) for _ in colList)
                kb.data.cachedColumns[safeSQLIdentificatorNaming(
                    conf.db)] = table
                continue

            infoMsg = "fetching columns "
            infoMsg += "for table '%s' " % unsafeSQLIdentificatorNaming(tbl)
            infoMsg += "on database '%s'" % unsafeSQLIdentificatorNaming(
                conf.db)
            logger.info(infoMsg)

            for blind in blinds:
                randStr = randomStr()
                query = rootQuery.inband.query % (conf.db,
                                                  conf.db,
                                                  conf.db,
                                                  conf.db,
                                                  conf.db,
                                                  conf.db,
                                                  conf.db,
                                                  unsafeSQLIdentificatorNaming(tbl))
                retVal = pivotDumpTable(
                    "(%s) AS %s" %
                    (query, randStr), [
                        '%s.name' %
                        randStr, '%s.usertype' %
                        randStr], blind=blind)

                if retVal:
                    table = {}
                    columns = {}

                    for name, type_ in filterPairValues(
                            zip(retVal[0]["%s.name" % randStr], retVal[0]["%s.usertype" % randStr])):
                        columns[name] = SYBASE_TYPES.get(int(type_) if isinstance(
                            type_, basestring) and type_.isdigit() else type_, type_)

                    table[safeSQLIdentificatorNaming(tbl)] = columns
                    kb.data.cachedColumns[safeSQLIdentificatorNaming(
                        conf.db)] = table

                    break

        return kb.data.cachedColumns

    def searchDb(self):
        warnMsg = "on Sybase searching of databases is not implemented"
        logger.warn(warnMsg)

        return []

    def searchTable(self):
        warnMsg = "on Sybase searching of tables is not implemented"
        logger.warn(warnMsg)

        return []

    def searchColumn(self):
        warnMsg = "on Sybase searching of columns is not implemented"
        logger.warn(warnMsg)

        return []

    def search(self):
        warnMsg = "on Sybase search option is not available"
        logger.warn(warnMsg)

    def getHostname(self):
        warnMsg = "on Sybase it is not possible to enumerate the hostname"
        logger.warn(warnMsg)
