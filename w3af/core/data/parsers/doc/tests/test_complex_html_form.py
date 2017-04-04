# -*- coding: UTF-8 -*-
"""
test_complex_html_form.py

Copyright 2017 Andres Riancho

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
import os
import unittest

import w3af.core.data.kb.config as cf

from w3af import ROOT_PATH
from w3af.core.data.parsers.doc.html import HTMLParser
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.doc.tests.test_sgml import build_http_response


class RaiseHTMLParser(HTMLParser):
    def _handle_exception(self, where, ex):
        raise ex


class TestComplexHTMLForm(unittest.TestCase):
    url = URL('http://w3af.com')
    COMPLEX_FORM = os.path.join(ROOT_PATH, 'core', 'data', 'parsers', 'doc',
                                'tests', 'data', 'complex-form.html')

    EXPECTED_PARAMS = ['ctl00$cphHuvud$passlangd', 'ctl00$cphHuvud$visabokade',
                       'ctl00$ucLogin$txtAnvnamn', 'ctl00$cphHuvud$hdnMaxdgr',
                       'ctl00$cphHuvud$ibnNo', '__EVENTVALIDATION',
                       '__PREVIOUSPAGE', 'ctl00$cphHuvud$passslut',
                       'ctl00$cphHuvud$hdnDatediff', 'ctl00$cphHuvud$bnAvmarkeraAlla',
                       'ctl00$cphHuvud$ListaObjurval', 'ctl00$cphHuvud$passstart',
                       '__VIEWSTATEGENERATOR', 'ctl00$cphHuvud$txtTdat',
                       'ctl00$ucLogin$btnLoggain', 'ctl00$cphHuvud$txtFdat',
                       'ctl00$cphHuvud$grundschemanamn', 'ctl00$cphHuvud$ibnSv',
                       'ctl00$cphHuvud$visalediga', 'ctl00$cphHuvud$ListaGrundschema',
                       'ctl00$cphHuvud$btnSok2', 'ctl00$cphHuvud$btnSok1',
                       '__VIEWSTATE', 'ctl00$cphHuvud$bnMarkeraAlla',
                       'ctl00$cphHuvud$sortera', 'ctl00$cphHuvud$soktyp',
                       'ctl00$cphHuvud$btnSokObj2', 'ctl00$cphHuvud$btnSokObj1',
                       'ctl00$cphHuvud$ibnEn', 'ctl00$ucLogin$txtLosen',
                       'ctl00$cphHuvud$ibnIs']

    def test_complex_form_parse_and_variants(self):
        """
        Reported by one of our partners. The issue seems to be that there are
        too many variants being generated.
        """
        body = file(self.COMPLEX_FORM).read()
        resp = build_http_response(self.url, body)
        p = RaiseHTMLParser(resp)
        p.parse()

        mode = cf.cf.get('form_fuzzing_mode')

        form_params = p.forms[0]
        self.assertEqual(len([fv for fv in form_params.get_variants(mode)]),
                         form_params.TOP_VARIANTS + 1)

        self.assertEqual(len(form_params.meta.keys()), 31)
        self.assertEqual(form_params.meta.keys(), self.EXPECTED_PARAMS)

