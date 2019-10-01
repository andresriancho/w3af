"""
dot_net_errors.py

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

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.vuln import Vuln


class dot_net_errors(InfrastructurePlugin):
    """
    Request specially crafted URLs that generate ASP.NET errors in order
    to gather information.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    SPECIAL_CHARS = ['|', '~']

    RUNTIME_ERROR = '<h2> <i>Runtime Error</i> </h2></span>'
    REMOTE_MACHINE = ('<b>Details:</b> To enable the details of this'
                      ' specific error message to be viewable on'
                      ' remote machines')

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._already_tested = ScalableBloomFilter()

        # On real web applications, if we can't trigger an error in the first
        # MAX_TESTS tests, it simply won't happen and we have to stop testing.
        self.MAX_TESTS = 25

    def discover(self, fuzzable_request, debugging_id):
        """
        Requests the special filenames.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        if len(self._already_tested) >= self.MAX_TESTS:
            return

        if fuzzable_request.get_url() in self._already_tested:
            return

        self._already_tested.add(fuzzable_request.get_url())

        self.worker_pool.map(self._send_and_check,
                             self._generate_urls(fuzzable_request.get_url()),
                             chunksize=1)

    def _generate_urls(self, original_url):
        """
        Generate new URLs based on original_url.

        :param original_url: The original url that has to be modified in
                             order to trigger errors in the remote application.
        """
        filename = original_url.get_file_name()

        if not filename:
            return

        if '.' not in filename:
            return

        split_filename = filename.split('.')
        extension = split_filename[-1:][0]
        name = '.'.join(split_filename[0:-1])

        for char in self.SPECIAL_CHARS:
            new_filename = name + char + '.' + extension

            try:
                new_url = original_url.url_join(new_filename)
            except ValueError:
                # When the filename has a colon the url_join() will fail with
                # ValueError
                continue

            yield new_url

    def _send_and_check(self, url):
        response = self._uri_opener.GET(url, cache=True)

        if self.RUNTIME_ERROR not in response.body:
            return

        if self.REMOTE_MACHINE in response.body:
            return

        desc = ('Detailed information about ASP.NET error messages can be'
                ' viewed from remote clients. The URL: "%s" discloses'
                ' detailed error messages.')
        desc %= response.get_url()

        v = Vuln('Information disclosure via .NET errors',
                 desc,
                 severity.LOW,
                 response.id,
                 self.get_name())

        kb.kb.append(self, 'dot_net_errors', v)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['grep.error_pages']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        Request specially crafted URLs that generate ASP.NET errors in order to
        gather information like the ASP.NET version. Some examples of URLs that
        generate errors are:
        
            - default|.aspx
            - default~.aspx
        """
