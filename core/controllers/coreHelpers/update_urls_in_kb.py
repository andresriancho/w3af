'''
update_URLs_in_KB.py

Copyright 2012 Andres Riancho

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
import core.data.kb.knowledgeBase as kb


def update_URLs_in_KB( fuzzable_request_list ):
    '''
    Updates the URL list in the kb for other plugins to use.
    
    >>> from core.data.parsers.urlParser import url_object
    >>> from core.data.request.fuzzableRequest import fuzzableRequest
    >>> kb.kb.save('url', 'url_objects', [])

    >>> u1 = url_object('http://w3af.org/')
    >>> r1 = fuzzableRequest(u1, method='GET')
    >>> update_URLs_in_KB( [r1,] )
    >>> kb.kb.getData('url', 'url_objects')
    [<url_object for "http://w3af.org/">]

    >>> u2 = url_object('http://w3af.org/blog/')
    >>> r2 = fuzzableRequest(u2, method='GET')    
    >>> u3 = url_object('http://w3af.org/')
    >>> r3 = fuzzableRequest(u3, method='GET')    
    >>> update_URLs_in_KB( [r1,r2,r3] )
    >>> kb.kb.getData('url', 'url_objects')
    [<url_object for "http://w3af.org/">, <url_object for "http://w3af.org/blog/">]
    
    '''
    url_object_list = kb.kb.getData( 'url', 'url_objects' )
    new_list = [ fr.getURL() for fr in fuzzable_request_list \
                 if fr.getURL() not in url_object_list ]

    # Update the list of URLs that is used world wide, it is VERY
    # important to notice that we always need to append stuff to the
    # end of this list and avoid things like sorting, inserting in
    # positions different than the tail, etc. This helps with the
    # implementation of scanrun.IteratedURLList .
    #
    # TODO: Force this somehow so that this isn't just a warning but
    # something that fails if developers change it.
    url_object_list.extend( new_list )
    kb.kb.save( 'urls', 'url_objects' ,  url_object_list )

