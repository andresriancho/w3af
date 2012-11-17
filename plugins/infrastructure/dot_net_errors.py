'''
dot_net_errors.py

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
import core.data.kb.knowledge_base as kb
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter


class dot_net_errors(InfrastructurePlugin):
    '''
    Request specially crafted URLs that generate ASP.NET errors in order
    to gather information.

    @author: Andres Riancho ((andres.riancho@gmail.com))
    '''

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Internal variables
        self._already_tested = ScalableBloomFilter()
        # On real web applications, if we can't trigger an error in the first
        # MAX_TESTS tests, it simply won't happen and we have to stop testing.
        self.MAX_TESTS = 25

    def discover(self, fuzzable_request):
        '''
        Requests the special filenames.

        @param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        if len(self._already_tested) < self.MAX_TESTS \
                and fuzzable_request.getURL() not in self._already_tested:
            self._already_tested.add(fuzzable_request.getURL())

            test_generator = self._generate_URLs(fuzzable_request.getURL())

            self._tm.threadpool.map(self._send_and_check,
                                    test_generator,
                                    chunksize=1)

    def _generate_URLs(self, original_url):
        '''
        Generate new URLs based on original_url.

        @param original_url: The original url that has to be modified in
                                 order to trigger errors in the remote application.
        '''
        special_chars = ['|', '~']

        filename = original_url.getFileName()
        if filename != '' and '.' in filename:
            splitted_filename = filename.split('.')
            extension = splitted_filename[-1:][0]
            name = '.'.join(splitted_filename[0:-1])

            for char in special_chars:
                new_filename = name + char + '.' + extension
                new_url = original_url.urlJoin(new_filename)
                yield new_url

    def _send_and_check(self, url):
        '''
        @param response: The HTTPResponse object that holds the content of
                             the response to analyze.
        '''
        response = self._uri_opener.GET(url, cache=True)

        viewable_remote_machine = '<b>Details:</b> To enable the details of this'
        viewable_remote_machine += ' specific error message to be viewable on'
        viewable_remote_machine += ' remote machines'

        if viewable_remote_machine not in response.body\
                and '<h2> <i>Runtime Error</i> </h2></span>' in response.body:
            v = vuln.vuln(response)
            v.set_plugin_name(self.get_name())
            v.set_id(response.id)
            v.set_severity(severity.LOW)
            v.set_name('Information disclosure via .NET errors')
            msg = 'Detailed information about ASP.NET error messages can be'
            msg += ' viewed from remote sites. The URL: "%s" discloses detailed'
            msg += ' error messages.'
            v.set_desc(msg % response.getURL())
            kb.kb.append(self, 'dot_net_errors', v)

    def get_plugin_deps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['grep.error_pages']

    def get_long_desc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        Request specially crafted URLs that generate ASP.NET errors in order to
        gather information like the ASP.NET version. Some examples of URLs that
        generate errors are:
            - default|.aspx
            - default~.aspx
        '''
