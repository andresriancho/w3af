"""
test_hpp.py

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


from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse

LAST = 'last occurance'
FIRST = 'first occurance'
CONCAT = 'concatenation'

RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('hpp'),),
        }
    }
}


class TestPHP(PluginTest):

    target_url = 'http://phptarget/test.php?id=1234'
    MOCK_RESPONSES = [

        MockResponse(url='http://phptarget/test.php?id=1234',
                     body='<a href="decoy.php?p=1&cl_id=1234"> a </a>'
                          '<a href="viewemail.php?action=view&'
                          'client_id=1234"> View </a>'
                     ),
        MockResponse(url='http://phptarget/test.php?id=1235',
                     body='<a href="decoy.php?cl_id=1235&p=1"> a </a>'
                          '<a href="viewemail.php?action=view&'
                          'client_id=1235"> View </a>',
                     ),
        MockResponse(url='http://phptarget/test.php?id=1234&id=1235',
                     body='<a href="decoy.php?cl_id=1235&p=1"> a </a>'
                          '<a href="viewemail.php?action=view'
                          '&client_id=1235"> View </a>',
                     ),
        MockResponse(url='http://phptarget/test.php?'
                         'id=1234%26action%3Dw3afHPPForgeToken',
                     body='<a href="decoy.php?cl_id=1234&p=1"> a </a>'
                          '<a href="viewemail.php?action=view&'
                          'client_id=1234&action=w3afHPPForgeToken"> '
                          'View </a>',
                     ),
    ]

    def test_php1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(vulns))
        self.assertEquals(LAST, vulns[0].precedence)


class TestJAVA(PluginTest):

    target_url = 'http://javatarget/test.jsp?a=view'
    MOCK_RESPONSES = [

        MockResponse(url='http://javatarget/test.jsp?a=view',
                     body='<a href="viewemail.jsp?action=view&'
                          'client_id=1234"> View </a>'
                     ),
        MockResponse(url='http://javatarget/test.jsp?'
                         'a=w3afHPPReflectToken',
                     body='<a href="viewemail.jsp?'
                          'action=w3afHPPReflectToken&client_id=1234">'
                          ' View </a>'
                     ),
        MockResponse(url='http://javatarget/test.jsp?a=view&'
                         'a=w3afHPPReflectToken',
                     body='<a href="viewemail.jsp?action=view&'
                          'client_id=1234"> View </a>'
                     ),
        MockResponse(url='http://javatarget/test.jsp?'
                         'a=view%26client_id%3D1235',
                     body='<a href="viewemail.jsp?a=view'
                          '&client_id=1235&client_id=1234"> View </a>',
                     )
    ]

    def test_java1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(vulns))
        self.assertEquals(FIRST, vulns[0].precedence)


class TestASPNET(PluginTest):

    target_url = 'http://aspnettarget/test.asp?id=1234'
    MOCK_RESPONSES = [

        MockResponse(url='http://aspnettarget/test.asp?id=1234',
                     body='<a href="viewemail.asp?client_id=1234&'
                          'action=view"> View </a>',
                     ),
        MockResponse(url='http://aspnettarget/test.asp?id=1235',
                     body='<a href="viewemail.asp?client_id=1235&'
                          'action=view"> View </a>',
                     ),
        MockResponse(url='http://aspnettarget/test.asp?id=1234&id=1235',
                     body='<a href="viewemail.asp?client_id=1234,1235&'
                          'action=view"> View </a>',
                     ),
    ]

    def test_aspnet1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        info = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(info))
        self.assertEquals(CONCAT, info[0].precedence)
