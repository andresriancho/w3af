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

import string
import sys

from errno import ENOSPC

import core.data.constants.severity as severity

from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.w3afException import w3afMustStopByKnownReasonExc
from core.data.options.option import option
from core.data.options.optionList import optionList

def catch_ioerror(meth):
    '''
    Function to decorate methods in order to catch IOError exceptions.
    '''
    def wrapper(self, *args, **kwargs):
        try:
            return meth(self, *args, **kwargs)
        except IOError as (errno, strerror):
            if errno == ENOSPC:
                msg = 'No space left on device'
                raise w3afMustStopByKnownReasonExc( msg )

    return wrapper

class console(baseOutputPlugin):
    '''
    Print messages to the console.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # User configured setting
        self.verbose = False

    def _make_printable(self, a_string):
        a_string = str( a_string )
        return ''.join(ch for ch in a_string if ch in string.printable)

    def _print_to_stdout(self, message, newline):
        to_print = self._make_printable( message )
        if newline:
            to_print += '\r\n'
        sys.stdout.write( to_print )
        sys.stdout.flush()
        
    @catch_ioerror
    def debug(self, message, newLine=True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for debug messages.
        '''
        if self.verbose:
            self._print_to_stdout(message, newLine)
            
    @catch_ioerror
    def _generic(self, message , newLine=True, severity=None ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for all messages except from debug ones.
        ''' 
        self._print_to_stdout(message, newLine)
        
    error = console = vulnerability = information = _generic

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to the console.
        
        One configurable parameter exists:
            - verbose
        '''

    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed 
        using the XML Options that was retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self.verbose = OptionList['verbose'].getValue()

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        d = 'Enables verbose output for the console'
        o = option('verbose', self.verbose, d, 'boolean')
        ol.add(o)
        
        return ol
