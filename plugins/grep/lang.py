'''
lang.py

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
from __future__ import with_statement

import core.controllers.outputManager as om
import core.data.kb.knowledgeBase as kb

from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.data.esmre.multi_in import multi_in

def whole_words(l):
    return [' %s ' % w for w in l ]

class lang(baseGrepPlugin):
    '''
    Read N pages and determines the language the site is written in.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    PREPOSITIONS = { 'en': multi_in(whole_words(['aboard', 'about', 'above',
                                     'absent', 'across', 'after', 'against', 'along',
                                     'alongside', 'amid', 'amidst', 'among',
                                     'amongst', 'around', 'as', 'astride', 'at',
                                     'atop', 'before', 'behind', 'below',
                                     'beneath', 'beside', 'besides', 'between',
                                     'beyond', 'but', 'by', 'despite', 'down',
                                     'during', 'except', 'following', 'for', 
                                     'from', 'in', 'inside', 'into', 'like',
                                     'mid', 'minus', 'near', 'nearest', 'notwithstanding',
                                     'of', 'off', 'on', 'onto', 'opposite', 'out',
                                     'outside', 'over', 'past', 're', 'round',
                                     'save', 'since', 'than', 'through', 'throughout',
                                     'till', 'to', 'toward', 'towards', 'under',
                                     'underneath', 'unlike', 'until', 'up', 
                                     'upon', 'via', 'with', 'within', 'without'])),
                    
                    # The 'a' preposition was removed, cause its also used in english
                     'es': multi_in(whole_words(['ante', 'bajo', 'cabe', 'con' , 
                                     'contra', 'de', 'desde', 'en', 'entre', 'hacia',
                                     'hasta', 'para', 'por' , 'segun', 'si',
                                     'so', 'sobre', 'tras'])),
                    
                    # Turkish
                    # Sertan Kolat <sertan@gmail.com>
                     'tr': multi_in(whole_words(['ancak', 'burada', 'duyuru', 'evet', 
                                     'fakat', 'gibi', 'haber', 'kadar', 'karar', 'kaynak',
                                     'olarak', 'sayfa', 'siteye', 'sorumlu', 
                                     'tamam', 'yasak', 'zorunlu'])),
                     }

    def __init__(self):
        baseGrepPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        
    def grep(self, request, response):
        '''
        Get the page indicated by the fuzzable_request and determine the language
        using the preposition list.
        
        @parameter request: The HTTP request object.
        @parameter response: The HTTP response object
        '''
        with self._plugin_lock:
            if self._exec and not is_404( response ) and response.is_text_or_html():
                kb.kb.save( self, 'lang', 'unknown' )
                
                matches = {}
                body = response.getClearTextBody().lower()
                
                for lang_string, m_in_obj in self.PREPOSITIONS.iteritems():
                    matches[ lang_string ] = len( m_in_obj.query(body) )
                            
                # Determine who is the winner
                def sortfunc(x,y):
                    return cmp(y[1],x[1])
                    
                items = matches.items()
                items.sort( sortfunc )
                
                if items[0][1] > items[1][1] * 2:
                    # Only run once
                    self._exec = False
                    identified_lang = items[0][0]
                    om.out.information('The page is written in: "%s".' % identified_lang )
                    kb.kb.save( self, 'lang', identified_lang )
                
                else:
                    msg = 'Could not determine the page language using ' + response.getURL() 
                    msg += ', not enough text to make a good analysis.'
                    om.out.debug(msg)
                    # Keep running until giving a good response...
                    self._exec = True
    
    def end( self ):
        if self._exec:
            # I never got executed !
            om.out.information('Could not determine the language of the site.')
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin reads N pages and determines the language the site is written
        in. This is done by saving a list of prepositions in different languages,
        and counting the number of matches on every page.
        '''
