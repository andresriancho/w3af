'''
remoteFileInclude.py

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
from core.controllers.misc.homeDir import get_home_dir
from core.controllers.misc.get_local_ip import get_local_ip
from core.controllers.misc.is_private_site import is_private_site

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.w3afException import w3afException
import core.controllers.daemons.webserver as webserver
import core.data.constants.w3afPorts as w3afPorts

import os
import socket

CONFIG_ERROR_MSG = 'audit.remoteFileInclude plugin has to be correctly ' \
'configured to use. Please set the correct values for local address and ' \
'port, or use the official w3af site as the target server for remote ' \
'inclusions.'


class remoteFileInclude(baseAuditPlugin):
    '''
    Find remote file inclusion vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._error_reported = False
        
        # User configured parameters
        self._rfi_url = ''
        self._rfi_result = ''
        self._listen_port = w3afPorts.REMOTEFILEINCLUDE
        self._listen_address = get_local_ip() or ''
        self._use_w3af_site = True
        
    def audit(self, freq):
        '''
        Tests an URL for remote file inclusion vulnerabilities.
        
        @param freq: A fuzzableRequest object
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
                
        self._tm.join(self)
    
    def _correctly_configured(self):
        '''
        @return: True if the plugin is correctly configured to run.
        '''
        listen_address = self._listen_address
        if not listen_address:
            if not self._use_w3af_site:
                return False
        else:
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
        
        @param freq: A fuzzableRequest object
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
        is_target_priv = is_private_site(urlParser.getDomain(freq.getURL()))
            
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
                
                # Wait for threads to finish
                self._tm.join(self)
            finally:
                self._rm_file()
            
    def _w3af_site_test_inclusion(self, freq):
        '''
        Check for RFI using the official w3af site.
        
        @param freq: A fuzzableRequest object
        @return: None, everything is saved to the kb
        '''        
        self._rfi_url = 'http://w3af.sourceforge.net/w3af/remoteFileInclude.html'
        self._rfi_result = 'w3af is goood!'
        # Perform the real work
        self._test_inclusion(freq)
        
    def _test_inclusion(self, freq):
        '''
        Checks a fuzzableRequest for remote file inclusion bugs.
        
        @return: None
        '''
        oResponse = self._sendMutant(freq, analyze=False).getBody()
        
        rfi_url_list = [self._rfi_url]
        mutants = createMutants(freq, rfi_url_list, oResponse=oResponse)
        
        for mutant in mutants:
            
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._hasNoBug('remoteFileInclude', 'remoteFileInclude',
                              mutant.getURL(), mutant.getVar()):
                
                targs = (mutant,)
                self._tm.startFunction(target=self._sendMutant, args=targs,
                                       ownerObj=self)
                
    def _analyzeResult(self, mutant, response):
        '''
        Analyze results of the _sendMutant method.
        '''
        #
        #   Only one thread at the time can enter here. This is because I want to report each
        #   vulnerability only once, and by only adding the "if self._hasNoBug" statement, that
        #   could not be done.
        #
        with self._plugin_lock:
            
            #
            #   I will only report the vulnerability once.
            #
            if self._hasNoBug('remoteFileInclude', 'remoteFileInclude', 
                                mutant.getURL(), mutant.getVar()):
                
                if self._rfi_result in response:
                    v = vuln.vuln(mutant)
                    v.setPluginName(self.getName())
                    v.setId(response.id)
                    v.setSeverity(severity.HIGH)
                    v.setName('Remote file inclusion vulnerability')
                    v.setDesc('Remote file inclusion was found at: ' + mutant.foundAt())
                    kb.kb.append(self, 'remoteFileInclude', v)
                
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
                            kb.kb.append(self, 'remoteFileInclude', v)
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join(self)
        self.printUniq(kb.kb.getData('remoteFileInclude', 'remoteFileInclude'), 'VAR')

    def _create_file(self):
        '''
        Create random name file php with random php content. To be used in the
        remote file inclusion test.
        '''
        # First, generate the php file to be included.
        rand1 = createRandAlNum(9)
        rand2 = createRandAlNum(9)
        filename = createRandAlNum()
        php_code = '<? \n echo "%s";\n echo "%s";\n ?>' % (rand1, rand2)
        
        # Write the php to the webroot
        file_handler = open(os.path.join(get_home_dir(), 'webroot', filename), 'w')
        file_handler.write(php_code)
        file_handler.close()
        
        # Define the required parameters
        self._rfi_url = 'http://' + self._listen_address +':' + str(self._listen_port)
        self._rfi_url += '/' + filename
        self._rfi_result = rand1 + rand2
        
    def _rm_file(self):
        '''
        Stop the server, remove the file from the webroot.
        '''
        # Remove the file
        filename = urlParser.getFileName(self._rfi_url)
        os.remove(os.path.join(get_home_dir(), 'webroot', filename))

    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'IP address that the webserver will use to receive requests'
        h1 = 'w3af runs a webserver to serve the files to the target web application \
        when doing remote file inclusions. This setting configures where the webserver\
        is going to listen for requests.'
        o1 = option('listenAddress', self._listen_address, d1, 'string', help=h1)

        d2 = 'TCP port that the webserver will use to receive requests'
        o2 = option('listenPort', self._listen_port, d2, 'integer')

        d3 = 'Use w3af site to test for remote file inclusion'
        h3 =  'The plugin can use the w3af site to test for remote file inclusions, which is\
        convenient when you are performing a test behind a NAT firewall.'
        o3 = option('usew3afSite', self._use_w3af_site, d3, 'boolean',  help=h3)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._listen_address = optionsMap['listenAddress'].getValue()
        self._listen_port = optionsMap['listenPort'].getValue()
        self._use_w3af_site = optionsMap['usew3afSite'].getValue()
        
        if not self._correctly_configured():
            raise w3afException(CONFIG_ERROR_MSG)

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds remote file inclusion vulnerabilities.
        
        Three configurable parameters exist:
            - listenAddress
            - listenPort
            - usew3afSite
        
        There are two ways of running this plugin, one is the most common one, by using the w3af
        site ( w3af.sf.net ) as the place from where the target web application will fetch the
        remote file. The other way to test for inclusion is to run a webserver on the local machine
        that is performing the scan. The second option is configured using the "listenAddress" and
        "listenPort" parameters.
        '''
