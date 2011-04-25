'''
zone_h.py

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
from core.controllers.w3afException import w3afException, w3afRunOnce

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.data.parsers.urlParser import url_object

import re


class zone_h(baseDiscoveryPlugin):
    '''
    Find out if the site was defaced in the past.
    
    @author: Jordan Santarsieri ( jsantarsieri@cybsec.com )
    '''    
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        
    def discover(self, fuzzableRequest ):
        '''
        Search zone_h and parse the output.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
                                                    (among other things) the URL to test.
        '''
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Only run once
            self._exec = False
                        
            target_domain = fuzzableRequest.getURL().getRootDomain()
            
            # Example URL:
            # http://www.zone-h.org/archive/domain=cyprus-stones.com
        
            # TODO: Keep this URL updated!
            zone_h_url_str = 'http://www.zone-h.org/archive/domain=' + target_domain
            zone_h_url = url_object( zone_h_url_str )

            try:
                response = self._urlOpener.GET( zone_h_url )
            except w3afException, e:
                msg = 'An exception was raised while running zone-h plugin. Exception: ' + str(e)
                om.out.debug( msg )
            else:
                # This handles some wierd cases in which zone-h responds with a blank page
                if response.getBody() == '':
                    om.out.debug('Zone-h responded with a blank body.')
                    
                    # Run again in the next discovery loop
                    self._exec = True
                else:
                    self._parse_zone_h_result( response )
    
    def _parse_zone_h_result(self, response):
        '''
        Parse the result from the zone_h site and create the corresponding info objects.
        
        @return: None
        '''
        if 'No results were found' in response.getBody():
            # Nothing to see here...
            pass
        else:
            #
            #   I'm going to do only one big "if":
            #
            #       - The target site was hacked more than one time
            #       - The target site was hacked only one time
            #
            
            # This is the string I have to parse:
            # in the zone_h response, they are two like this, the first has to be ignored!
            regex = 'Total notifications: <b>(\d*)</b> of which <b>(\d*)</b> single ip and <b>(\d*)</b> mass'
            regex_result = re.findall( regex, response.getBody() )

            try:
                total_attacks = int(regex_result[0][0])
            except IndexError:
                om.out.debug('An error was generated during the parsing of the zone_h website.')
            else:
                
                # Do the if...
                if total_attacks > 1:
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setName('Previous defacements')
                    v.setURL( response.getURL() )
                    v.setSeverity( severity.MEDIUM )
                    msg = 'The target site was defaced more than one time in the past. For more'
                    msg += ' information please visit the following URL: "' + response.getURL()
                    msg += '".'
                    v.setDesc( msg )
                    kb.kb.append( self, 'defacements', v )
                    om.out.information( v.getDesc() )
                else:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Previous defacement')
                    i.setURL( response.getURL() )
                    msg = 'The target site was defaced in the past. For more information'
                    msg += ' please visit the following URL: "' + response.getURL() + '".'
                    i.setDesc( msg )
                    kb.kb.append( self, 'defacements', i )
                    om.out.information( i.getDesc() )
                
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, options ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        return '''
        This plugin searches the zone-h.org defacement database and parses the result. The information
        stored in that database is useful to know about previous defacements to the target website. In
        some cases, the defacement site provides information about the exploited vulnerability, which may
        be still exploitable.
        '''
