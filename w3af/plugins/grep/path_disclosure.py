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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
import w3af.core.data.parsers.parser_cache as parser_cache

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.quick_match.multi_re import MultiRE
from w3af.core.data.constants.common_directories import get_common_directories


class path_disclosure(GrepPlugin):
    """
    Grep every page for traces of path disclosure vulnerabilities.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        GrepPlugin.__init__(self)

        # Internal variables
        self._reported = DiskList(table_prefix='path_disclosure')
        self._signature_re = None

    def setup(self):
        """
        :return: None, the result is saved in self._path_disc_regex_list
        """
        if self._signature_re is not None:
            return

        all_signatures = []

        for common_directory in get_common_directories():
            regex_string = '[^A-Za-z0-9\._\-\\/\+~](%s.*?)[^A-Za-z0-9\._\-\\/\+~]'
            regex_string = regex_string % common_directory
            all_signatures.append(regex_string)
            
        self._signature_re = MultiRE(all_signatures, hint_len=1)

    def grep(self, request, response):
        """
        Identify the path disclosure vulnerabilities.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None, the result is saved in the kb.
        """
        if not response.is_text_or_html():
            return

        self.setup()

        if self.find_path_disclosure(request, response):
            self._update_kb_path_list()

    def find_path_disclosure(self, request, response):
        """
        Actually find the path disclosure vulnerabilities
        """
        match_list = []
        body_text = response.get_body()
        real_url = response.get_url().url_decode()

        for match, _, _ in self._signature_re.query(body_text):
            match_list.append(match.group(1))

        # Sort by the longest match, this is needed for filtering out
        # some false positives. Please read the note below.
        match_list.sort(longest_cmp)

        for match in match_list:
            # Avoid duplicated reports
            if (real_url, match) in self._reported:
                continue

            # Remove false positives
            if self._is_false_positive(match, request, response):
                continue

            # Found!
            self._reported.append((real_url, match))

            desc = 'The URL: "%s" has a path disclosure vulnerability which discloses "%s".'
            desc %= (response.get_url(), match)

            v = Vuln('Path disclosure vulnerability', desc, severity.LOW,
                     response.id, self.get_name())
            v.add_to_highlight(match)
            v.set_url(real_url)
            v['path'] = match

            self.kb_append(self, 'path_disclosure', v)
            return v

    def _is_false_positive(self, match, request, response):
        """
        :return: True if the match is a false positive
        """
        # This if is to avoid false positives
        if request.sent(match):
            return True

        # https://github.com/andresriancho/w3af/issues/6640
        url_list = kb.kb.get_all_known_urls()

        for url in url_list:
            path_and_file = url.get_path()
            if match == path_and_file:
                return True

        # There is a rare bug also, which is triggered in cases like this one:
        #
        #   >>> import re
        #
        #   >>> re.findall('/var/www/.*','/var/www/foobar/htdocs/article.php')
        #   ['/var/www/foobar/htdocs/article.php']
        #
        #   >>> re.findall('/htdocs/.*','/var/www/foobar/htdocs/article.php')
        #   ['/htdocs/article.php']
        #
        # What I need to do here, is to keep the longest match.
        for real_url_reported, match_reported in self._reported:
            if match_reported.endswith(match):
                return True

        # Check if the match we got is part of a tag attribute value
        #
        # This part of the function is the one that consumes the most CPU usage
        # thus we run it last, hoping that at least one of the methods we
        # implemented above tags this match as a false positive and we don't
        # have to run the expensive method
        if self._is_attr_value(match, response):
            return True

        return False

    def _is_attr_value(self, path_disclosure_string, response):
        """
        This method was created to remove some false positives.

        This method consumes 99% of the CPU usage of the plugin, but there
        are only a few improvements that come to mind:

            * Run the code that checks if the value is in the attributes
              in the subprocess. The performance of this plugin will be
              slightly improved.

            * Before calling the document parser check at least it looks like
              the path_disclosure_string is part of an attribute value using
              a regular expression such as [1]:

                </?\w+((\s+\w+(\s*=\s*(?:".*?"|'.*?'|[\^'">\s]+))?)+\s*|\s*)/?>

                (I just need to add the path_disclosure_string somewhere there)

              At some point I was using a similar approach [0] but it seems
              that it was slow? (I doubt that it will be slower than parsing
              the response with lxml).

              Something that could be done, and given that we know that this
              is an HTML string is:

                - Find all places in the response where path_disclosure_string
                  appears

                - Create 'HTTP response snippets' with the locations of
                  path_disclosure_string +/- 500 strings.

                - Apply the regular expression over those strings only, avoiding
                  the cost of applying the regex to the whole HTML response

        [0] https://github.com/andresriancho/w3af/commit/f1029328fcaf7e790cc317701b63954c55a3f4c8
        [1] https://haacked.com/archive/2004/10/25/usingregularexpressionstomatchhtml.aspx/

        :return: True if path_disclosure_string is the value of an attribute
                 inside a tag.

        Examples:
            path_disclosure_string = '/home/image.png'
            response_body = '....<img src="/home/image.png">...'
            return: True

            path_disclosure_string = '/home/image.png'
            response_body = '...<b>Error while checking /home/image.png</b>...'
            return: False
        """
        for tag in parser_cache.dpc.get_tags_by_filter(response, None):
            for value in tag.attrib.itervalues():
                if path_disclosure_string in value:
                    return True

        return False

    def _update_kb_path_list(self):
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
        self._reported.cleanup()

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


def longest_cmp(a, b):
    return cmp(len(b), len(a))
