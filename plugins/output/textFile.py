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
from core.controllers.w3afException import w3afFileException
import sys, os
import time
import codecs
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

# severity constants for vuln messages
import core.data.constants.severity as severity

class textFile(baseOutputPlugin):
    '''
    Prints all messages to a text file.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # User configured parameters
        self._fileName = 'output.txt'
        self._httpFileName = 'output-http.txt'
        # I changed this to false because the performance is enhanced A LOT
        # Show Caller False: Performed 4001 requests in 10 seconds (400.100000 req/sec)
        # Show Caller True: Performed 4001 requests in 28 seconds (142.892857 req/sec)
        self._showCaller = False
        self.verbose = True
        
        # Internal variables
        self._flushCounter = 0
        self._flushNumber = 10
        self._initialized = False
        self._file = None

    
    def _init( self ):
        self._initialized = True
        try:
            #self._file = codecs.open( self._fileName, "w", "utf-8", 'replace' )
            self._file = open( self._fileName, "w")
        except Exception, e:
            raise w3afException('Cant open report file ' + self._httpFileName + ' for output. Exception: ' + str(e) )
            
        try:
            # Images aren't ascii, so this file that logs every request/response, will be binary
            #self._http = codecs.open( self._httpFileName, "wb", "utf-8", 'replace' )
            self._http = open( self._httpFileName, "wb" )
        except Exception, e:
            raise w3afException('Cant open HTTP log file ' + self._httpFileName + ' for output. Exception: ' + str(e) )
        
    def __del__(self):
        if self._file != None:
            self._file.close()
    
    def _writeToFile( self, msg ):
        try:
            self._file.write( self._cleanString(msg) )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def _writeToHTTPLog( self, msg ):
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
            toPrint = message
            
            now = time.localtime(time.time())
            theTime = time.strftime("%c", now)
            if self._showCaller:
                timestamp = '[ ' + theTime + ' - debug - '+self.getCaller()+' ] '
            else:
                timestamp = '[ ' + theTime + ' - debug ] '
            
            toPrint = timestamp + toPrint
            toPrint = toPrint.replace('\n', '\n'+timestamp)
            if newLine == True:
                toPrint += '\n'
            
            self._writeToFile( toPrint )
            self._flush()

    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        '''
        if not self._initialized:
            self._init()
            
        toPrint = message
    
        now = time.localtime(time.time())
        theTime = time.strftime("%c", now)
        if self._showCaller:
            timestamp = '[ ' + theTime + ' - information - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + theTime + ' - information ] '
        
        toPrint = timestamp + toPrint
        toPrint = toPrint.replace('\n', '\n'+timestamp)
        
        if newLine == True:
            toPrint += '\n'
            
        self._writeToFile( toPrint )

        self._flush()


    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        if not self._initialized:
            self._init()
        
        toPrint = message
        if newLine == True:
            toPrint += '\n'
        
        now = time.localtime(time.time())
        theTime = time.strftime("%c", now)
        if self._showCaller:
            timestamp = '[ ' + theTime + ' - error - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + theTime + ' - error ] '
            
        self._writeToFile( timestamp + toPrint )

        self._flush()

    def vulnerability(self, message , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        if not self._initialized:
            self._init()
        
        toPrint = message
        if newLine == True:
            toPrint += '\n'
        now = time.localtime(time.time())
        theTime = time.strftime("%c", now)
        if self._showCaller:
            timestamp = '[ ' + theTime + ' - vulnerability - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + theTime + ' - vulnerability ] '
        self._writeToFile( timestamp + toPrint )

        self._flush()
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        if not self._initialized:
            self._init()
        toPrint = message
        if newLine == True:
            toPrint += '\n'
        now = time.localtime(time.time())
        theTime = time.strftime("%c", now)
        
        if self._showCaller:
            timestamp = '[ ' + theTime + ' - console - '+self.getCaller()+' ] '
        else:
            timestamp = '[ ' + theTime + ' - console ] '
            
        self._writeToFile( timestamp + toPrint )
        self._flush()
        
    def _flush(self):
        '''
        textfile.flush is called every time a message is sent to this plugin.
        self._file.flush() is called every self._flushNumber
        '''
        if self._flushCounter % self._flushNumber == 0:
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
        self._fileName = OptionList['fileName'].getValue()
        self._httpFileName = OptionList['httpFileName'].getValue()
        self._showCaller = OptionList['showCaller'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Enable if verbose output is needed'
        o1 = option('verbose', self.verbose, d1, 'boolean')
        
        d2 = 'File name where this plugin will write to'
        o2 = option('fileName', self._fileName, d2, 'string')
        
        d3 = 'File name where this plugin will write HTTP requests and responses'
        o3 = option('httpFileName', self._httpFileName, d3, 'string')
        
        d4 = 'Enables a slightly more verbose output that shows who called the output manager'
        o4 = option('showCaller', self._showCaller, d4, 'boolean')
        
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
        theTime = time.strftime("%c", now)
        
        msg = '='*40  + 'Request ' + str(response.id) + ' - '+ theTime+'='*40 + '\n'
        self._writeToHTTPLog(  msg )
        self._writeToHTTPLog( request.dump() )
        msg2 = '\n' + '='*40  + 'Response ' + str(response.id) + ' - '+ theTime+'='*39 + '\n'
        self._writeToHTTPLog( msg2 )
        self._writeToHTTPLog( response.dump() )
        
        self._writeToHTTPLog( '\n' + '='*(len(msg)-1) + '\n')
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
