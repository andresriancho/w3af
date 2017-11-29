"""
sqli.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.dbms as dbms
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.kb.vuln import Vuln


class sqli(AuditPlugin):
    """
    Find SQL injection bugs.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SQL_ERRORS_STR = (
        # ASP / MSSQL
        (r'System.Data.OleDb.OleDbException', dbms.MSSQL),
        (r'[SQL Server]', dbms.MSSQL),
        (r'[Microsoft][ODBC SQL Server Driver]', dbms.MSSQL),
        (r'[SQLServer JDBC Driver]', dbms.MSSQL),
        (r'[SqlException', dbms.MSSQL),
        (r'System.Data.SqlClient.SqlException', dbms.MSSQL),
        (r'Unclosed quotation mark after the character string', dbms.MSSQL),
        (r"'80040e14'", dbms.MSSQL),
        (r'mssql_query()', dbms.MSSQL),
        (r'odbc_exec()', dbms.MSSQL),
        (r'Microsoft OLE DB Provider for ODBC Drivers', dbms.MSSQL),
        (r'Microsoft OLE DB Provider for SQL Server', dbms.MSSQL),
        (r'Incorrect syntax near', dbms.MSSQL),
        (r'Sintaxis incorrecta cerca de', dbms.MSSQL),
        (r'Syntax error in string in query expression', dbms.MSSQL),
        (r'ADODB.Field (0x800A0BCD)<br>', dbms.MSSQL),
        (r"ADODB.Recordset'", dbms.MSSQL),
        (r"Unclosed quotation mark before the character string", dbms.MSSQL),
        (r"'80040e07'", dbms.MSSQL),
        (r'Microsoft SQL Native Client error', dbms.MSSQL),
        (r'SQL Server Native Client', dbms.MSSQL),
        (r'Invalid SQL statement', dbms.MSSQL),

        # DB2
        (r'SQLCODE', dbms.DB2),
        (r'DB2 SQL error:', dbms.DB2),
        (r'SQLSTATE', dbms.DB2),
        (r'[CLI Driver]', dbms.DB2),
        (r'[DB2/6000]', dbms.DB2),

        # Sybase
        (r"Sybase message:", dbms.SYBASE),
        (r"Sybase Driver", dbms.SYBASE),
        (r"[SYBASE]", dbms.SYBASE),

        # Access
        (r'Syntax error in query expression', dbms.ACCESS),
        (r'Data type mismatch in criteria expression.', dbms.ACCESS),
        (r'Microsoft JET Database Engine', dbms.ACCESS),
        (r'[Microsoft][ODBC Microsoft Access Driver]', dbms.ACCESS),

        # ORACLE
        (r'Microsoft OLE DB Provider for Oracle', dbms.ORACLE),
        (r'wrong number or types', dbms.ORACLE),

        # POSTGRE
        (r'PostgreSQL query failed:', dbms.POSTGRE),
        (r'supplied argument is not a valid PostgreSQL result', dbms.POSTGRE),
        (r'unterminated quoted string at or near', dbms.POSTGRE),
        (r'pg_query() [:', dbms.POSTGRE),
        (r'pg_exec() [:', dbms.POSTGRE),

        # MYSQL
        (r'supplied argument is not a valid MySQL', dbms.MYSQL),
        (r'Column count doesn\'t match value count at row', dbms.MYSQL),
        (r'mysql_fetch_array()', dbms.MYSQL),
        (r'mysql_', dbms.MYSQL),
        (r'on MySQL result index', dbms.MYSQL),
        (r'You have an error in your SQL syntax;', dbms.MYSQL),
        (r'You have an error in your SQL syntax near', dbms.MYSQL),
        (r'MySQL server version for the right syntax to use', dbms.MYSQL),
        (r'Division by zero in', dbms.MYSQL),
        (r'not a valid MySQL result', dbms.MYSQL),
        (r'[MySQL][ODBC', dbms.MYSQL),
        (r"Column count doesn't match", dbms.MYSQL),
        (r"the used select statements have different number of columns",
            dbms.MYSQL),
        (r"DBD::mysql::st execute failed", dbms.MYSQL),
        (r"DBD::mysql::db do failed:", dbms.MYSQL),

        # Informix
        (r'com.informix.jdbc', dbms.INFORMIX),
        (r'Dynamic Page Generation Error:', dbms.INFORMIX),
        (r'An illegal character has been found in the statement',
            dbms.INFORMIX),
        (r'[Informix]', dbms.INFORMIX),
        (r'<b>Warning</b>:  ibase_', dbms.INTERBASE),
        (r'Dynamic SQL Error', dbms.INTERBASE),

        # DML
        (r'[DM_QUERY_E_SYNTAX]', dbms.DMLDATABASE),
        (r'has occurred in the vicinity of:', dbms.DMLDATABASE),
        (r'A Parser Error (syntax error)', dbms.DMLDATABASE),

        # Java
        (r'java.sql.SQLException', dbms.JAVA),
        (r'Unexpected end of command in statement', dbms.JAVA),

        # Coldfusion
        (r'[Macromedia][SQLServer JDBC Driver]', dbms.MSSQL),

        # SQLite
        (r'could not prepare statement', dbms.SQLITE),

        # Generic errors..
        (r'Unknown column', dbms.UNKNOWN),
        (r'where clause', dbms.UNKNOWN),
        (r'SqlServer', dbms.UNKNOWN),
        (r'syntax error', dbms.UNKNOWN),
        (r'Microsoft OLE DB Provider', dbms.UNKNOWN),
    )
    _multi_in = MultiIn(x[0] for x in SQL_ERRORS_STR)

    SQL_ERRORS_RE = (
        # ASP / MSSQL
        (r"Procedure '[^']+' requires parameter '[^']+'", dbms.MSSQL),
        # ORACLE
        (r'PLS-[0-9][0-9][0-9][0-9]', dbms.ORACLE),
        (r'ORA-[0-9][0-9][0-9][0-9]', dbms.ORACLE),
        # MYSQL
        (r"Table '[^']+' doesn't exist", dbms.MYSQL),
        # Generic errors..
        (r'SELECT .*? FROM .*?', dbms.UNKNOWN),
        (r'UPDATE .*? SET .*?', dbms.UNKNOWN),
        (r'INSERT INTO .*?', dbms.UNKNOWN),
    )
    _multi_re = MultiRE(SQL_ERRORS_RE)

    # Note that these payloads are similar but they do generate different errors
    # depending on the SQL query context they are used. Removing one or the
    # other will lower our SQLMap testenv coverage
    SQLI_STRINGS = (u"a'b\"c'd\"",
                    u"1'2\"3")

    SQLI_MESSAGE = (u'A SQL error was found in the response supplied by '
                    u'the web application, the error is (only a fragment is '
                    u'shown): "%s". The error was found on response with id'
                    u' %s.')

    def __init__(self):
        AuditPlugin.__init__(self)

    def audit(self, freq, orig_response, debugging_id):
        """
        Tests an URL for SQL injection vulnerabilities.

        :param freq: A FuzzableRequest
        :param orig_response: The HTTP response associated with the fuzzable request
        :param debugging_id: A unique identifier for this call to audit()
        """
        mutants = create_mutants(freq, self.SQLI_STRINGS, orig_resp=orig_response)

        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result,
                                      debugging_id=debugging_id)

    def _analyze_result(self, mutant, response):
        """
        Analyze results of the _send_mutant method.
        """
        sql_error_list = self._findsql_error(response)
        orig_resp_body = mutant.get_original_response_body()

        for sql_error_string, dbms_type in sql_error_list:
            if sql_error_string not in orig_resp_body:
                if self._has_no_bug(mutant):
                    # Create the vuln,
                    desc = 'SQL injection in a %s was found at: %s'
                    desc %= dbms_type, mutant.found_at()
                                        
                    v = Vuln.from_mutant('SQL injection', desc, severity.HIGH,
                                         response.id, self.get_name(), mutant)

                    v.add_to_highlight(sql_error_string)
                    v['error'] = sql_error_string
                    v['db'] = dbms_type
                    
                    self.kb_append_uniq(self, 'sqli', v)
                    break

    def _findsql_error(self, response):
        """
        This method searches for SQL errors in html's.

        :param response: The HTTP response object
        :return: A list of errors found on the page
        """
        res = []

        for match in self._multi_in.query(response.body):
            om.out.information(self.SQLI_MESSAGE % (match, response.id))
            dbms_type = [x[1] for x in self.SQL_ERRORS_STR if x[0] == match][0]
            res.append((match, dbms_type))

        for match, _, regex_comp, dbms_type in self._multi_re.query(response.body):
            om.out.information(self.SQLI_MESSAGE % (match.group(0), response.id))
            res.append((match.group(0), dbms_type))

        return res

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds SQL injections. To find this vulnerabilities the
        plugin sends the string d'z"0 to every injection point, and searches
        for SQL errors in the response body.
        """
