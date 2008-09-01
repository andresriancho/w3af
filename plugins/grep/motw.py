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
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.urlParser as uparser
from core.data.getResponseType import *
import re

class motw (baseGrepPlugin):
    """
    Identify whether the page is compliant to mark of the web.
    @author: Sharad Ganapathy sharadgana |at| gmail.com
    """
    def __init__(self):
        baseGrepPlugin.__init__(self)
        #The following regex matches a valid url as well as the text about:internet. 
        # Also it validates the number in the parenthesis. It should be a 4 digit number and must tell about the 
        # length of the url that follows
        self._motw_re = re.compile(r"""^<!-\-\s{1}saved from url=\(([\d]{4})\)(https?://([-\w\.]+)+(:\d+)?(/([\w/_\.]*(\?\S+)?)?)?|about:internet)\s{1}\-\->""")
        self._withoutMOTW = False


    def _testResponse(self, request, response):

        if response.is_text_or_html():
            self.is404 = kb.kb.getData( 'error404page', '404' )
            if not self.is404( response ):
                motw = self._motw_re.search(response.getBody())
                
                # Create the info object
                if motw or self._withoutMOTW:
                    i = info.info()
                    i.setName('Mark of the web')
                    i.setURL( response.getURL() )
                    i.setId( response.id )
                
                # Act based on finding/non-finding
                if motw :
                    url_length_indicated = int(motw.group(1))
                    url_length_actual =len(motw.group(2))
                    if (url_length_indicated <= url_length_actual):
                        msg = 'The  URL: '  + response.getURL() + ' contains a  valid Mark of the Web.'
                        i.setDesc( msg )
                        kb.kb.append( self, 'motw', i )
                    else:
                        msg = 'The URL: ' + response.getURL() + ' will be executed in Local Machine Zone security context because the indicated length is greater than the actual URL length.'
                        i['localMachine'] = True
                        i.setDesc( msg )
                        kb.kb.append( self, 'motw', i )
              
                elif  self._withoutMOTW:
                    msg = "The URL: " + response.getURL() + " doesn't contain a Mark of the Web."
                    i.setDesc( msg )
                    kb.kb.append( self, 'no_motw', i )

    def setOptions( self, optionsMap ):
        self._withoutMOTW = optionsMap['withoutMOTW'].getValue()
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'List the pages that don\'t have a MOTW'
        o1 = option('withoutMOTW', self._withoutMOTW, d1, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        return ol
            
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        # Print the results to the user
        prettyMsg = {}
        prettyMsg['motw'] = 'The following URLs contain a MOTW:'
        prettyMsg['no_motw'] = 'The following URLs don\'t contain a MOTW:'
        for type in prettyMsg:
            inform = []
            for i in kb.kb.getData( 'motw', type ):
                inform.append( i )
        
            if len( inform ):
                om.out.information( prettyMsg[ type ] )
                for i in inform:
                    if 'localMachine' not in i:
                        om.out.information( '- ' + i.getURL() )
                    else:
                        om.out.information( '- ' + i.getURL() + ' [Executed in Local machine context]')
    
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
        This plugin will specify whether the page is compliant against the MOTW standard. The standard is explained in:
            - http://msdn2.microsoft.com/en-us/library/ms537628.aspx
            
        This plugin tests if the length of the URL specified by "(XYZW)" is lower, equal or greater than the length of the
        URL; and also reports the existance of this tag in the body of all analyzed pages.
        
        One configurable parameter exists:
            - withoutMOTW
            
        If "withoutMOTW" is enabled, the plugin will show all URLs that don't contain a MOTW.
        '''
