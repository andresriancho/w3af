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
import threading
import core.data.kb.knowledgeBase as kb

update_lock = threading.RLock()


def update_kb( fuzzable_request ):
    '''
    Updates the URL and fuzzable request list in the kb for other plugins to 
    use.
    '''
    with update_lock:
        # Update the list of URLs that is used world wide, it is VERY
        # important to notice that we always need to append stuff to the
        # end of this list and avoid things like sorting, inserting in
        # positions different than the tail, etc. This helps with the
        # implementation of scanrun.IteratedURLList .
        #
        # TODO: Force this somehow so that this isn't just a warning but
        # something that fails if developers change it.
        url_object_list = get_urls_from_kb()
        if fuzzable_request.getURL() not in url_object_list:
    
            url_object_list.append( fuzzable_request.getURL() )
            kb.kb.save( 'urls', 'url_objects', url_object_list )
    
        # Update the list of fuzzable requests that lives in the KB
        # TODO: Move the whole KB to a sqlite database in order to save
        #       some memory usage.
        kb_fr_set = get_fuzzable_requests_from_kb()
        kb_fr_set.add( fuzzable_request )

def get_urls_from_kb():
    return kb.kb.getData( 'urls', 'url_objects' )
    
def get_fuzzable_requests_from_kb():
    return kb.kb.getData( 'urls', 'fuzzable_requests' )
        