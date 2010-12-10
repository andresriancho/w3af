'''
hmap.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import plugins.discovery.oHmap.hmap as originalHmap

import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afRunOnce,  w3afException


class hmap(baseDiscoveryPlugin):
    '''
    Fingerprint the server type, i.e apache, iis, tomcat, etc.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Control flow
        self._runned_hmap = False
        self._exec = True
        
        # User configured parameters
        self._genFpF = False

    def discover(self, fuzzableRequest ):
        '''
        It calls the "main" from hmap and writes the results to the kb.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            
            if self._runned_hmap:
                # Nothing else to do here.
                self._exec = False
                            
            if not self._runned_hmap:
                self._runned_hmap = True
                
                msg = 'Hmap web server fingerprint is starting, this may take a while.'
                om.out.information( msg )
                
                url = fuzzableRequest.getURL()
                protocol = urlParser.getProtocol( url )
                server = urlParser.getNetLocation( url )
                
                # Set some defaults that can be overriden later
                if protocol == 'https':
                    port = 443
                    ssl = True
                else:
                    port = 80
                    ssl = False
                
                # Override the defaults
                if server.count(':'):
                    port = int( server.split(':')[1] )
                    server = server.split(':')[0]

                
                try:
                    results = originalHmap.testServer( ssl, server, port, 1, self._genFpF )
                except w3afException, w3:
                    msg = 'A w3afException ocurred while running hmap: "' + str(w3) + '"'
                    om.out.error( msg )
                except Exception,  e:
                    msg = 'An unhandled exception ocurred while running hmap: "' + str(e) + '"'
                    om.out.error( msg )
                else:
                    #
                    #   Found any results?
                    # 
                    if len(results):
                        server = results[0]
                    
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('Webserver Fingerprint')
                        desc = 'The most accurate fingerprint for this HTTP server is: "'
                        desc += str(server) + '".'
                        i.setDesc( desc )
                        i['server'] = server
                        om.out.information( i.getDesc() )
                        
                        # Save the results in the KB so that other plugins can use this information
                        kb.kb.append( self, 'server', i )
                        kb.kb.save( self, 'serverString', server )
                    
                    #
                    # Fingerprint file generated (this is independent from the results)
                    #
                    if self._genFpF:
                        msg = 'Hmap fingerprint file generated, please send a mail to w3af-develop'
                        msg += '@lists.sourceforge.net including the fingerprint file, your name'
                        msg += ' and what server you fingerprinted. New fingerprints make the hmap'
                        msg += ' plugin more powerfull and accurate.'
                        om.out.information( msg )
            
        return []
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'Generate a fingerprint file.'
        h1 = 'Define if we will generate a fingerprint file based on the findings made during this'
        h1 += ' execution.'
        o1 = option('genFpF', self._genFpF, d1, 'boolean', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._genFpF = optionsMap['genFpF'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        # I dont really use the serverType plugin here, but it is nice to have two
        # opinions about what we are dealing with.
        return ['discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin fingerprints the remote web server and tries to determine the
        server type, version and patch level. It uses fingerprinting, not just the Server
        header returned by remote server. This plugin is a wrapper for Dustin Lee's hmap.
        
        One configurable parameters exist:
            - genFpF
            
        If genFpF is set to True, a fingerprint file is generated. Fingerprint files are 
        used to identify web servers, if you generate new files please send them 
        to w3af.project@gmail.com so we can add them to the framework.
        
        One important thing to notice is that hmap connects directly to the remote web
        server, without using the framework HTTP configurations (like proxy or authentication).
        '''

