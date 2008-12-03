'''
sqli.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.controllers.w3afException import w3afException
import core.data.constants.dbms as dbms

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

import re


class sqli(baseAuditPlugin):
    '''
    Find SQL injection bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def audit(self, freq ):
        '''
        Tests an URL for SQL injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'SQLi plugin is testing: ' + freq.getURL() )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        sqli_strings = self._get_sqli_strings()
        mutants = createMutants( freq , sqli_strings, oResponse=oResponse )
        
        for mutant in mutants:
            if self._hasNoBug( 'sqli' , 'sqli' , mutant.getURL() , mutant.getVar() ):
                # Only spawn a thread if the mutant has a modified variable
                # that has no reported bugs in the kb
                targs = (mutant,)
                self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
        
            
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method.
        '''
        sql_error_list = self._findsql_error( response )
        for sql_error in sql_error_list:
            if not re.search( sql_error[0], mutant.getOriginalResponseBody(), re.IGNORECASE ):
                # Create the vuln,
                v = vuln.vuln( mutant )
                v.setId( response.id )
                v.setName( 'SQL injection vulnerability' )
                v.setSeverity(severity.HIGH)
                v['error'] = sql_error[0]
                v['db'] = sql_error[1]
                v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'sqli', v )
                break
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'sqli', 'sqli' ), 'VAR' )
    
    def _get_sqli_strings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all SQLi strings to test. Example: [ '\'','\'\'']
        '''
        sqli_strings = []
        sqli_strings.append("d'z\"0")
        return sqli_strings

    def _findsql_error( self, response ):
        '''
        This method searches for SQL errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for sql_error in self._get_SQL_errors():
            match = re.search( sql_error[0] , response.getBody() , re.IGNORECASE )
            if  match:
                msg = 'A SQL error was found in the response supplied by the web application,'
                msg += ' the error is (only a fragment is shown): "' 
                msg += response.getBody()[match.start():match.end()]  + '". The error was found '
                msg += 'on response with id ' + str(response.id) + '.'
                om.out.information( msg )
                res.append( sql_error )
        return res

    def _get_SQL_errors(self):
        errors = []
        
        # ASP / MSSQL
        errors.append( ('System\.Data\.OleDb\.OleDbException', dbms.MSSQL ) )
        errors.append( ('\\[IBM\\]\\[CLI Driver\\]\\[DB2', dbms.DB2 ) )
        errors.append( ('\\[SQL Server\\]', dbms.MSSQL ) )
        errors.append( ('\\[Microsoft\\]\\[ODBC SQL Server Driver\\]', dbms.MSSQL ) )
        errors.append( ('\\[SQLServer JDBC Driver\\]', dbms.MSSQL ) )
        errors.append( ('\\[SqlException', dbms.MSSQL ) )
        errors.append( ('System.Data.SqlClient.SqlException', dbms.MSSQL ) )
        errors.append( ('Unclosed quotation mark after the character string', dbms.MSSQL ) )
        errors.append( ("'80040e14'", dbms.MSSQL ) )
        errors.append( ('mssql_query\\(\\)', dbms.MSSQL ) )
        errors.append( ('odbc_exec\\(\\)', dbms.MSSQL ) )
        errors.append( ('Microsoft OLE DB Provider for ODBC Drivers', dbms.MSSQL ))
        errors.append( ('Microsoft OLE DB Provider for SQL Server', dbms.MSSQL ))
        errors.append( ('Incorrect syntax near', dbms.MSSQL ) )
        errors.append( ('Syntax error in string in query expression', dbms.MSSQL ) )
        errors.append( ('ADODB\\.Field \\(0x800A0BCD\\)<br>', dbms.MSSQL ) )
        errors.append( ("Procedure '[^']+' requires parameter '[^']+'", dbms.MSSQL ))
        
        # Access
        errors.append( ('Syntax error in query expression', dbms.ACCESS ))
        errors.append( ('Data type mismatch in criteria expression.', dbms.ACCESS ))
        errors.append( ('Microsoft JET Database Engine', dbms.ACCESS ))
        errors.append( ('\\[Microsoft\\]\\[ODBC Microsoft Access Driver\\]', dbms.ACCESS ) )
        
        # ORACLE
        errors.append( ('(PLS|ORA)-[0-9][0-9][0-9][0-9]', dbms.ORACLE ) )
        
        # POSTGRE
        errors.append( ('PostgreSQL query failed:', dbms.POSTGRE ) )
        errors.append( ('supplied argument is not a valid PostgreSQL result', dbms.POSTGRE ) )
        errors.append( ('pg_query\\(\\) \\[:', dbms.POSTGRE ) )
        errors.append( ('pg_exec\\(\\) \\[:', dbms.POSTGRE ) )
        
        # MYSQL
        errors.append( ('supplied argument is not a valid MySQL', dbms.MYSQL ) )
        errors.append( ('mysql_fetch_array\\(\\)', dbms.MYSQL ) )
        errors.append( ('mysql_', dbms.MYSQL ) )
        errors.append( ('on MySQL result index', dbms.MYSQL ) )
        errors.append( ('You have an error in your SQL syntax;', dbms.MYSQL ) )
        errors.append( ('You have an error in your SQL syntax near', dbms.MYSQL ) )
        errors.append( ('MySQL server version for the right syntax to use', dbms.MYSQL ) )
        errors.append( ('\\[MySQL\\]\\[ODBC', dbms.MYSQL ))
        errors.append( ("Column count doesn't match", dbms.MYSQL ))
        errors.append( ("the used select statements have different number of columns", dbms.MYSQL ))
        errors.append( ("Table '[^']+' doesn't exist", dbms.MYSQL ))

        
        # Informix
        errors.append( ('com\\.informix\\.jdbc', dbms.INFORMIX ))
        errors.append( ('Dynamic Page Generation Error:', dbms.INFORMIX ))
        errors.append( ('<b>Warning</b>:  ibase_', dbms.INTERBASE ))
        
        # DML
        errors.append( ('\\[DM_QUERY_E_SYNTAX\\]', dbms.DMLDATABASE ))
        errors.append( ('has occurred in the vicinity of:', dbms.DMLDATABASE ))
        errors.append( ('A Parser Error \\(syntax error\\)', dbms.DMLDATABASE ))
        
        # Java
        errors.append( ('java\\.sql\\.SQLException', dbms.JAVA ))

        # Coldfusion
        errors.append( ('\\[Macromedia\\]\\[SQLServer JDBC Driver\\]', dbms.MSSQL ))
        
        # Generic errors..
        errors.append( ('SELECT .*? FROM .*?', dbms.UNKNOWN ))
        errors.append( ('UPDATE .*? SET .*?', dbms.UNKNOWN ))
        errors.append( ('INSERT INTO .*?', dbms.UNKNOWN ))
        
        return errors
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['grep.error500']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds SQL injections. To find this vulnerabilities the plugin sends the string d'z"0 to every
        injection point, and searches for SQL errors in the response body.
        '''
