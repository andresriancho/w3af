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
from core.controllers.w3afException import w3afRunOnce

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info


class serverHeader(baseDiscoveryPlugin):
    '''
    Identify the server type based on the server header.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        self._x_powered = True
        
        # User configured variables
        self._exec_one_time = True        

    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                      (among other things) the URL to test.
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
                        break
                
                if server != '':
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Server header')
                    i.setId( response.getId() )
                    i.setDesc('The server header for the remote web server is: "' + server + '".' )
                    i['server'] = server
                    om.out.information( i.getDesc() )
                    i.addToHighlight( h + ':' )
                    
                    # Save the results in the KB so the user can look at it
                    kb.kb.append( self, 'server', i )
                    
                    # Also save this for easy internal use
                    # other plugins can use this information
                    kb.kb.save( self , 'serverString' , server )
                    
                else:
                    # strange !
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Omitted server header')
                    i.setId( response.getId() )
                    msg = 'The remote HTTP Server omitted the "server" header in its response.'
                    i.setDesc( msg )
                    om.out.information( i.getDesc() )
                    
                    # Save the results in the KB so that other plugins can use this information
                    kb.kb.append( self, 'omittedHeader', i )

                    # Also save this for easy internal use
                    # other plugins can use this information
                    kb.kb.save( self , 'serverString' , '' )
                    
                if self._exec_one_time:
                    self._exec = False
                
        if self._x_powered:
            self._check_x_power( fuzzableRequest )
        
        return []
        
    def _check_x_power( self, fuzzableRequest ):
        '''
        Analyze X-Powered-By header.
        '''
        try:
            response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
        except:
            pass
        else:
            powered_by = ''
            for header_name in response.getHeaders().keys():
                for i in [ 'ASPNET', 'POWERED']:
                    if i in header_name.upper() or header_name.upper() in i:
                        powered_by = response.getHeaders()[header_name]

                        #
                        #    Check if I already have this info in the KB
                        #
                        powered_by_in_kb = [ j['poweredBy'] for j in kb.kb.getData( 'serverHeader', 'poweredBy' ) ]
                        if powered_by not in powered_by_in_kb:
                        
                            #
                            #    I don't have it in the KB, so I need to add it,
                            #
                            i = info.info()
                            i.setPluginName(self.getName())
                            i.setName('Powered by header')
                            i.setId( response.getId() )
                            msg = '"' + header_name + '" header for this HTTP server is: "'
                            msg += powered_by + '".'
                            i.setDesc( msg )
                            i['poweredBy'] = powered_by
                            om.out.information( i.getDesc() )
                            i.addToHighlight( header_name + ':' )
                            
                            #    Save the results in the KB so that other plugins can use this information
                            # Before knowing that some servers may return more than one poweredby
                            # header I had:
                            # - kb.kb.save( self , 'poweredBy' , poweredBy )
                            # But I have seen an IIS server with PHP that returns both the ASP.NET and
                            # the PHP headers
                            powered_by_in_kb = [ j['poweredBy'] for j in kb.kb.getData( 'serverHeader', 'poweredBy' ) ]
                            if powered_by not in powered_by_in_kb:
                                kb.kb.append( self , 'poweredBy' , i )
                            
                                # Also save this for easy internal use
                                kb.kb.append( self , 'poweredByString' , powered_by )
                            
                            if self._exec_one_time:
                                self._x_powered = False          

    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Execute plugin only one time'
        h1 = 'Generally the server header wont change during a scan to a same site, so executing'
        h1 += ' this plugin only one time is a safe choice.'
        o1 = option('execOneTime', self._exec_one_time, d1, 'boolean', help=h1)
        
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
        self._exec_one_time = optionsMap['execOneTime'].getValue()

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
        This plugin GETs the server header and saves the result to the knowledge base.
        
        Nothing strange, just do a GET request to the url and save the server headers
        to the kb. A smarter way to check the server type is with the hmap plugin.
        '''
