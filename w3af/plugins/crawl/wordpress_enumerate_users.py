"""
wordpress_username_enumeration.py

Copyright 2011 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import re

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.info import Info


class wordpress_enumerate_users(CrawlPlugin):
    """
    Finds users in a WordPress installation.
    :author: Andres Tarantini ( atarantini@gmail.com )
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._exec = True

    def crawl(self, fuzzable_request, debugging_id):
        """
        Find users in a WordPress installation

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if not self._exec:
            raise RunOnce()

        # Check if there is a wordpress installation in this directory
        domain_path = fuzzable_request.get_url().get_domain_path()
        wp_unique_url = domain_path.url_join('wp-login.php')
        response = self._uri_opener.GET(wp_unique_url, cache=True)

        if is_404(response):
            return

        self._enum_users(fuzzable_request)

    def _enum_users(self, fuzzable_request):
        # Only run once
        self._exec = False

        # First user ID, will be incremented until 404
        uid = 0

        # Save the last title for non-redirection scenario
        self._title_cache = ''

        # Tolerance for user ID gaps in the sequence (this gaps are present
        # when users are deleted and new users created)
        gap_tolerance = 10
        gap = 0

        domain_path = fuzzable_request.get_url().get_domain_path()

        # Loop into authors and increment user ID
        while gap <= gap_tolerance:

            uid += 1
            gap += 1

            domain_path.querystring = [(u'author', [u'%s' % uid])]
            wp_author_url = domain_path
            response_author = self._uri_opener.GET(wp_author_url, cache=True)

            if is_404(response_author):
                continue

            if response_author.was_redirected():
                extracted_from_redir = self._extract_from_redir(response_author)

                if extracted_from_redir:
                    gap = 0
                    continue

            extracted_from_body = self._extract_from_body(response_author)
            if extracted_from_body:
                gap = 0
                continue

    def _extract_from_body(self, response_author):
        """No redirect was made, try to fetch username from
        title of the author's archive page"""
        # Example strings:
        #    <title>admin | moth</title>
        #    <title>admin | Bonsai - Information Security Blog</title>
        title_search = re.search('<title>(.*?)</title>',
                                 response_author.get_body(), re.I)
        if title_search:
            title = title_search.group(1)
            # If the title is the same than the last user
            # ID requested, there are no new users
            if title == self._title_cache:
                return False
            else:
                # The title changed, username probably found
                self._title_cache = title
                username = title.split(' ')[0]
                self._kb_info_user(response_author.get_url(),
                                   response_author.id, username)
                return True

        return False

    def _extract_from_redir(self, response_author):
        path = response_author.get_redir_uri().get_path()
        if 'author' in path:
            # A redirect to /author/<username> was made, username probably found
            username = path.split("/")[-2]
            self._kb_info_user(response_author.get_uri(),
                               response_author.id, username)

            return True

        return False

    def _kb_info_user(self, url, response_id, username):
        """
        Put user in Kb
        :return: None, everything is saved in kb
        """
        desc = 'WordPress user "%s" found during username enumeration.'
        desc = desc % username
        
        i = Info('Identified WordPress user', desc, response_id,
                 self.get_name())
        i.set_url(url)
        
        kb.kb.append(self, 'users', i)
        om.out.information(i.get_desc())

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds user names in WordPress installations.

        The author's archive page is tried using "?author=ID" query and 
        incrementing the ID for each request until a 404 response is received.
        
        If the response is a redirect, the blog is affected by TALSOFT-2011-0526
        (http://seclists.org/fulldisclosure/2011/May/493) advisory. If no
        redirect is done, the plugin will try to fetch the username from title.
        """
