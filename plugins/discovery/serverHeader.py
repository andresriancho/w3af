'''
serverHeader.py

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
from core.controllers.w3afException import w3afRunOnce

class serverHeader(baseDiscoveryPlugin):
    '''
    Identify the server type based on the server header.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    '''
    Nothing strange, just do a GET request to the url and save the server headers
    to the kb. A smarter way to check the server type is with the hmap plugin.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._execOneTime = True
        self._exec = True
        self._xpowered = True

    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            try:
                response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )       
            except KeyboardInterrupt,e:
                raise e
            else:
                server = ''
                for h in response.getHeaders().keys():
                    if h.lower() == 'server':
                        server = response.getHeaders()[h]
                
                if server != '':
                    # Output the results
                    om.out.information('The Server header for this HTTP server is: ' + server )
                    # Save the results in the KB so that other plugins can use this information
                    kb.kb.save( self , 'server' , server )
                else:
                    # strange !
                    om.out.information('The remote HTTP Server ommited the "Server" header in its response.' )
    
                if self._execOneTime:
                    self._exec = False
                
        if self._xpowered:
            self._checkXPower( fuzzableRequest )
        
        return []
        
    def _checkXPower( self, fuzzableRequest ):
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except:
            pass
        else:
            poweredBy = ''
            for h in response.getHeaders().keys():
                for d in [ 'ASPNET','POWERED']:
                    if d in h.upper() or h.upper() in d :
                        poweredBy = response.getHeaders()[h]
                        # Output the results
                        om.out.information( h + ' header for this HTTP server is: ' + poweredBy )
                        # Save the results in the KB so that other plugins can use this information
                        
                        # Before knowing that some servers may return more than one poweredby header I had:
                        #kb.kb.save( self , 'poweredBy' , poweredBy )
                        # But I have seen an IIS server with PHP that returns both the ASP.NET and the PHP headers
                        if poweredBy not in kb.kb.getData( 'serverHeader', 'poweredBy' ):
                            kb.kb.append( self , 'poweredBy' , poweredBy )
                        
                        if self._execOneTime:
                            self._xpowered = False          
            
            if poweredBy == '':
                # not as strange as the one above, this is because of a config or simply
                # cause I requested a static "html" file.
                # I will save the server header as the poweredBy, its the best choice I have right now
                if kb.kb.getData( 'serverHeader' , 'server' ) not in kb.kb.getData( 'serverHeader', 'poweredBy' ):
                    kb.kb.append( self , 'poweredBy' , kb.kb.getData( 'serverHeader' , 'server' ) )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Execute plugin only one time'
        h1 = 'Generally the server header wont change during a scan to \
    a same site, so executing this plugin only one time is a safe choice.'
        o1 = option('execOneTime', self._execOneTime, d1, 'boolean', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._execOneTime = optionsMap['execOneTime'].getValue()

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
        This plugin gets the server header and saves the result to the knowledgeBase.
        '''
