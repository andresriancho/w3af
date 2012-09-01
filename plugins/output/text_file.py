'''
text_file.py

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
import sys
import time
import os

import core.data.kb.config as cf
import core.data.constants.severity as severity

from core.controllers.plugins.output_plugin import OutputPlugin
from core.controllers.w3afException import w3afException
from core.data.options.option import option
from core.data.options.option_list import OptionList


class text_file(OutputPlugin):
    '''
    Prints all messages to a text file.
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    def __init__(self):
        OutputPlugin.__init__(self)
        
        # User configured parameters
        self._file_name = 'output.txt'
        self._http_file_name = 'output-http.txt'
        self.verbose = True
        
        # Internal variables
        self._flush_counter = 0
        self._flush_number = 10
        self._initialized = False
        # File handlers
        self._file = None
        self._http = None
        # XXX Only set '_show_caller' to True for debugging purposes. It
        # causes the execution of potentially slow code that handles
        # with introspection. 
        self._show_caller = False

    def _init( self ):
        self._initialized = True
        try:
            #self._file = codecs.open( self._file_name, "w", "utf-8", 'replace' )
            self._file = open( self._file_name, "w")
        except IOError, io:
            msg = 'Can\'t open report file "' + os.path.abspath(self._file_name) + '" for writing'
            msg += ': "' + io.strerror + '".'
            raise w3afException( msg )
        except Exception, e:
            msg = 'Can\'t open report file "' + self._file_name + '" for writing. Exception: "'
            msg += str(e) + '".'
            raise w3afException( msg )
            
        try:
            # Images aren't ascii, so this file that logs every request/response, will be binary
            #self._http = codecs.open( self._http_file_name, "wb", "utf-8", 'replace' )
            self._http = open( self._http_file_name, "wb" )
        except IOError, io:
            msg = 'Can\'t open report file "' + os.path.abspath(self._http_file_name) + '" for writing'
            msg += ': "' + io.strerror + '".'
            raise w3afException( msg )
        except Exception, e:
            msg = 'Can\'t open report file "' + self._http_file_name + '" for writing. Exception: "'
            msg += str(e) + '".'
            raise w3afException( msg )
        
    def __del__(self):
        if self._file is not None:
            self._file.close()
    
    def _write_to_file( self, msg ):
        '''
        Write to the log file.
        
        @parameter msg: The text to write.
        '''
        try:
            self._file.write( self._clean_string(msg) )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def _write_to_HTTP_log( self, msg ):
        '''
        Write to the HTTP log file.
        
        @parameter msg: The text to write (a string representation of the HTTP
                        request and response)
        '''
        try:
            self._http.write(msg)
        except Exception, e:
            print 'An exception was raised while trying to write to the HTTP'
            ' log output file:', e
            sys.exit(1)
            
    def write(self, message, log_type, newLine = True ):
        '''
        Method that writes stuff to the text_file.
        
        @param message: The message to write to the file
        @param log_type: Type of message are we writing to the file
        @param newLine: Add a new line after the message
        '''
        if not self._initialized:
            self._init()
        
        to_print = str(message)
        if newLine == True:
            to_print += '\n'
        
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        
        if self._show_caller:
            timestamp = '[%s - %s - %s] ' % (the_time, log_type, self.getCaller())
        else:
            timestamp = '[%s - %s] ' % (the_time, log_type)
            
        self._write_to_file( timestamp + to_print )

        self._flush()
    
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.
        '''
        if self.verbose:
            self.write( message, 'debug', newLine)
            
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for informational messages.
        '''
        self.write( message, 'information', newLine)

    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        '''
        self.write( message, 'error', newLine)     

    def vulnerability(self, message , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was 
        called from a plugin or from the framework. This method should take an
        action when a vulnerability is found.
        '''
        self.write( message, 'vulnerability', newLine)
        
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        self.write( message, 'console', newLine)
        
    def log_enabled_plugins(self,  plugins_dict,  options_dict):
        '''
        This method is called from the output manager object. This method should
        take an action for the enabled plugins and their configuration. Usually,
        write the info to a file or print it somewhere.
        
        @parameter pluginsDict: A dict with all the plugin types and the enabled
                                plugins for that type of plugin.
        @parameter optionsDict: A dict with the options for every plugin.
        '''
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        timestamp = '[ ' + the_time + ' - Enabled plugins ] '
        
        to_print = ''
        
        for plugin_type in plugins_dict:
            to_print += self._create_plugin_info( plugin_type, 
                                                  plugins_dict[plugin_type], 
                                                  options_dict[plugin_type])
        
        # And now the target information
        str_targets = ', '.join( [u.url_string for u in cf.cf.get('targets')] )
        to_print += 'target\n'
        to_print += '    set target ' + str_targets + '\n'
        to_print += '    back'
        
        to_print = to_print.replace('\n', '\n' + timestamp ) + '\n'
        
        self._write_to_file( timestamp + to_print )
    
    def _flush(self):
        '''
        textfile.flush is called every time a message is sent to this plugin.
        self._file.flush() is called every self._flush_number
        '''
        if self._flush_counter % self._flush_number == 0:
            #   TODO: Remove this if I discover that it wasn't really needed.
            #   I just commented this because after some profiling I found that
            #   the file flushing takes some considerable time that I want to use for
            #   some other more interesting things :)
            #
            #self._file.flush()
            pass
            
    def set_options( self, option_list ):
        '''
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed 
        using the XML Options that was retrieved from the plugin using
        get_options()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self.verbose = option_list['verbose'].getValue()
        self._file_name = option_list['fileName'].getValue()
        self._http_file_name = option_list['httpFileName'].getValue()
        
        self._init()
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        
        d = 'Enable if verbose output is needed'
        o = option('verbose', self.verbose, d, 'boolean')
        ol.add(o)
        
        d = 'File name where this plugin will write to'
        o = option('fileName', self._file_name, d, 'string')
        ol.add(o)
        
        d = 'File name where this plugin will write HTTP requests and responses'
        o = option('httpFileName', self._http_file_name, d, 'string')
        ol.add(o)
        
        return ol

    def logHttp(self, request, response):
        '''
        log the http req / res to file.
        @parameter request: A fuzzable request object
        @parameter response: A httpResponse object
        '''
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        
        msg = '=' * 40 + 'Request ' + str(response.id) + ' - ' + the_time + '=' * 40 + '\n'
        self._write_to_HTTP_log(msg)
        self._write_to_HTTP_log(request.dump())
        msg2 = '\n' + '=' * 40 + 'Response ' + str(response.id) + ' - ' + the_time + '=' * 39 + '\n'
        self._write_to_HTTP_log(msg2)
        self._write_to_HTTP_log(response.dump())
        
        self._write_to_HTTP_log('\n' + '=' * (len(msg) - 1) + '\n')
        self._http.flush()

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to a text file.
        
        Four configurable parameters exist:
            - fileName
            - httpFileName
            - verbose
        '''
