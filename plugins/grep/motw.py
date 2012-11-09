''''
motw.py

Copyright 2007 Sharad Ganapathy

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
import re

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.kb.info as info

from core.controllers.plugins.grep_plugin import GrepPlugin
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList


class motw (GrepPlugin):
    """
    Identify whether the page is compliant to mark of the web.
    @author: Sharad Ganapathy sharadgana |at| gmail.com
    """
    def __init__(self):
        GrepPlugin.__init__(self)

        # The following regex matches a valid url as well as the text about:internet.
        # Also it validates the number in the parenthesis. It should be a 4 digit number
        # and must tell about the length of the url that follows
        regex = r"""<!--\s*saved from url=\(([\d]{4})\)(https?://([-\w\.]+)"""
        regex += r"""+(:\d+)?(/([\w/_\.]*(\?\S+)?)?)?|about:internet)\s{1}\-\->"""
        self._motw_re = re.compile(regex)

        # User configured parameter
        self._withoutMOTW = False

    def grep(self, request, response):
        '''
        Plugin entry point, search for motw.
        
        @param request: The HTTP request object.
        @param response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html():

            if not is_404( response ):
                motw_match = self._motw_re.search(response.getBody())

                # Create the info object
                if motw_match or self._withoutMOTW:
                    i = info.info()
                    i.setPluginName(self.get_name())
                    i.set_name('Mark of the web')
                    i.setURL( response.getURL() )
                    i.set_id( response.id )
                    i.addToHighlight(motw_match.group(0))
                
                # Act based on finding/non-finding
                if motw_match:

                    # This int() can't fail because the regex validated
                    # the data before
                    url_length_indicated = int(motw_match.group(1))
                    url_length_actual = len(motw_match.group(2))
                    if (url_length_indicated <= url_length_actual):
                        msg = 'The  URL: "'  + response.getURL() + '"'
                        msg += ' contains a  valid Mark of the Web.'
                        i.set_desc( msg )
                        kb.kb.append( self, 'motw', i )
                    else:
                        msg = 'The URL: "' + response.getURL() + '" will be executed in Local '
                        msg += 'Machine Zone security context because the indicated length is '
                        msg += 'greater than the actual URL length.'
                        i['localMachine'] = True
                        i.set_desc( msg )
                        kb.kb.append( self, 'motw', i )
              
                elif self._withoutMOTW:
                    msg = 'The URL: "' + response.getURL()
                    msg += '" doesn\'t contain a Mark of the Web.'
                    i.set_desc( msg )
                    kb.kb.append( self, 'no_motw', i )

    def set_options( self, options_list ):
        self._withoutMOTW = options_list['withoutMOTW'].get_value()
        
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        
        d1 = 'List the pages that don\'t have a MOTW'
        o1 = opt_factory('withoutMOTW', self._withoutMOTW, d1, 'boolean')
        ol.add(o1)
        
        return ol
            
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print the results to the user
        pretty_msg = {}
        pretty_msg['motw'] = 'The following URLs contain a MOTW:'
        pretty_msg['no_motw'] = 'The following URLs don\'t contain a MOTW:'
        for motw_type in pretty_msg:
            inform = []
            for i in kb.kb.get( 'motw', motw_type ):
                inform.append( i )
        
            if len( inform ):
                om.out.information( pretty_msg[ motw_type ] )
                for i in inform:
                    if 'localMachine' not in i:
                        om.out.information( '- ' + i.getURL() )
                    else:
                        msg = '- ' + i.getURL() + ' [Executed in Local machine context]'
                        om.out.information( msg )
    
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will specify whether the page is compliant against the MOTW
        standard. The standard is explained in:
            - http://msdn2.microsoft.com/en-us/library/ms537628.aspx
            
        This plugin tests if the length of the URL specified by "(XYZW)" is
        lower, equal or greater than the length of the URL; and also reports the
        existence of this tag in the body of all analyzed pages.
        
        One configurable parameter exists:
            - withoutMOTW
            
        If "withoutMOTW" is enabled, the plugin will show all URLs that don't
        contain a MOTW.
        '''
