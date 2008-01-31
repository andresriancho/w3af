'''
findComments.py

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

import core.data.parsers.dpCache as dpCache
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
from core.data.getResponseType import *

class findComments(baseGrepPlugin):
    '''
    Find HTML comments.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        # This is nicer, but htmlParser inherits from SGMLParser that AINT
        # thread safe, So i have to create an instance of htmlParser for every
        # call to testResponse
        #self._htmlParser = htmlParser.htmlParser()
        self._comments = {}
        self._search404 = False
        self._interestingWords = ['user', 'pass', 'xxx', 'fix', 'bug', 'broken', 'oops', 'hack', 
        'caution', 'todo', 'note', 'warning', '!!!', '???', 'shit','stupid', 'tonto', 'porqueria',
        'ciudado', 'usuario', 'contrase', 'puta']
        self._alreadyReportedInteresting = []
        
    def _testResponse(self, request, response):
            
        if isTextOrHtml(response.getHeaders()):
            
            self.is404 = kb.kb.getData( 'error404page', '404' )
            
            if not self.is404( response ) or self._search404:
                dp = dpCache.dpc.getDocumentParserFor( response.getBody(), response.getURL() )
                commentList = dp.getComments()
                
                for comment in commentList:
                    # This next two lines fix this issue:
                    # audit.ssi + grep.findComments + web app with XSS = false positive
                    if self._wasSent( request, '<!--'+comment+'>' ):
                        continue
                        
                    if comment not in self._comments.keys():
                        self._comments[ comment ] = [ response.getURL(), ]
                    else:
                        if response.getURL() not in self._comments[ comment ]:
                            self._comments[ comment ].append( response.getURL() )
                    
                    comment = comment.lower()
                    for word in self._interestingWords:
                        if comment.count( word ) and ( word, response.getURL() ) not in self._alreadyReportedInteresting:
                            i = info.info()
                            i.setDesc( 'A comment with the string "' + word + '" was found in: ' + response.getURL() + ' . This could be interesting.' )
                            i.setId( response.id )
                            i.setDc( request.getDc )
                            i.setURI( response.getURI() )
                            kb.kb.append( self, 'interestingComments', i )
                            om.out.information( i.getDesc() )
                            self._alreadyReportedInteresting.append( ( word, response.getURL() ) )
                    
    def setOptions( self, optionsMap ):
        self._search404 = optionsMap['search404']
    
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/output.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="search404">\
                <default>'+str(self._search404)+'</default>\
                <desc>Search comments on 404 pages.</desc>\
                <type>boolean</type>\
            </Option>\
        </OptionList>\
        '

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        inform = []
        for comment in self._comments.keys():
            urlsWithThisComment = self._comments[comment]
            om.out.information('The comment : "' + comment + '" was found on this URLs:')
            for url in urlsWithThisComment:
                inform.append('- ' + url )
        
            inform.sort()
            inform = list(set(inform))
            for i in inform:
                om.out.information( i )

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
        This plugin greps every page for comments, special comments like the ones containing the words
        "password" or "user" are specially reported.
        '''
