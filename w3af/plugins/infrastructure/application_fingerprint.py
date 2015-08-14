"""
application_fingerprint.py

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
import copy
from wad.detection import Detector
from wad.group import group
from wad.output import HumanReadableOutput

import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import NoMoreCalls
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
        self.knowledge = {}
        self.full_results = {}
        self.request_ids = []
        self.kb_info_id = None
        self.no_new_knowledge_count = 0

        # User configurable
        self.no_new_knowledge_count_max = 10

    def discover(self, fuzzable_request):
        """
        It calls the "main" from WAD and writes the results to the kb.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        result = self._main(fuzzable_request)
        if not result:
            return

        self.knowledge.update(result)
        self.full_results.update(result)
        self.request_ids.append(self.detector.original_response.id)

        new_knowledge = group(copy.deepcopy(self.knowledge))
        if new_knowledge != self.knowledge:
            self.no_new_knowledge_count = 0
            self.knowledge = new_knowledge
        else:
            self.no_new_knowledge_count += 1

        self._report()
        if self.no_new_knowledge_count >= self.no_new_knowledge_count_max:
            raise NoMoreCalls

    def _main(self, fuzzable_request):
        """
        Based on WAD's main executable
        """
        self.detector = w3afDetector(uri_opener=self._uri_opener)
        return self.detector.detect(fuzzable_request.get_url())

    def _report(self):
        """
        Displays detailed report information to the user and save the data to
        the kb.

        :return: None.
        """
        desc = HumanReadableOutput().retrieve(self.full_results)
        i = Info('Application fingerprint',
                 desc, self.request_ids, self.get_name())

        if not self.kb_info_id:
            kb.kb.append(self, 'Application fingerprint', i)
            self.kb_info_id = i.get_uniq_id()
        else:
            info = kb.kb.get_by_uniq_id(self.kb_info_id)
            new_info = copy.deepcopy(info)
            new_info.set_desc(desc)
            new_info.set_id(self.request_ids)
            kb.kb.update(info, new_info)
            self.kb_info_id = new_info.get_uniq_id()

        # Also save this for easy internal use
        # other plugins can use this information
        kb.kb.raw_write('application_fingerprint',
                        'application_fingerprint', self.full_results)

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
