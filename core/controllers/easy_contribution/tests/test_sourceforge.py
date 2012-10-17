# -*- coding: utf8 -*-
'''
test_sourceforge.py

Copyright 2011 Andres Riancho

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
import unittest

from core.controllers.easy_contribution.sourceforge import SourceforgeXMLRPC


class TestSourceforge(unittest.TestCase):
    
    def test_login(self):
        sf = SourceforgeXMLRPC('fake','12345')
        self.assertFalse( sf.login() )
        
        sf = SourceforgeXMLRPC('unittest','unittest12345')
        self.assertTrue( sf.login() )

    def test_report_bug_no_login(self):
        sf = SourceforgeXMLRPC('unittest','unittest12345')
        summary = 'Unittest bug report'
        userdesc = 'Please mark this ticket as invalid' 
        self.assertRaises(AssertionError, sf.report_bug, summary,userdesc)
    
    def test_report_bug_login(self):
        sf = SourceforgeXMLRPC('unittest','unittest12345')
        summary = 'Unittest bug report'
        userdesc = 'Please mark this ticket as invalid' 
        self.assertTrue( sf.login() )
        
        ticket_id, ticket_url = sf.report_bug(summary,userdesc)
        self.assertTrue( ticket_id.isdigit() )
        self.assertTrue( ticket_url.startswith('http://sourceforge.net/apps/trac/w3af/ticket/1') )
