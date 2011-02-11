'''
dbDriver.py

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
from core.controllers.w3afException import w3afException
from plugins.attack.db.dbDriverFunctions import dbDriverFunctions
from core.controllers.basePlugin.basePlugin import basePlugin
from plugins.attack.db.dump import SQLMapDump
from core.data.fuzzer.fuzzer import *


class dbDriver(dbDriverFunctions, basePlugin):
    '''
    This represents a database driver. This class is an "interface" between w3af and sqlmap.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, urlOpener, cmpFunction, vuln):
        dbDriverFunctions.__init__(self, cmpFunction)
        # Params initialization
        self.args.injectionMethod = vuln['type']
        self.args.injParameter = vuln.getVar()
        self.args.httpMethod = vuln.getMethod()
        
        self._urlOpener = urlOpener
        self._vuln = vuln
        
        mutant = vuln.getMutant()
        url = mutant.getURI()       
        if vuln.getMethod() == 'POST':
            url += '?' + str(vuln.getMutant().getData())
        self.args.trueResult = vuln['trueHtml']
        
        falseValue = self._findFalseValue( vuln )
        self._vuln['falseValue'] = falseValue
        
        # "pretty" prints output
        self.dump = SQLMapDump()
    
    def auxGetTables( self, db=None ):
        self.args.db = db
        # Now I call the sqlmap function
        return self.getTables()
    
    def auxGetColumns( self, tbl , db=None):
        self.args.tbl = tbl
        self.args.db = db
        
        # Now I call the sqlmap function
        return self.getColumns()
        
    def auxDump( self, tbl , db=None, col=None):
        self.args.tbl = tbl
        self.args.db = db
        self.args.col = col
        
        # Now I call the sqlmap function
        return self.dumpTable()
        
    def _findFalseValue( self, vuln ):
        '''
        Find a value that returns a false response for the sql injection. 
        For example:
            http://a/a.php?id=1
        and
            http://a/a.php?id=1 OR 1=1
        both return the same response, so the false value i'm looking for is any value that returns
        something different than http://a/a.php?id=1 , for example, '2' .
        '''
        found = False
        for i in xrange(3):
            
            if vuln['type'] == 'numeric':
                possibleFalse = createRandNum(4)
            elif vuln['type'] in ['stringsingle','stringdouble']:
                possibleFalse = createRandAlpha(5)
            
            mutant = vuln.getMutant()
            mutant.setModValue( possibleFalse )
            
            res = self._sendMutant( mutant, analyze=False )
            if res.getBody() != vuln['trueHtml']:
                return possibleFalse
            
        if not found:
            raise w3afException('Failed to find a false value for the injection.')

    def getTables(self):
        '''
        To be implemented by subclasses.
        '''
        pass
    
    def getColumns(self):
        '''
        To be implemented by subclasses.
        '''        
        pass
    
    def dumpTable(self):
        '''
        To be implemented by subclasses.
        '''
        pass
