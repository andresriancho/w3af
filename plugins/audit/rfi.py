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
from __future__ import with_statement

import os
import socket

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.controllers.daemons.webserver as webserver
import core.data.constants.w3afPorts as w3afPorts

from core.controllers.plugins.audit_plugin import AuditPlugin
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.get_local_ip import get_local_ip
from core.controllers.misc.is_private_site import is_private_site
from core.controllers.w3afException import w3afException

from core.data.options.option import option
from core.data.options.option_list import OptionList
from core.data.fuzzer.fuzzer import create_mutants, rand_alnum
from core.data.parsers.urlParser import url_object

CONFIG_ERROR_MSG = ('audit.rfi plugin has to be correctly '
'configured to use. Please set the correct values for local address and '
'port, or use the official w3af site as the target server for remote '
'inclusions.')

RFI_TEST_URL = 'http://w3af.sourceforge.net/w3af/rfi.html'


class rfi(AuditPlugin):
    '''
    Find remote file inclusion vulnerabilities.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        AuditPlugin.__init__(self)
        
        # Internal variables
        self._error_reported = False
        
        # User configured parameters
        self._rfi_url = None
        self._rfi_result = None
        self._listen_port = w3afPorts.REMOTEFILEINCLUDE
        self._listen_address = get_local_ip() or ''
        self._use_w3af_site = True
        
    def audit(self, freq):
        '''
        Tests an URL for remote file inclusion vulnerabilities.
        
        @param freq: A fuzzable_request object
        '''
        # Sanity check 
        if not self._correctly_configured():
            # Report error to the user only once
            self._error_reported = True
            raise w3afException(CONFIG_ERROR_MSG)
        
        if not self._error_reported:
            # 1- create a request that will include a file from a local web server
            self._local_test_inclusion(freq)
            
            # The plugin is going to use two different techniques:
            # 2- create a request that will include a file from the w3af official site
            if self._use_w3af_site:
                self._w3af_site_test_inclusion(freq)
        
    def _correctly_configured(self):
        '''
        @return: True if the plugin is correctly configured to run.
        '''
        if self._use_w3af_site:
            return True
        
        listen_address = self._listen_address
        listen_port = self._listen_port
        
        if listen_address and listen_port:
            with self._plugin_lock:
                # If we have an active instance then we're OK!
                if webserver.is_running(listen_address, 
                                        self._listen_port):
                    return True
                else:
                    # Now test if it's possible to bind the address
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        s.bind((listen_address, self._listen_port))
                    except socket.error:
                        return False
                    finally:
                        s.close()
                        del s
                    return True
    
    def _local_test_inclusion(self, freq):
        '''
        Check for RFI using a local web server
        
        @param freq: A fuzzable_request object
        @return: None, everything is saved to the kb
        '''
        #
        # The listen address is an empty string when I have no default route
        #
        # Only work if:
        #   - The listen address is private and the target address is private
        #   - The listen address is public and the target address is public
        #
        if self._listen_address == '':
            return
        
        is_listen_priv = is_private_site(self._listen_address)
        is_target_priv = is_private_site(freq.getURL().getDomain())
            
        if (is_listen_priv and is_target_priv) or \
            not (is_listen_priv or is_target_priv):
            om.out.debug('RFI test using local web server for URL: ' + freq.getURL())
            om.out.debug('w3af is running a webserver')
            try:
                # Create file for remote inclusion
                self._create_file()
                
                # Start web server
                webroot = os.path.join(get_home_dir(), 'webroot')
                webserver.start_webserver(self._listen_address,
                                          self._listen_port, webroot)
                
                # Perform the real work
                self._test_inclusion(freq)
            except Exception, e:
                om.out.error('An error occurred while running local webserver:'
                             ' "%s"' % e)
            finally:
                self._rm_file()
            
    def _w3af_site_test_inclusion(self, freq):
        '''
        Check for RFI using the official w3af site.
        
        @param freq: A fuzzable_request object
        @return: None, everything is saved to the kb
        '''        
        self._rfi_url = url_object(RFI_TEST_URL)
        self._rfi_result = 'w3af is goood!'
        # Perform the real work
        self._test_inclusion(freq)
        
    def _test_inclusion(self, freq):
        '''
        Checks a fuzzable_request for remote file inclusion bugs.
        
        @return: None
        '''
        orig_resp = self._uri_opener.send_mutant(freq)
        
        rfi_url = str(self._rfi_url)
        # FIXME: We don't really care about this null byte, but we should have
        # a handler that returns the content we want for every HTTP request,
        # without checking the filename
        rfi_url_list = [rfi_url, rfi_url + '\0']
        mutants = create_mutants(freq, rfi_url_list, orig_resp=orig_resp)
        
        self._send_mutants_in_threads(self._uri_opener.send_mutant,
                                      mutants,
                                      self._analyze_result)
                
    def _analyze_result(self, mutant, response):
        '''
        Analyze results of the _send_mutant method.
        '''
        #
        #   I will only report the vulnerability once.
        #
        if self._has_no_bug(mutant):
            
            if self._rfi_result in response:
                v = vuln.vuln(mutant)
                v.setPluginName(self.getName())
                v.setId(response.id)
                v.setSeverity(severity.HIGH)
                v.setName('Remote file inclusion vulnerability')
                v.setDesc('Remote file inclusion was found at: ' + mutant.foundAt())
                kb.kb.append(self, 'rfi', v)
            
            else:
                #
                #   Analyze some errors that indicate that there is a RFI but with some
                #   "configuration problems"
                #
                rfi_errors = ['php_network_getaddresses: getaddrinfo',
                              'failed to open stream: Connection refused in']
                for error in rfi_errors:
                    if error in response and not error in mutant.getOriginalResponseBody():
                        v = vuln.vuln( mutant )
                        v.setPluginName(self.getName())
                        v.setId( response.id )
                        v.setSeverity(severity.MEDIUM)
                        v.addToHighlight(error)
                        v.setName('Remote file inclusion vulnerability')
                        v.setDesc('Remote file inclusion was found at: ' + mutant.foundAt())
                        kb.kb.append(self, 'rfi', v)

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self.print_uniq(kb.kb.getData('rfi', 'rfi'), 'VAR')

    def _create_file(self):
        '''
        Create random name file php with random php content. To be used in the
        remote file inclusion test.
        '''
        # First, generate the php file to be included.
        rand1 = rand_alnum(9)
        rand2 = rand_alnum(9)
        filename = rand_alnum()
        php_code = '<? \n echo "%s";\n echo "%s";\n ?>' % (rand1, rand2)
        
        # Write the php to the webroot
        file_handler = open(os.path.join(get_home_dir(), 'webroot', filename), 'w')
        file_handler.write(php_code)
        file_handler.close()
        
        # Define the required parameters
        netloc = self._listen_address +':' + str(self._listen_port)
        path = '/' + filename
        self._rfi_url = url_object.from_parts('http', netloc, path, None, None, None)
        self._rfi_result = rand1 + rand2
        
    def _rm_file(self):
        '''
        Stop the server, remove the file from the webroot.
        '''
        # Remove the file
        filename = self._rfi_url.getFileName()
        os.remove(os.path.join(get_home_dir(), 'webroot', filename))

    def get_options(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        
        d = 'IP address that the webserver will use to receive requests'
        h = 'w3af runs a webserver to serve the files to the target web application \
        when doing remote file inclusions. This setting configures where the webserver\
        is going to listen for requests.'
        o = option('listenAddress', self._listen_address, d, 'string', help=h)
        ol.add(o)
        
        d = 'TCP port that the webserver will use to receive requests'
        o = option('listenPort', self._listen_port, d, 'integer')
        ol.add(o)
        
        d = 'Use w3af site to test for remote file inclusion'
        h =  'The plugin can use the w3af site to test for remote file inclusions, which is\
        convenient when you are performing a test behind a NAT firewall.'
        o = option('usew3afSite', self._use_w3af_site, d, 'boolean',  help=h)
        ol.add(o)
        
        return ol
        
    def set_options( self, options_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter options_list: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listen_address = options_list['listenAddress'].getValue()
        self._listen_port = options_list['listenPort'].getValue()
        self._use_w3af_site = options_list['usew3afSite'].getValue()
        
        if not self._correctly_configured():
            raise w3afException(CONFIG_ERROR_MSG)

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds remote file inclusion vulnerabilities.
        
        Three configurable parameters exist:
            - listenAddress
            - listenPort
            - usew3afSite
        
        There are two ways of running this plugin, one is the most common one,
        by using the w3af site ( w3af.sf.net ) as the place from where the target
        web application will fetch the remote file. The other way to test for
        inclusion is to run a webserver on the local machine that is performing
        the scan. The second option is configured using the "listenAddress" and
        "listenPort" parameters.
        '''
