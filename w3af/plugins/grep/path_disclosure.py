"""
path_disclosure.py

Copyright 2006 Andres Riancho

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

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.constants.common_directories import get_common_directories
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.db.disk_list import DiskList


class path_disclosure(GrepPlugin):
    """
    Grep every page for traces of path disclosure vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._already_added = DiskList()

        # Compile all regular expressions and store information to avoid
        # multiple queries to the same function
        self._common_directories = get_common_directories()
        self._compiled_regexes = {}
        self._compile_regex()

    def _compile_regex(self):
        """
        :return: None, the result is saved in self._path_disc_regex_list
        """
        #
        #    I tried to enhance the performance of this plugin by putting
        #    all the regular expressions in one (1|2|3|4...|N)
        #    That gave no visible result.
        #
        for path_disclosure_string in self._common_directories:
            regex_string = '(%s.*?)[^A-Za-z0-9\._\-\\/\+~]'
            regex_string = regex_string % path_disclosure_string
            regex = re.compile(regex_string, re.IGNORECASE)
            
            self._compiled_regexes[path_disclosure_string] = regex

    def _potential_disclosures(self, html_string):
        """
        Taking into account that regular expressions are slow, we first
        apply this function to check if the HTML string has potential
        path disclosures.

        With this performance enhancement we reduce the plugin run time
        to 1/8 of the time in cases where no potential disclosures are found,
        and around 1/3 when potential disclosures *are* found.

        :return: A list of the potential path disclosures
        """
        potential_disclosures = []

        for path_disclosure_string in self._common_directories:
            if path_disclosure_string in html_string:
                potential_disclosures.append(path_disclosure_string)

        return potential_disclosures

    def grep(self, request, response):
        """
        Identify the path disclosure vulnerabilities.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, the result is saved in the kb.
        """
        if not response.is_text_or_html():
            return
        
        if self.find_path_disclosure(request, response):
            self._update_KB_path_list()
        
    def find_path_disclosure(self, request, response):
        """
        Actually find the path disclosure vulnerabilities
        """
        html_string = response.get_body()

        for potential_disclosure in self._potential_disclosures(html_string):

            path_disc_regex = self._compiled_regexes[potential_disclosure]
            match_list = path_disc_regex.findall(html_string)

            # Decode the URL, this will transform things like
            #     http://host.tld/?id=%2Fhome
            # into,
            #     http://host.tld/?id=/home
            realurl = response.get_url().url_decode()

            #   Sort by the longest match, this is needed for filtering out
            #   some false positives please read the note below.
            match_list.sort(self._longest)

            for match in match_list:

                # This if is to avoid false positives
                if not request.sent(match) and not \
                self._attr_value(match, html_string):

                    # Check for dups
                    if (realurl, match) in self._already_added:
                        continue

                    #   There is a rare bug also, which is triggered in cases like this one:
                    #
                    #   >>> import re
                    #   >>> re.findall('/var/www/.*','/var/www/foobar/htdocs/article.php')
                    #   ['/var/www/foobar/htdocs/article.php']
                    #   >>> re.findall('/htdocs/.*','/var/www/foobar/htdocs/article.php')
                    #   ['/htdocs/article.php']
                    #   >>>
                    #
                    #   What I need to do here, is to keep the longest match.
                    for realurl_added, match_added in self._already_added:
                        if match_added.endswith(match):
                            break
                    else:

                        #   Note to self: I get here when "break" is NOT executed.
                        #   It's a new one, report!
                        self._already_added.append((realurl, match))

                        desc = 'The URL: "%s" has a path disclosure'\
                               ' vulnerability which discloses "%s".'
                        desc = desc % (response.get_url(), match)

                        v = Vuln('Path disclosure vulnerability', desc,
                                 severity.LOW, response.id, self.get_name())

                        v.set_url(realurl)
                        v['path'] = match
                        v.add_to_highlight(match)
                        
                        self.kb_append(self, 'path_disclosure', v)
                        return True
                    
        return False

    def _longest(self, a, b):
        """
        :param a: A string.
        :param a: Another string.
        :return: The longest string.
        """
        return cmp(len(a), len(b))

    def _attr_value(self, path_disclosure_string, response_body):
        """
        This method was created to remove some false positives.

        :return: True if path_disclosure_string is the value of an attribute inside a tag.

        Examples:
            path_disclosure_string = '/home/image.png'
            response_body = '....<img src="/home/image.png">...'
            return: True

            path_disclosure_string = '/home/image.png'
            response_body = '...<b>Error while processing /home/image.png</b>...'
            return: False
        """
        regex = '<.+?(["|\']%s["|\']).*?>' % re.escape(path_disclosure_string)
        regex_res = re.findall(regex, response_body)
        in_attr = path_disclosure_string in regex_res
        return in_attr

    def _update_KB_path_list(self):
        """
        If a path disclosure was found, I can create a list of full paths to
        all URLs ever visited. This method updates that list.
        """
        path_disc_vulns = kb.kb.get('path_disclosure', 'path_disclosure')
        url_list = kb.kb.get_all_known_urls()
        
        # Now I find the longest match between one of the URLs that w3af has
        # discovered, and one of the path disclosure strings that this plugin
        # has found. I use the longest match because with small match_list I
        # have more probability of making a mistake.
        longest_match = ''
        longest_path_disc_vuln = None
        for path_disc_vuln in path_disc_vulns:
            for url in url_list:
                path_and_file = url.get_path()

                if path_disc_vuln['path'].endswith(path_and_file):
                    if len(longest_match) < len(path_and_file):
                        longest_match = path_and_file
                        longest_path_disc_vuln = path_disc_vuln

        # Now I recalculate the place where all the resources are in disk, all
        # this is done taking the longest_match as a reference, so... if we
        # don't have a longest_match, then nothing is actually done
        if not longest_match:
            return

        # Get the webroot
        webroot = longest_path_disc_vuln['path'].replace(longest_match, '')

        #
        # This if fixes a strange case reported by Olle
        #         if webroot[0] == '/':
        #         IndexError: string index out of range
        # That seems to be because the webroot == ''
        #
        if not webroot:
            return
        
        # Check what path separator we should use (linux / windows)
        path_sep = '/' if webroot.startswith('/') else '\\'

        # Create the remote locations
        remote_locations = []
        for url in url_list:
            remote_path = url.get_path().replace('/', path_sep)
            remote_locations.append(webroot + remote_path)
        remote_locations = list(set(remote_locations))

        kb.kb.raw_write(self, 'list_files', remote_locations)
        kb.kb.raw_write(self, 'webroot', webroot)

    def end(self):
        self._already_added.cleanup()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin greps every page for path disclosure vulnerabilities like:

            - C:\\www\\files\...
            - /var/www/htdocs/...

        The results are saved to the KB, and used by all the plugins that need
        to know the location of a file inside the remote web server.
        """
