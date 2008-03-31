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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

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
            toPrint = unicode ( message )
            if newLine == True:
                toPrint += '\r\n'
            sys.stdout.write( self._cleanString(toPrint) )
            sys.stdout.flush()

    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        ''' 
        toPrint = unicode ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( self._cleanString(toPrint) )
        sys.stdout.flush()


    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        toPrint = unicode ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stderr.write( self._cleanString(toPrint) )
        sys.stdout.flush()

    def vulnerability(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        toPrint = unicode ( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( self._cleanString(toPrint) )
        sys.stdout.flush()
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        toPrint = unicode( message )
        if newLine == True:
            toPrint += '\r\n'
        sys.stdout.write( self._cleanString(toPrint) )
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

    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self.verbosity = OptionList['verbosity']

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Verbosity level for this plugin.'
        o1 = option('verbosity', self.verbosity, d1, 'integer')
        
        ol = optionList()
        ol.add(o1)
        return ol
