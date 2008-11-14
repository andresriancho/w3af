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

from core.data.fuzzer.fuzzer import createMutants
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
import re
import core.data.constants.severity as severity

# We define some constants
DB2 = 'IBM DB2 database'
MSSQL = 'Microsoft SQL database'
ORACLE = 'Oracle database'
SYBASE = 'Sybase database'
POSTGRE = 'PostgreSQL database'
MYSQL = 'MySQL database'
JAVA = 'Java connector'
ACCESS = 'Microsoft Access database'
INFORMIX = 'Informix database'
INTERBASE = 'Interbase database'
DMLDATABASE = 'DML Language database'
UNKNOWN = 'Unknown database'

class sqli(baseAuditPlugin):
    '''
    Find SQL injection bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)

    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for SQL injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'SQLi plugin is testing: ' + freq.getURL() )
        
        oResponse = self._sendMutant( freq , analyze=False ).getBody()
        sqliStrings = self._getSQLiStrings()
        mutants = createMutants( freq , sqliStrings, oResponse=oResponse )
        
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
        sqlErrorList = self._findSqlError( response )
        for sqlError in sqlErrorList:
            if not re.search( sqlError[0], mutant.getOriginalResponseBody(), re.IGNORECASE ):
                # Create the vuln,
                v = vuln.vuln( mutant )
                v.setId( response.id )
                v.setName( 'SQL injection vulnerability' )
                v.setSeverity(severity.HIGH)
                v['error'] = sqlError[0]
                v['db'] = sqlError[1]
                v.setDesc( 'SQL injection in a '+ v['db'] +' was found at: ' + mutant.foundAt() )
                kb.kb.append( self, 'sqli', v )
                break
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'sqli', 'sqli' ), 'VAR' )
    
    def _getSQLiStrings( self ):
        '''
        Gets a list of strings to test against the web app.
        
        @return: A list with all SQLi strings to test. Example: [ '\'','\'\'']
        '''
        sqliStrings = []
        sqliStrings.append("d'z\"0")
        return sqliStrings

    def _findSqlError( self, response ):
        '''
        This method searches for SQL errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        for sqlError in self._getSqlErrors():
            match = re.search( sqlError[0] , response.getBody() , re.IGNORECASE )
            if  match:
                om.out.information('A SQL error was found in the response supplied by the web application, the error is (only a fragment is shown): "' + response.getBody()[match.start():match.end()]  + '". The error was found on response with id ' + str(response.id) + '.' )
                res.append( sqlError )
        return res

    def _getSqlErrors(self):
        errors = []
        
        # ASP / MSSQL
        errors.append( ('System\.Data\.OleDb\.OleDbException', MSSQL ) )
        errors.append( ('\\[IBM\\]\\[CLI Driver\\]\\[DB2', DB2 ) )
        errors.append( ('\\[SQL Server\\]', MSSQL ) )
        errors.append( ('\\[Microsoft\\]\\[ODBC SQL Server Driver\\]', MSSQL ) )
        errors.append( ('\\[SQLServer JDBC Driver\\]', MSSQL ) )
        errors.append( ('\\[SqlException', MSSQL ) )
        errors.append( ('System.Data.SqlClient.SqlException', MSSQL ) )
        errors.append( ('Unclosed quotation mark after the character string', MSSQL ) )
        errors.append( ("'80040e14'", MSSQL ) )
        errors.append( ('mssql_query\\(\\)', MSSQL ) )
        errors.append( ('odbc_exec\\(\\)', MSSQL ) )
        errors.append( ('Microsoft OLE DB Provider for ODBC Drivers', MSSQL ))
        errors.append( ('Microsoft OLE DB Provider for SQL Server', MSSQL ))
        errors.append( ('Incorrect syntax near', MSSQL ) )
        errors.append( ('Syntax error in string in query expression', MSSQL ) )
        errors.append( ('ADODB\\.Field \\(0x800A0BCD\\)<br>', MSSQL ) )
        errors.append( ("Procedure '[^']+' requires parameter '[^']+'", MSSQL ))
        
        # Access
        errors.append( ('Syntax error in query expression', ACCESS ))
        errors.append( ('Data type mismatch in criteria expression.', ACCESS ))
        errors.append( ('Microsoft JET Database Engine', ACCESS ))
        errors.append( ('\\[Microsoft\\]\\[ODBC Microsoft Access Driver\\]', ACCESS ) )
        
        # ORACLE
        errors.append( ('(PLS|ORA)-[0-9][0-9][0-9][0-9]', ORACLE ) )
        
        # POSTGRE
        errors.append( ('PostgreSQL query failed:', POSTGRE ) )
        errors.append( ('supplied argument is not a valid PostgreSQL result', POSTGRE ) )
        errors.append( ('pg_query\\(\\) \\[:', POSTGRE ) )
        errors.append( ('pg_exec\\(\\) \\[:', POSTGRE ) )
        
        # MYSQL
        errors.append( ('supplied argument is not a valid MySQL', MYSQL ) )
        errors.append( ('mysql_fetch_array\\(\\)', MYSQL ) )
        errors.append( ('mysql_', MYSQL ) )
        errors.append( ('on MySQL result index', MYSQL ) )
        errors.append( ('You have an error in your SQL syntax;', MYSQL ) )
        errors.append( ('You have an error in your SQL syntax near', MYSQL ) )
        errors.append( ('MySQL server version for the right syntax to use', MYSQL ) )
        errors.append( ('\\[MySQL\\]\\[ODBC', MYSQL ))
        errors.append( ("Column count doesn't match", MYSQL ))
        errors.append( ("the used select statements have different number of columns", MYSQL ))
        errors.append( ("Table '[^']+' doesn't exist", MYSQL ))

        
        # Informix
        errors.append( ('com\\.informix\\.jdbc', INFORMIX ))
        errors.append( ('Dynamic Page Generation Error:', INFORMIX ))
        errors.append( ('<b>Warning</b>:  ibase_', INTERBASE ))
        
        # DML
        errors.append( ('\\[DM_QUERY_E_SYNTAX\\]', DMLDATABASE ))
        errors.append( ('has occurred in the vicinity of:', DMLDATABASE ))
        errors.append( ('A Parser Error \\(syntax error\\)', DMLDATABASE ))
        
        # Java
        errors.append( ('java\\.sql\\.SQLException', JAVA ))

        # Coldfusion
        errors.append( ('\\[Macromedia\\]\\[SQLServer JDBC Driver\\]', MSSQL ))
        
        # Generic errors..
        errors.append( ('SELECT .*? FROM .*?', UNKNOWN ))
        errors.append( ('UPDATE .*? SET .*?', UNKNOWN ))
        errors.append( ('INSERT INTO .*?', UNKNOWN ))
        
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
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds SQL injections. To find this vulnerabilities the plugin sends the string d'z"0 to every
        injection point, and searches for SQL errors in the response body.
        '''
