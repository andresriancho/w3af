'''
webroot.py

Copyright 2008 Andres Riancho

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
from core.data.parsers.urlParser import url_object
import core.data.kb.knowledgeBase as kb


def get_webroot_dirs( domain=None ):
    '''
    @return: A list of strings with possible webroots. This function also analyzed the contents of the
    knowledgeBase and tries to use that information in order to guess.
    '''
    result = []
    
    # This one has more probability of success that all the other ones together
    obtained_webroot = kb.kb.getData( 'pathDisclosure', 'webroot' )
    if obtained_webroot:
        result.append(obtained_webroot)
    
    if domain:
        root_domain = url_object( 'http://' + domain ).getRootDomain()
        
        result.append('/var/www/' +  domain )
        result.append( '/var/www/' + domain + '/www/' )
        result.append( '/var/www/' + domain + '/html/' )
        result.append( '/var/www/' + domain + '/htdocs/' )
        
        result.append( '/home/' + domain )
        result.append( '/home/' + domain + '/www/' )
        result.append( '/home/' + domain + '/html/' )
        result.append( '/home/' + domain + '/htdocs/' )
        
        if domain != root_domain:
            result.append( '/home/' + root_domain )
            result.append( '/home/' + root_domain + '/www/' )
            result.append( '/home/' + root_domain + '/html/' )
            result.append( '/home/' + root_domain + '/htdocs/' )
            result.append('/var/www/' +  root_domain )
            result.append( '/var/www/' + root_domain + '/www/' )
            result.append( '/var/www/' + root_domain + '/html/' )
            result.append( '/var/www/' + root_domain + '/htdocs/' )            
    
    result.append('/var/www/')
    result.append('/var/www/html/')
    result.append('/var/www/htdocs/')
    
    return result
    
    
