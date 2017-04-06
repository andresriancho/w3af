"""
webapp_detection.py

Copyright 2015 Piotr Lizonczyk

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
from wad.detection import Detector
from wad.output import HumanReadableOutput

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.data.kb.info import Info


class w3afDetector(Detector):
    """
    This class overrides some getter functions in original Detector class
    in order to use w3af's ExtendedUrllib.
    """
    def __init__(self, uri_opener):
        super(w3afDetector, self).__init__()
        self._uri_opener = uri_opener
        self.original_response = None

    def get_page(self, url, timeout=None):
        # timeout is not used as w3af urlopener already has configurable timeout
        # through http-settings
        self.original_response = self._uri_opener.GET(url, cache=True)
        return self.original_response

    def get_new_url(self, page):
        return page.get_url().url_string

    def get_content(self, page, url):
        return page.get_body()


class application_fingerprint(InfrastructurePlugin):
    """
    Identify technologies used by website based on HTTP response
     and HTML content

    :author: Piotr Lizonczyk (piotr.lizonczyk@gmail.com)
    """
    def __init__(self):
        InfrastructurePlugin.__init__(self)
        self.detector = None

    @runonce(exc_class=RunOnce)
    def discover(self, fuzzable_request):
        """
        It calls the "main" from WAD and writes the results to the kb.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        self._main(fuzzable_request)

    def _main(self, fuzzable_request):
        """
        Based on WAD's main executable
        """
        self.detector = w3afDetector(uri_opener=self._uri_opener)
        results = self.detector.detect(fuzzable_request.get_url())

        self._report(results)

    def _report(self, results):
        """
        Displays detailed report information to the user and save the data to
        the kb.

        :return: None.
        """
        if results:
            i = Info('Application fingerprint',
                     HumanReadableOutput().retrieve(results),
                     self.detector.original_response.id,
                     self.get_name())

            kb.kb.append(self, 'Application fingerprint', i)

            # Also save this for easy internal use
            # other plugins can use this information
            kb.kb.raw_write(self, 'application_fingerprint', results)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to identify technology stack used on website
        by parsing HTTP response and HTML content.

        Results may include CMS, database, web server, frameworks,
        javascript plugins, operating systems and multiple other technologies.

        This plugin is a wrapper of CERN's CERT team's Web application detection
        (WAD) tool.
        """
