"""
phishtank.py

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
import os.path
import socket
import csv

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity
from w3af import ROOT_PATH
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.quick_match.multi_in import MultiIn
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import RunOnce, BaseFrameworkException
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.misc.is_ip_address import is_ip_address


class phishtank(CrawlPlugin):
    """
    Search the phishtank.com database to determine if your server is (or was)
    being used in phishing scams.

    :author: Andres Riancho (andres.riancho@gmail.com)
    :author: Special thanks to http://www.phishtank.com/ !
    """
    PHISHTANK_DB = os.path.join(ROOT_PATH, 'plugins', 'crawl', 'phishtank',
                                'index.csv')

    def __init__(self):
        CrawlPlugin.__init__(self)
        self._multi_in = None

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request, debugging_id):
        """
        Plugin entry point, performs all the work.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        to_check = self._get_to_check(fuzzable_request.get_url())

        # I found some URLs, create fuzzable requests
        pt_matches = self._is_in_phishtank(to_check)

        if not pt_matches:
            return

        for ptm in pt_matches:
            fr = FuzzableRequest(ptm.url)
            self.output_queue.put(fr)

        desc = ('The URL: "%s" seems to be involved in a Phishing scam.'
                ' Please see %s for more info.')
        desc %= (ptm.url, ptm.more_info_url)

        v = Vuln('Phishing scam', desc, severity.MEDIUM, [], self.get_name())
        v.set_url(ptm.url)

        kb.kb.append(self, 'phishtank', v)
        om.out.vulnerability(v.get_desc(), severity=v.get_severity())

    def _get_to_check(self, target_url):
        """
        :param target_url: The url object we can use to extract some information
        :return: From the domain, get a list of FQDN, rootDomain and IP address.
        """
        def addrinfo(url):
            return [x[4][0] for x in socket.getaddrinfo(url.get_domain(), 0)]

        def getfqdn(url):
            return [socket.getfqdn(url.get_domain()), ]

        def root_domain(url):
            if not is_ip_address(url.get_domain()):
                return [url.get_root_domain(), ]
            
            return []

        res = set()
        for func in (addrinfo, getfqdn, root_domain):
            try:
                data_lst = func(target_url)
            except Exception:
                pass
            else:
                for data in data_lst:
                    res.add(data)

        return res

    def _is_in_phishtank(self, to_check):
        """
        Reads the phishtank db and tries to match the entries on that db with
        the to_check

        :return: A list with the sites to match against the phishtank db
        """
        try:
            phishtank_db_fd = file(self.PHISHTANK_DB, 'r')
        except Exception, e:
            msg = 'Failed to open phishtank database: "%s", exception: "%s".'
            raise BaseFrameworkException(msg % (self.PHISHTANK_DB, e))

        pt_matches = []
        self._multi_in = MultiIn(to_check)

        om.out.debug('Starting the phishtank CSV parsing.')

        pt_csv_reader = csv.reader(phishtank_db_fd, delimiter=' ',
                                   quotechar='|', quoting=csv.QUOTE_MINIMAL)

        for phishing_url, phishtank_detail_url in pt_csv_reader:
            pt_match = self._url_matches(phishing_url, phishtank_detail_url)
            if pt_match:
                pt_matches.append(pt_match)

        om.out.debug('Finished CSV parsing.')

        return pt_matches

    def _url_matches(self, phishing_url, phishtank_detail_url):
        """
        :param url: The url (as string) from the phishtank database
        :return: A PhishTankMatch if url matches what we're looking for, None
                 if there is no match
        """
        for query_result in self._multi_in.query(phishing_url):
            phish_url = URL(phishing_url)
            target_host_url = URL(query_result[0])

            if target_host_url.get_domain() == phish_url.get_domain() or \
            phish_url.get_domain().endswith('.' + target_host_url.get_domain()):

                phish_detail_url = URL(phishtank_detail_url)
                ptm = PhishTankMatch(phish_url, phish_detail_url)
                return ptm

        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches the domain being tested in the phishtank database.
        If your site is in this database the chances are that you were hacked
        and your server is now being used in phishing attacks.
        """


class PhishTankMatch(object):
    """
    Represents a phishtank match between the site I'm scanning and
    something in the index.xml file.
    """
    def __init__(self, url, more_info_url):
        self.url = url
        self.more_info_url = more_info_url
