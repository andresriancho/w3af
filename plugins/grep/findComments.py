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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import re


class findComments(baseGrepPlugin):
    '''
    Find HTML comments.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)

        # Internal variables
        self._comments = {}
        self._interestingWords = ['user', 'pass', 'xxx', 'fix', 'bug', 'broken', 'oops', 'hack', 
        'caution', 'todo', 'note', 'warning', '!!!', '???', 'shit','stupid', 'tonto', 'porqueria',
        'ciudado', 'usuario', 'contrase', 'puta']
        self._already_reported_interesting = []
        self.is404 = None

        # User configurations
        self._search404 = False
        
    def grep(self, request, response):
        '''
        Plugin entry point, parse those comments!
        @return: None
        '''
        # Set the is404 method if not already set
        if not self.is404:
            self.is404 = kb.kb.getData( 'error404page', '404' )

        if response.is_text_or_html():
            if not self.is404( response ) or self._search404:
                
                try:
                    dp = dpCache.dpc.getDocumentParserFor( response )
                except w3afException:
                    return

                commentList = dp.getComments()
                
                for comment in commentList:
                    # This next two lines fix this issue:
                    # audit.ssi + grep.findComments + web app with XSS = false positive
                    if self._wasSent( request, '<!--'+comment+'>' ):
                        continue
                        
                    if comment not in self._comments.keys():
                        self._comments[ comment ] = [ (response.getURL(), response.id), ]
                    else:
                        if response.getURL() not in [ x[0] for x in self._comments[ comment ] ]:
                            self._comments[ comment ].append( (response.getURL(), response.id) )
                    
                    comment = comment.lower()
                    for word in self._interestingWords:
                        if word in comment and ( word, response.getURL() ) not in self._already_reported_interesting:
                            i = info.info()
                            i.setName('HTML comment with "' + word + '" inside')
                            msg = 'A comment with the string "' + word + '" was found in: "'
                            msg += response.getURL() + '". This could be interesting.'
                            i.setDesc( msg )
                            i.setId( response.id )
                            i.setDc( request.getDc )
                            i.setURI( response.getURI() )
                            kb.kb.append( self, 'interestingComments', i )
                            om.out.information( i.getDesc() )
                            self._already_reported_interesting.append( ( word, response.getURL() ) )
                    
                    if re.search('<[a-zA-Z]*.*?>.*?</[a-zA-Z]>', comment) and \
                    ( comment, response.getURL() ) not in self._already_reported_interesting:
                        # There is HTML code in the comment.
                        i = info.info()
                        i.setName('HTML comment contains HTML code')
                        desc = 'A comment with the string "' +comment + '" was found in: "'
                        desc += response.getURL() + '" . This could be interesting.'
                        i.setDesc( desc )
                        i.setId( response.id )
                        i.setDc( request.getDc )
                        i.setURI( response.getURI() )
                        kb.kb.append( self, 'htmlCommentsHideHtml', i )
                        om.out.information( i.getDesc() )
                        self._already_reported_interesting.append( ( comment, response.getURL() ) )
                            
    def setOptions( self, optionsMap ):
        self._search404 = optionsMap['search404'].getValue()
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Search for HTML comments in 404 pages.'
        o1 = option('search404', self._search404, d1, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        inform = []
        for comment in self._comments.keys():
            urls_with_this_comment = self._comments[comment]
            om.out.information('The comment : "' + comment + '" was found on this URL(s):')
            for url , request_id in urls_with_this_comment:
                inform.append('- ' + url + ' (request with id:'+str(request_id)+')' )
        
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
