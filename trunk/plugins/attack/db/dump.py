#!/usr/bin/env python


class SQLMapDump:
    def dump( self, method, arguments, response ):
        '''
        The entry point for the other methods.
        '''
        if method == 'users':
            return self.list( 'Database users: ', response )
        elif method == 'dbs':
            return self.list( 'Available databases: ', response )
        elif method == 'tables':
            return self.dbTables( response )
        elif method == 'columns':
            return self.dbTableColumns( response )
        elif method == 'dump':
            return self.dbTableValues( response )
            
        return self.string( method, response )
    
    def string(self, header, string):
        res = ''
        
        if string:
            if "\n" in string:
                res += "%s:\n---\n%s---\n\n" % (header, string)
            else:
                res += "%s: '%s'\n\n" % (header, string)
        else:
            res += "%s:\tNone\n" % header
        
        return res.strip()

    def list(self, header, list):
        res = ''
        res += "%s [%d]:\n" % (header, len(list))

        list.sort()
        for element in list:
            res += "[*] %s\n" % element
        return res.strip()


    def dbTables(self, dbTables):
        res = ''
        maxlength = 0

        for tables in dbTables.values():
            for table in tables:
                maxlength = max(maxlength, len(table))

        lines = "-" * (int(maxlength) + 2)

        for db, tables in dbTables.items():
            res += "Database: %s\n" % db

            if len(tables) == 1:
                res += "[1 table]\n"
            else:
                res += "[%d tables]\n" % len(tables)

            res += "+%s+\n" % lines

            for table in tables:
                blank = " " * (maxlength - len(table))
                res +=  "| %s%s |\n" % (table, blank)

            res += "+%s+\n\n" % lines
        
        return res.strip()


    def dbTableColumns(self, tableColumns):
        res = ''
        for db, tables in tableColumns.items():
            if not db:
                db = "All"

            for table, columns in tables.items():
                maxlength1 = 0
                maxlength2 = 0

                for column, coltype in columns.items():
                    maxlength1 = max(maxlength1, len(column))
                    maxlength2 = max(maxlength2, len(coltype))

                maxlength1 = max(maxlength1, len("COLUMN"))
                maxlength2 = max(maxlength2, len("TYPE"))
                lines1 = "-" * (int(maxlength1) + 2)
                lines2 = "-" * (int(maxlength2) + 2)

                res += "Database: %s\nTable: %s\n" % (db, table)

                if len(columns) == 1:
                    res += "[1 column]\n"
                else:
                    res += "[%d columns]\n" % len(columns)

                res += "+%s+%s+\n" % (lines1, lines2)

                blank1 = " " * (maxlength1 - len("COLUMN"))
                blank2 = " " * (maxlength2 - len("TYPE"))

                res += "| Column%s" % blank1
                res += "| Type%s |\n" % blank2
                res += "+%s+%s+\n" % (lines1, lines2)

                for column, coltype in columns.items():
                    blank1 = " " * (maxlength1 - len(column))
                    blank2 = " " * (maxlength2 - len(coltype))
                    res += "| %s%s" % (column, blank1)
                    res += "| %s%s |\n" % (coltype, blank2)

                res += "+%s+%s+\n" % (lines1, lines2)
        
        return res.strip()


    def dbTableValues(self, tableValues):
        res = ''
        
        db = tableValues["__infos__"]["db"]
        if not db:
            db = "All"
        table = tableValues["__infos__"]["table"]
        count = int(tableValues["__infos__"]["count"])

        separator = ""

        for column, info in tableValues.items():
            if column != "__infos__":
                lines = "-" * (int(info["length"]) + 2)
                separator += "+%s" % lines

        separator += "+"
        res += "Database: %s\nTable: %s\n" % (db, table)

        count = int(tableValues["__infos__"]["count"])
        if count == 1:
            res += "[1 entry]\n"
        else:
            res += "[%d entries]\n" % count

        res += separator + '\n'

        for column, info in tableValues.items():
            if column != "__infos__":
                maxlength = int(info["length"])
                blank = " " * (maxlength - len(column))
                res +=  "| %s%s " % (column, blank)

        res += "|\n%s\n" % separator

        for i in range(count):
            for column, info in tableValues.items():
                if column != "__infos__":
                    value = info["values"][i]
                    maxlength = int(info["length"])
                    blank = " " * (maxlength - len(value))
                    res +=  "| %s%s " % (value, blank)

            res += "|\n"

        res += "%s\n" % separator
        
        return res.strip()
