'''
console.py

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


from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
import sys

class console(baseOutputPlugin):
    '''
    Print messages to the console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        self.verbosity = 0

    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        if int( self.verbosity ) > 5:
            toPrint = str ( message )
            if newLine == True:
                toPrint += '\r\n'
            sys.stdout.write( toPrint )
            sys.stdout.flush()

    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        ''' 
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( toPrint )
        sys.stdout.flush()


    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stderr.write( toPrint )
        sys.stdout.flush()

    def vulnerability(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( toPrint )
        sys.stdout.flush()
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        toPrint = str( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( toPrint )
        sys.stdout.flush()

    def logHttp( self, request, response):
        pass

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to the console.
        '''
