# -*- coding: latin-1 -*-
'''
webOutput.py

Copyright 2007 Mariano Nuñez Di Croce @ CYBSEC

This file is part of sapyto, http://www.cybsec.com/EN/research/tools/sapyto.php

sapyto is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

sapyto is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with sapyto; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
import sys

class webOutput(baseOutputPlugin):
    '''
    Print all messages to the web user interface.
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        self.verbosity = 0

        # Initialize cache
        self._msgCache = []

    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
    
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\n'
        self._msgCache.append( ('debug', toPrint) )

    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        ''' 
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\n'
        self._msgCache.append( ('info', toPrint) )


    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\n'
        self._msgCache.append( ('error', toPrint) )

    def vulnerability(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        toPrint = str ( message )
        if newLine == True:
            toPrint += '\n'
        self._msgCache.append( ('vuln', toPrint) )
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the sapyto console to print messages to the outside.
        '''
        pass

    def logHttp( self, request, response):
        pass
    
    def getMessageCache(self, debug=False ):
        '''
        This method retrieves message cache and clears it afterwards
        '''
        if debug:
            res = [ x[1] for x in self._msgCache ]
        else:
            res = [ x[1] for x in self._msgCache if x[0] != 'debug' ]
            
        # empty the cache.
        self._msgCache = []
        return res

    def end( self ):
        '''
        This method is called when the plugin won't be used anymore.
        Best case scenario this is because the start() method of w3afCore finished it's work.
        Other cases are errors or Ctrl+C hitted in the console by the user.
        '''
        self.information('w3af has finished it\'s work.')
        
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to a cache, where the webUI can then read the data
        to show to the user in the client browser. This plugin is the "glue" that joins w3af and the client browser.
        You should only enable it if you are running a webUI or testing something wierd. 
        
        Note: When you run w3af with the "-w" flag ( web ), this plugin is auto-enabled.
        '''
