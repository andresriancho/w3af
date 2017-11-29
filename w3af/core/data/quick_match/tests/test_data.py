"""
test_data.py

Copyright 2017 Andres Riancho

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

HTTP_RESPONSE = """
<br />
<b>Fatal error</b>:  Uncaught exception 'Exception' with message 'Error performing query: SELECT * FROM users where name='d'z&quot;0': &lt;br /&gt;1064: You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'z&quot;0'' at line 1' in /var/www/w3af/audit/sql_injection/select/sql_injection_string.php:15
Stack trace:
#0 {main}
thrown in <b>/var/www/w3af/audit/sql_injection/select/sql_injection_string.php</b> on line <b>15</b><br />
  """

SQL_ERRORS = (
    # ASP / MSSQL
    (r'System\.Data\.OleDb\.OleDbException', ),
    (r'\[SQL Server\]', ),
    (r'\[Microsoft\]\[ODBC SQL Server Driver\]', ),
    (r'\[SQLServer JDBC Driver\]', ),
    (r'\[SqlException', ),
    (r'System.Data.SqlClient.SqlException', ),
    (r'Unclosed quotation mark after the character string', ),
    (r"'80040e14'", ),
    (r'mssql_query\(\)', ),
    (r'odbc_exec\(\)', ),
    (r'Microsoft OLE DB Provider for ODBC Drivers', ),
    (r'Microsoft OLE DB Provider for SQL Server', ),
    (r'Incorrect syntax near', ),
    (r'Sintaxis incorrecta cerca de', ),
    (r'Syntax error in string in query expression', ),
    (r'ADODB\.Field \(0x800A0BCD\)<br>', ),
    (r"Procedure '[^']+' requires parameter '[^']+'", ),
    (r"ADODB\.Recordset'", ),
    (r"Unclosed quotation mark before the character string", ),
    (r"'80040e07'", ),
    (r'Microsoft SQL Native Client error', ),
    # DB2
    (r'SQLCODE', ),
    (r'DB2 SQL error:', ),
    (r'SQLSTATE', ),
    (r'\[CLI Driver\]', ),
    (r'\[DB2/6000\]', ),
    # Sybase
    (r"Sybase message:", ),
    (r"Sybase Driver", ),
    (r"\[SYBASE\]", ),
    # Access
    (r'Syntax error in query expression', ),
    (r'Data type mismatch in criteria expression.', ),
    (r'Microsoft JET Database Engine', ),
    (r'\[Microsoft\]\[ODBC Microsoft Access Driver\]', ),
    # ORACLE
    (r'(PLS|ORA)-[0-9][0-9][0-9][0-9]', ),
    # POSTGRE
    (r'PostgreSQL query failed:', ),
    (r'supplied argument is not a valid PostgreSQL result', ),
    (r'pg_query\(\) \[:', ),
    (r'pg_exec\(\) \[:', ),
    # MYSQL
    (r'supplied argument is not a valid MySQL', ),
    (r'Column count doesn\'t match value count at row', ),
    (r'mysql_fetch_array\(\)', ),
    (r'mysql_', ),
    (r'on MySQL result index', ),
    (r'You have an error in your SQL syntax;', ),
    (r'You have an error in your SQL syntax near', ),
    (r'MySQL server version for the right syntax to use', ),
    (r'\[MySQL\]\[ODBC', ),
    (r"Column count doesn't match", ),
    (r"the used select statements have different number of columns",),
    (r"Table '[^']+' doesn't exist", ),
    (r"DBD::mysql::st execute failed", ),
    (r"DBD::mysql::db do failed:", ),
    # Informix
    (r'com\.informix\.jdbc', ),
    (r'Dynamic Page Generation Error:', ),
    (r'An illegal character has been found in the statement',),
    (r'\[Informix\]', ),
    (r'<b>Warning</b>:  ibase_', ),
    (r'Dynamic SQL Error', ),
    # DML
    (r'\[DM_QUERY_E_SYNTAX\]', ),
    (r'has occurred in the vicinity of:', ),
    (r'A Parser Error \(syntax error\)', ),
    # Java
    (r'java\.sql\.SQLException', ),
    (r'Unexpected end of command in statement', ),
    # Coldfusion
    (r'\[Macromedia\]\[SQLServer JDBC Driver\]', ),
    # Generic errors..
    (r'SELECT .*? FROM .*?', ),
    (r'UPDATE .*? SET .*?', ),
    (r'INSERT INTO .*?', ),
    (r'Unknown column', ),
    (r'where clause', ),
    (r'SqlServer', )
)
