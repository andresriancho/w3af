"""
test_pdf.py

Copyright 2012 Andres Riancho

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
import os

from w3af import ROOT_PATH
from w3af.plugins.grep.password_profiling_plugins.pdf import pdf


class TestPDF(unittest.TestCase):
    
    def test_extract_pdf(self):
        fname = os.path.join(ROOT_PATH, 'plugins', 'grep',
                             'password_profiling_plugins', 'tests', 'test.pdf')
        
        pdf_inst = pdf()
        
        words = pdf_inst._get_pdf_content(file(fname).read())

        EXPECTED_RESULT = ['Testing,', 'testing,', '123.', 'Text', 'in',
                           'page', 'number', 'two.']
        self.assertEqual(EXPECTED_RESULT, words)
