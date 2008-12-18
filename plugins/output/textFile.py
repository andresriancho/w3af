'''
textFile.py

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
from core.controllers.w3afException import w3afException

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

# severity constants for vuln messages
import core.data.constants.severity as severity

import sys
import time


class textFile(baseOutputPlugin):
    '''
    Prints all messages to a text file.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # User configured parameters
        self._file_name = 'output.txt'
        self._http_file_name = 'output-http.txt'
        # I changed this to false because the performance is enhanced A LOT
        # Show Caller False: Performed 4001 requests in 10 seconds (400.100000 req/sec)
        # Show Caller True: Performed 4001 requests in 28 seconds (142.892857 req/sec)
        self._show_caller = False
        self.verbose = True
        
        # Internal variables
        self._flush_counter = 0
        self._flush_number = 10
        self._initialized = False
        # File handlers
        self._file = None
        self._http = None

    
    def _init( self ):
        self._initialized = True
        try:
            #self._file = codecs.open( self._file_name, "w", "utf-8", 'replace' )
            self._file = open( self._file_name, "w")
        except Exception, e:
            msg = 'Cant open report file "' + self._http_file_name + '" for output. Exception: "'
            msg += str(e) + '".'
            raise w3afException( msg )
            
        try:
            # Images aren't ascii, so this file that logs every request/response, will be binary
            #self._http = codecs.open( self._http_file_name, "wb", "utf-8", 'replace' )
            self._http = open( self._http_file_name, "wb" )
        except Exception, e:
            msg = 'Cant open report file "' + self._http_file_name + '" for output. Exception: "'
            msg += str(e) + '".'
            raise w3afException( msg )
        
    def __del__(self):
        if self._file != None:
            self._file.close()
    
    def _write_to_file( self, msg ):
        try:
            self._file.write( self._cleanString(msg) )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def _write_to_HTTP_log( self, msg ):
        try:
            self._http.write( msg )
        except Exception, e:
            print 'An exception was raised while trying to write to the HTTP log output file:', e
            sys.exit(1)
            
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        if not self._initialized:
            self._init()
            
        if self.verbose:
            to_print = message
            
            now = time.localtime(time.time())
            the_time = time.strftime("%c", now)
            if self._show_caller:
                timestamp = '[ ' + the_time + ' - debug - '+self.getCaller()+' ] '
            else:
                timestamp = '[ ' + the_time + ' - debug ] '
            
            to_print = timestamp + to_print
            to_print = to_print.replace('\n', '\n'+timestamp)
            if newLine == True:
                to_print += '\n'
            
            self._write_to_file( to_print )
            self._flush()

    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        '''
        if not self._initialized:
            self._init()
            
        to_print = message
    
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        if self._show_caller:
            timestamp = '[ ' + the_time + ' - information - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + the_time + ' - information ] '
        
        to_print = timestamp + to_print
        to_print = to_print.replace('\n', '\n'+timestamp)
        
        if newLine == True:
            to_print += '\n'
            
        self._write_to_file( to_print )

        self._flush()


    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        if not self._initialized:
            self._init()
        
        to_print = message
        if newLine == True:
            to_print += '\n'
        
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        if self._show_caller:
            timestamp = '[ ' + the_time + ' - error - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + the_time + ' - error ] '
            
        self._write_to_file( timestamp + to_print )

        self._flush()

    def vulnerability(self, message , newLine=True, msg_severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        if not self._initialized:
            self._init()
        
        to_print = message
        if newLine == True:
            to_print += '\n'
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        if self._show_caller:
            timestamp = '[ ' + the_time + ' - vulnerability - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + the_time + ' - vulnerability ] '
        self._write_to_file( timestamp + to_print )

        self._flush()
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        if not self._initialized:
            self._init()
        to_print = message
        if newLine == True:
            to_print += '\n'
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        
        if self._show_caller:
            timestamp = '[ ' + the_time + ' - console - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + the_time + ' - console ] '
            
        self._write_to_file( timestamp + to_print )
        self._flush()
        
    def logEnabledPlugins(self,  enabledPluginsDict,  pluginOptionsDict):
        '''
        This method is called from the output managerobject. 
        This method should take an action for the enabled plugins 
        and their configuration.
        '''
        pass
        
    def _flush(self):
        '''
        textfile.flush is called every time a message is sent to this plugin.
        self._file.flush() is called every self._flush_number
        '''
        if self._flush_counter % self._flush_number == 0:
            self._file.flush()
            
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self.verbose = OptionList['verbose'].getValue()
        self._file_name = OptionList['fileName'].getValue()
        self._http_file_name = OptionList['httpFileName'].getValue()
        self._show_caller = OptionList['showCaller'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Enable if verbose output is needed'
        o1 = option('verbose', self.verbose, d1, 'boolean')
        
        d2 = 'File name where this plugin will write to'
        o2 = option('fileName', self._file_name, d2, 'string')
        
        d3 = 'File name where this plugin will write HTTP requests and responses'
        o3 = option('httpFileName', self._http_file_name, d3, 'string')
        
        d4 = 'Enables a slightly more verbose output that shows who called the output manager'
        o4 = option('showCaller', self._show_caller, d4, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol

    def logHttp( self, request, response):
        '''
        log the http req / res to file.
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        
        msg = '='*40  + 'Request ' + str(response.id) + ' - '+ the_time+'='*40 + '\n'
        self._write_to_HTTP_log(  msg )
        self._write_to_HTTP_log( request.dump() )
        msg2 = '\n' + '='*40  + 'Response ' + str(response.id) + ' - '+ the_time+'='*39 + '\n'
        self._write_to_HTTP_log( msg2 )
        self._write_to_HTTP_log( response.dump() )
        
        self._write_to_HTTP_log( '\n' + '='*(len(msg)-1) + '\n')
        self._http.flush()

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to a text file.
        
        Four configurable parameters exist:
            - fileName
            - httpFileName
            - verbose
            - showCaller
        '''
