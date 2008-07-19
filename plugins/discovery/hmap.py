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
from core.controllers.misc.levenshtein import relative_distance

class hmap(baseDiscoveryPlugin):
    '''
    Fingerprint the server type, i.e apache, iis, tomcat, etc.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    '''
    It uses fingerprinting, not just the Server header returned by remote server.
    This plugin is a wrapper for Dustin Lee's hmap.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Control flow
        self._foundOS = False
        self._runnedHmap = False
        self._exec = True
        
        # Constant
        self._matchCount = 1
        
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
            
            if self._foundOS and self._runnedHmap:
                # Nothing else to do here.
                self._exec = False
                
            if not self._foundOS:
                self._findOS( fuzzableRequest )
            
            if not self._runnedHmap:
                self._runnedHmap = True
                
                om.out.information('Hmap web server fingerprint is starting, this may take a while.')
                
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
                    results = originalHmap.testServer( ssl, server, port, self._matchCount, self._genFpF )
                except w3afException, w3:
                    om.out.debug('A w3afException ocurred while running hmamp: ' + str(w3) )
                except Exception,  e:
                    om.out.error('An unhandled exception ocurred while running hmamp: ' + str(e) )
                else:
                    server = results[0]
                    
                    i = info.info()
                    i.setName('Webserver Fingerprint')
                    i.setDesc('The most accurate fingerprint for this HTTP server is: ' + str(server))
                    i['server'] = server
                    om.out.information( i.getDesc() )
                    
                    # Save the results in the KB so that other plugins can use this information
                    kb.kb.append( self, 'server', i )
                    kb.kb.save( self, 'serverString', i )
                    
                    # Fingerprint file generated
                    if self._genFpF:
                        om.out.information('Fingerprint file generated, please send a mail to w3af-develop@lists.sourceforge.net including'+
                        ' the fingerprint file, your name and what server you fingerprinted. New fingerprints make hmap plugin'+
                        ' more powerfull and accurate.')
            
        return []
    
    def _findOS( self, fuzzableRequest ):
        '''
        Analyze responses and determine if remote web server runs on windows or *nix
        @Return: None, the knowledge is saved in the knowledgeBase
        '''
        dirs = urlParser.getDirectories( fuzzableRequest.getURL() )
        filename = urlParser.getFileName( fuzzableRequest.getURL() )
        if len( dirs ) > 1 and filename:
            last = dirs[-1]
            windowsURL = last[0:-1] + '\\' + filename
            windowsResponse = self._urlOpener.GET( windowsURL )
            
            originalResponse = self._urlOpener.GET( fuzzableRequest.getURL() )
            self._foundOS = True
            
            if relative_distance( originalResponse.getBody(), windowsResponse.getBody() ) > 0.98:
                i = info.info()
                i.setName('Operating system')
                i.setURL( windowsResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('Fingerprinted this host as a Microsoft Windows system.' )
                i.setId( windowsResponse.id )
                kb.kb.append( self, 'operatingSystem', 'windows' )
                om.out.information( i.getDesc() )
            else:
                i = info.info()
                i.setName('Operating system')
                i.setURL( originalResponse.getURL() )
                i.setMethod( 'GET' )
                i.setDesc('Fingerprinted this host as a *nix system. Detection for this operating system is weak, "if not windows: is linux".' )
                i.setId( originalResponse.id )
                kb.kb.append( self, 'operatingSystem', 'unix' )
                om.out.information( i.getDesc() )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        d1 = 'Generate a fingerprint file.'
        h1 = 'Define if we will generate a fingerprint file based on the findings made during this execution.'
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
        server type, version and patch level.
        
        One configurable parameters exist:
            - genFpF
            
        if genFpF is set to True, a fingerprint file is generated. Fingerprint files are used to identify unknown web servers, if you
        generate new files please send them to w3af.project@gmail.com so we can add them to the framework.
        '''
