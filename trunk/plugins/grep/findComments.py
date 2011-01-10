# coding: utf-8

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

from core.controllers.coreHelpers.fingerprint_404 import is_404
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
        'ciudado', 'usuario', 'contrase', 'puta',
        'secret','@', 'email','security','captcha',
        # some in Portuguese
        'banco', 'bradesco', 'itau', 'visa', 'bancoreal', 'transfêrencia', 'depósito', 'cartão', 'crédito', 'dados pessoais'
        ]
        self._already_reported_interesting = []

        # User configurations
        self._search404 = False
        
    def grep(self, request, response):
        '''
        Plugin entry point, parse those comments!
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        @return: None
        '''
        if response.is_text_or_html():
            if not is_404( response ) or self._search404:
                
                try:
                    dp = dpCache.dpc.getDocumentParserFor( response )
                except w3afException:
                    return

                commentList = dp.getComments()

                for comment in commentList:
                    # This next two lines fix this issue:
                    # audit.ssi + grep.findComments + web app with XSS = false positive
                    if request.sent( '<!--'+comment+'>' ):
                        continue
                    
                    # show nice comments ;)
                    comment = comment.strip()
                    
                    if comment not in self._comments.keys():
                        self._comments[ comment ] = [ (response.getURL(), response.id), ]
                    else:
                        if response.getURL() not in [ x[0] for x in self._comments[ comment ] ]:
                            self._comments[ comment ].append( (response.getURL(), response.id) )
                    
                    comment = comment.lower()
                    for word in self._interestingWords:
                        if word in comment and ( word, response.getURL() ) not in self._already_reported_interesting:
                            i = info.info()
                            i.setPluginName(self.getName())
                            i.setName('HTML comment with "' + word + '" inside')
                            msg = 'A comment with the string "' + word + '" was found in: "'
                            msg += response.getURL() + '". This could be interesting.'
                            i.setDesc( msg )
                            i.setId( response.id )
                            i.setDc( request.getDc )
                            i.setURI( response.getURI() )
                            i.addToHighlight( word )
                            kb.kb.append( self, 'interestingComments', i )
                            om.out.information( i.getDesc() )
                            self._already_reported_interesting.append( ( word, response.getURL() ) )
                    
                    html_in_comment = re.search('<[a-zA-Z]*.*?>.*?</[a-zA-Z]>', comment)
                    if html_in_comment and \
                    ( comment, response.getURL() ) not in self._already_reported_interesting:
                        # There is HTML code in the comment.
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('HTML comment contains HTML code')
                        desc = 'A comment with the string "' +comment + '" was found in: "'
                        desc += response.getURL() + '" . This could be interesting.'
                        i.setDesc( desc )
                        i.setId( response.id )
                        i.setDc( request.getDc )
                        i.setURI( response.getURI() )
                        i.addToHighlight( html_in_comment.group(0) )
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
        @return: None
        '''
        inform = []
        for comment in self._comments.keys():
            urls_with_this_comment = self._comments[comment]
            stick_comment = ' '.join(comment.split())
            if len(stick_comment) > 40:
                msg = 'A comment with the string "%s..." (and %s more bytes) was found on these URL(s):' % (stick_comment[:40], str(len(stick_comment) - 40))
                om.out.information( msg )
            else:
                msg = 'A comment containing "%s" was found on these URL(s):' % (stick_comment)
                om.out.information( msg )
             
            for url , request_id in urls_with_this_comment:
                inform.append('- ' + url + ' (request with id: '+str(request_id)+')' )
        
            inform.sort()
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
        This plugin greps every page for HTML comments, special comments like the ones containing
        the words "password" or "user" are specially reported.
        '''
