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

import lxml.etree as etree

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.constants.severity as severity

from w3af import ROOT_PATH
from w3af.core.data.parsers.url import URL
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.esmre.esm_multi_in import esm_multi_in
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
                                'index.xml')

    def __init__(self):
        CrawlPlugin.__init__(self)

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request):
        """
        Plugin entry point, performs all the work.
        """
        to_check = self._get_to_check(fuzzable_request.get_url())

        # I found some URLs, create fuzzable requests
        pt_handler = self._is_in_phishtank(to_check)

        for ptm in pt_handler.matches:
            fr = FuzzableRequest(ptm.url)
            self.output_queue.put(fr)

        # Only create the vuln object once
        if pt_handler.matches:
            desc = 'The URL: "%s" seems to be involved in a phishing scam.' \
                   ' Please see %s for more info.'
            desc = desc % (ptm.url, ptm.more_info_url)

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
            # According to different sources, xml.sax knows how to handle
            # encoding, so it will simply decode using the header:
            #
            # <?xml version="1.0" encoding="utf-8"?>
            phishtank_db_fd = file(self.PHISHTANK_DB, 'r')
        except Exception, e:
            msg = 'Failed to open phishtank database: "%s", exception: "%s".'
            raise BaseFrameworkException(msg % (self.PHISHTANK_DB, e))

        pt_handler = PhishTankHandler(to_check)
        parser = etree.HTMLParser(recover=True, target=pt_handler)

        om.out.debug('Starting the phishtank XML parsing. ')

        try:
            etree.parse(phishtank_db_fd, parser)
        except Exception, e:
            msg = 'XML parsing error in phishtank DB, exception: "%s".'
            raise BaseFrameworkException(msg % e)

        om.out.debug('Finished XML parsing. ')

        return pt_handler

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


class PhishTankHandler(object):
    """
    <entry>
        <url><![CDATA[http://cbisis...paypal.support/]]></url>
        <phish_id>118884</phish_id>
        <phish_detail_url>
            <![CDATA[http://www.phishtank.com/phish_detail.php?phish_id=118884]]>
        </phish_detail_url>
        <submission>
            <submission_time>2007-03-03T21:01:19+00:00</submission_time>
        </submission>
        <verification>
            <verified>yes</verified>
            <verification_time>2007-03-04T01:58:05+00:00</verification_time>
        </verification>
        <status>
            <online>yes</online>
        </status>
    </entry>
    """
    def __init__(self, to_check):
        self._to_check = to_check
        self._to_check_esm = esm_multi_in(to_check)

        self.url = u''
        self.phish_detail_url = u''
        
        self.inside_entry = False
        self.inside_URL = False
        self.url_count = 0
        self.inside_detail = False
        
        self.matches = []

    def start(self, name, attrs):
        if name == u'entry':
            self.inside_entry = True

        elif name == u'url':
            self.inside_URL = True
            self.url = u''

        elif name == u'phish_detail_url':
            self.inside_detail = True
            self.phish_detail_url = u''

        return

    def data(self, ch):
        if self.inside_URL:
            self.url += ch

        if self.inside_detail:
            self.phish_detail_url += ch

    def end(self, name):
        if name == u'phish_detail_url':
            self.inside_detail = False

        if name == u'url':
            self.inside_URL = False
            self.url_count += 1

        if name == u'entry':
            self.inside_entry = False
            #
            #    Now I try to match the entry with an element in the
            #    to_check_list
            #
            query_result = self._to_check_esm.query(self.url)

            if query_result:
                phish_url = URL(self.url)
                target_host_url = URL(query_result[0])

                if target_host_url.get_domain() == phish_url.get_domain() or \
                phish_url.get_domain().endswith('.' + target_host_url.get_domain()):

                    phish_detail_url = URL(self.phish_detail_url)
                    ptm = PhishTankMatch(phish_url, phish_detail_url)
                    self.matches.append(ptm)

    def close(self):
        return self.matches
