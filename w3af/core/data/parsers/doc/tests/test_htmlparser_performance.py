# -*- coding: UTF-8 -*-
"""
test_htmlparser_performance.py

Copyright 2015 Andres Riancho

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
import unittest
import resource
import time
import os

from nose.plugins.attrib import attr
from memory_profiler import profile

from w3af import ROOT_PATH
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.dc.headers import Headers
from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.tests.generate_html_file import OUTPUT_FILE


class TestHTMLParserPerformance(unittest.TestCase):

    MEMORY_DUMP = 'manual-analysis-%s.dump'

    HTML_FILE = os.path.join(ROOT_PATH, 'core', 'data', 'context', 'tests',
                             'samples', 'django-500.html')

    @attr('ci_ignore')
    def test_parse_html_performance(self):
        headers = Headers()
        headers['content-type'] = 'text/html'
        body = file(self.HTML_FILE).read()
        url = URL('http://www.w3af.org/')
        response = HTTPResponse(200, body, headers, url, url, charset='utf-8')

        #self.measure_memory(1)

        parsers = []

        for _ in xrange(40):
            p = HTMLParser(response)
            p.parse()
            #parsers.append(p)

        # Clear any reference to the parser
        #del p
        #parsers = []

        #self.measure_memory(2)

        time.sleep(360)

    def measure_memory(self, _id):
        # pylint: disable=E0401
        from meliae import scanner, loader
        # pylint: enable=E0401
        scanner.dump_all_objects(self.MEMORY_DUMP % _id)

        om = loader.load(self.MEMORY_DUMP % _id)
        om.remove_expensive_references()
        summary = om.summarize()

        print summary

        #print('runsnakemem %s' % self.MEMORY_DUMP)

        usage = resource.getrusage(resource.RUSAGE_SELF)
        print 'maximum resident set size', usage.ru_maxrss
        print 'shared memory size', usage.ru_ixrss
        print 'unshared memory size', usage.ru_idrss
        print 'unshared stack size', usage.ru_isrss

        import psutil
        self_pid = psutil.Process()
        # pylint: disable=E1101
        print self_pid.memory_info()


def test():
    """
    Run using:
        python -m memory_profiler w3af/core/data/parsers/tests/test_htmlparser_performance.py

    That will activate the profiler.
    """
    body = file(OUTPUT_FILE).read()
    url = URL('http://www.clarin.com.ar/')
    headers = Headers()
    headers['content-type'] = 'text/html'
    response = HTTPResponse(200, body, headers, url, url, charset='utf-8')

    p = HTMLParser(response)
    del p


if __name__ == '__main__':
    test()
