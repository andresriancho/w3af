'''
wordpress_username_enumeration.py

Copyright 2011 Andres Riancho

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

# Import options
import re

from core.data.options.option_list import OptionList

from core.controllers.plugins.crawl_plugin import CrawlPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.w3afException import w3afRunOnce
from core.controllers.core_helpers.fingerprint_404 import is_404


# Main class
class wordpress_enumerate_users(CrawlPlugin):
    '''
    Finds users in a WordPress installation.
    @author: Andres Tarantini ( atarantini@gmail.com )
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._exec = True

    def crawl(self, fuzzable_request):
        '''
        Find users in a WordPress installation
        @parameter fuzzable_request: A fuzzable_request instance that contains
        (among other things) the URL to test.
        '''
        uid = 1           # First user ID, will be incremented until 404
        redirect = False  # Store if redirection was success
        title_cache = ""  # Save the last title for non-redirection scenario
        gap_tolerance = 10 # Tolerance for user ID gaps in the sequence (this gaps are present when users are deleted and new users created)
        gap = 0

        if not self._exec :
            # Remove the plugin from the crawl plugins to be run.
            raise w3afRunOnce()
        else:
            # Check if the server is running WordPress
            domain_path = fuzzable_request.getURL().getDomainPath()
            wp_unique_url = domain_path.urlJoin( 'wp-login.php' )
            response = self._uri_opener.GET( wp_unique_url, cache=True )

            # If wp_unique_url is not 404, wordpress = true
            if not is_404( response ):
                # Loop into authors and increment user ID
                while (gap <= gap_tolerance):
                    domain_path.querystring = {u'author': u'%s' % uid}
                    wp_author_url = domain_path
                    response_author = self._uri_opener.GET(wp_author_url, cache=True)
                    if not is_404( response_author ):
                        path = response_author.getRedirURI().getPath()
                        if 'author' in path:
                            # A redirect to /author/<username> was made, username probably found
                            username = path.split("/")[-2]
                            redirect = True
                            self._kb_info_user(self.getName(), wp_author_url, response_author.id, username)
                            gap = 0
                        elif response_author.getURI() == wp_author_url and redirect is False:
                            # No redirect was made, try to fetch username from
                            # title of the author's archive page
                            title_search = re.search('<title>(.*)</title>', response_author.getBody(), re.IGNORECASE)
                            if title_search:
                                title =  title_search.group(1)
                                # If the title is the same than the last user
                                # ID requested, there are no new users
                                if title == title_cache:
                                    gap += 1
                                else:
                                    # The title changed, username probably found
                                    title_cache = title
                                    username = title.split()[0]
                                    self._kb_info_user(self.getName(), wp_author_url, response_author.id, username)
                                    gap = 0

                        gap += 1
                    else:
                        # 404 error
                        gap += 1

                    uid = uid + 1

        # Only run once
        self._exec = False

    def _kb_info_user(self, p_name, url, response_id, username):
        '''
        Put user in Kb
        @return: None, everything is saved in kb
        '''
        i = info.info()
        i.setPluginName(p_name)
        i.setName('WordPress user "'+ username +'" found')
        i.setURL( url )
        i.setId( response_id )
        i.setDesc( 'WordPress user "'+ username +'" found from enumeration.' )
        kb.kb.append( self, 'info', i )
        om.out.information( i.getDesc() )

    # W3af options and output
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        return ol

    def set_options( self, option_list ):
        '''
        This method sets all the options that are configured using the user interface
        generated by the framework using the result of get_options().

        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        pass

    def get_plugin_deps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds usernames in a WordPress installation using "?author=ID" query.

        The author's archive page is tried using "?author=ID" query and incrementing the
        ID for each request until 404. If the response is a redirect, the blog is affected
        by TALSOFT-2011-0526 (http://seclists.org/fulldisclosure/2011/May/493) advisory. If
        no redirect is done, the plugin will try to fetch the username from title.

        The plugin will not be aware of gaps between two user IDs, this is a known issue.
        '''