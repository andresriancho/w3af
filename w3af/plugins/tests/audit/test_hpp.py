"""
test_hpp.py

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


from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse

RUN_CONFIG = {
    'cfg': {
        'target': None,
        'plugins': {
            'audit': (PluginConfig('hpp'),),
        }
    }
}

# class NOT_VULN(PluginTest):
#
#     target_url = 'http://nvtarget/test.nv?a=view&id=1234'
#     MOCK_RESPONSES = [
#               MockResponse(url='http://nvtarget/test.nv?a=view%26a%3Dw3afHPPReflectToken&id=1234',
#                            body='Invalid Request',
#                             ),
#               MockResponse(url='http://nvtarget/test.nv?a=view&id=1234',
#                            body='<a href="viewemail.nv?client_id=1234&action=view"> View </a>',
#                            ),
#               MockResponse(url='http://nvtarget/test.nv?a=w3afHPPReflectToken&id=1234',
#                            body='<a href="viewemail.nv?client_id=1234&action=w3afHPPReflectToken"> View </a>',
#                            ),
#               ]
#
#     def test_nv1(self):
#         cfg = RUN_CONFIG['cfg']
#         self._scan(self.target_url, cfg['plugins'])
#         vulns = self.kb.get('hpp', 'hpp')
#         self.assertEquals(1, len(vulns))
#
# class Test_UNAFFECTED(PluginTest):
#
#     target_url = 'http://nvtarget/test.nv?a=view&id=1234'
#     MOCK_RESPONSES = [
#               MockResponse(url='http://nvtarget/test.nv?a=view%26a%3Dw3afHPPReflectToken&id=1234',
#                            body='<a href="viewemail.nv?client_id=1234&action=view"> View </a>',
#                             ),
#               MockResponse(url='http://nvtarget/test.nv?a=view&id=1234',
#                            body='<a href="viewemail.nv?client_id=1234&action=view"> View </a>',
#                            ),
#               MockResponse(url='http://nvtarget/test.nv?a=w3afHPPReflectToken&id=1234',
#                            body='<a href="viewemail.nv?client_id=1234&action=view"> View </a>',
#                            ),
#               ]
#
#     def test_unaffected1(self):
#         cfg = RUN_CONFIG['cfg']
#         self._scan(self.target_url, cfg['plugins'])
#         vulns = self.kb.get('hpp', 'hpp')
#         self.assertEquals(1, len(vulns))
# #
class Test_PHP_VULN(PluginTest):

    target_url = 'http://phptarget/test.php?a=view&id=1234'
    MOCK_RESPONSES = [
              MockResponse(url='http://phptarget/test.php?a=view&a=w3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.php?client_id=1234&action=w3afHPPReflectToken"> View </a>',
                            ),
              MockResponse(url='http://phptarget/test.php?a=view&id=1234&id=w3afHPPReflectToken',
                           body='<a href="viewemail.php?client_id=1234&action=w3afHPPReflectToken"> View </a>',
                            ),
              MockResponse(url='http://phptarget/test.php?a=view&id=1234',
                           body='<a href="viewemail.php?client_id=1234&action=view"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=w3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.php?client_id=1234&action=w3afHPPReflectToken"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=view&id=w3afHPPReflectToken',
                           body='<a href="viewemail.php?client_id=w3afHPPReflectToken&action=view"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=w3afHPPReflectToken%26action%3Dw3afHPPForgeToken&id=1234',
                           body='<a href="viewemail.php?client_id=1234&action=w3afHPPReflectToken&action=w3afHPPForgeToken"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=view&id=w3afHPPReflectToken%26action%3Dw3afHPPForgeToken',
                           body='<a href="viewemail.php?client_id=w3afHPPReflectToken&action=w3afHPPForgeToken&action=view"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=w3afHPPReflectToken%26client_id%3Dw3afHPPForgeToken&id=1234',
                           body='<a href="viewemail.php?client_id=1234&action=w3afHPPReflectToken&client_id=w3afHPPForgeToken"> View </a>',
                           ),
              MockResponse(url='http://phptarget/test.php?a=view&id=w3afHPPReflectToken%26client_id%3Dw3afHPPForgeToken',
                           body='<a href="viewemail.php?client_id=w3afHPPReflectToken&client_id=w3afHPPForgeToken&action=view"> View </a>',
                           ),
              ]

    def test_php1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(vulns))

#
# class Test_PHP_VULN_FORM(PluginTest):
#
#     target_url = 'http://phpform/test.php?to=info@mmm.com'
#     MOCK_RESPONSES = [
#               MockResponse(url='http://phpform/test.php?to=info%40mmm.com%26to%3Dw3afHPPReflectToken',
#                            body='<form action="post">'
#                                    'To: <input type="hidden" name="to" value="w3afHPPReflectToken"/> <br/>'
#                                     'From: <input type="text" name="from" /> <br/'
#                                     '<input type="text" name="message">'
# 	                                 '</form>'
#                             ),
#               MockResponse(url='http://phpform/test.php?to=info%40mmm.com',
#                            body='<form action="post">'
#                                     'To: <input type="hidden" name="to" value="info@mmm.com"/> <br/>'
#                                     'From: <input type="text" name="from" /> <br/'
#                                     '<input type="text" name="message">'
# 	                                '</form>'
#                             ),
#               MockResponse(url='http://phpform/test.php?to=w3afHPPReflectToken',
#                            body='<form action="post">'
#                                     'To: <input type="hidden" name="to" value="w3afHPPReflectToken"/> <br/>'
#                                     'From: <input type="text" name="from" /> <br/'
#                                     '<input type="text" name="message">'
# 	                                '</form>'
#                             ),
#               ]
#
#     def test_php_form1(self):
#         cfg = RUN_CONFIG['cfg']
#         self._scan(self.target_url, cfg['plugins'])
#         vulns = self.kb.get('hpp', 'hpp')
#         self.assertEquals(1, len(vulns))

class Test_JAVA_VULN(PluginTest):

    target_url = 'http://javatarget/test.jsp?a=view&id=1234'
    #target_url = 'http://help.merlion.ru/test.jsp?a=view&id=1234'
    MOCK_RESPONSES = [

              MockResponse(url='http://javatarget/test.jsp?a=view&a=w3afHPPReflectToken&id=1234',
                            body='<a href="viewemail.jsp?client_id=1234&action=view"> View </a>'
                            ),
              MockResponse(url='http://javatarget/test.jsp?a=view&id=1234',
                            body='<a href="viewemail.jsp?client_id=1234&action=view"> View </a>'
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=w3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.jsp?client_id=1234&action=w3afHPPReflectToken"> View </a>'
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=view&id=1234&id=w3afHPPReflectToken',
                           body='<a href="viewemail.jsp?client_id=1234&action=view"> View </a>',
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=view&id=w3afHPPReflectToken',
                           body='<a href="viewemail.jsp?client_id=w3afHPPReflectToken&action=view"> View </a>',
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=w3afHPPReflectToken%26action%3Dw3afHPPForgeToken&id=1234',
                           body='<a href="viewemail.jsp?client_id=1234&action=w3afHPPReflectToken&action=w3afHPPForgeToken"> View </a>',
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=view&id=w3afHPPReflectToken%26action%3Dw3afHPPForgeToken',
                           body='<a href="viewemail.jsp?client_id=w3afHPPReflectToken&action=view&action=w3afHPPForgeToken"> View </a>',
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=w3afHPPReflectToken%26client_id%3Dw3afHPPForgeToken&id=1234',
                           body='<a href="viewemail.jsp?client_id=w3afHPPForgeToken&action=w3afHPPReflectToken&client_id=1234"> View </a>',
                           ),
              MockResponse(url='http://javatarget/test.jsp?a=view&id=w3afHPPReflectToken%26client_id%3Dw3afHPPForgeToken',
                           body='<a href="viewemail.jsp?client_id=w3afHPPReflectToken&client_id=w3afHPPForgeToken&action=view"> View </a>',
                           ),
              ]

    def test_java1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(vulns))

class Test_ASPNET_VULN(PluginTest):

    target_url = 'http://aspnettarget/test.asp?a=view&id=1234'
    MOCK_RESPONSES = [
              MockResponse(url='http://aspnettarget/test.asp?a=view%26a%3Dw3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.asp?client_id=1234&action=view,w3afHPPReflectToken"> View </a>',
                            ),
              MockResponse(url='http://aspnettarget/test.asp?a=view&a=w3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.asp?client_id=1234&action=view,w3afHPPReflectToken"> View </a>',
                            ),
              MockResponse(url='http://aspnettarget/test.asp?a=view&id=1234&id=w3afHPPReflectToken',
                           body='<a href="viewemail.asp?client_id=1234,w3afHPPReflectToken&action=view"> View </a>',
                            ),
              MockResponse(url='http://aspnettarget/test.asp?a=view&id=1234',
                           body='<a href="viewemail.asp?client_id=1234&action=view"> View </a>',
                           ),
              MockResponse(url='http://aspnettarget/test.asp?a=view&id=w3afHPPReflectToken',
                           body='<a href="viewemail.asp?client_id=w3afHPPReflectToken&action=view"> View </a>',
                           ),
              MockResponse(url='http://aspnettarget/test.asp?a=w3afHPPReflectToken&id=1234',
                           body='<a href="viewemail.asp?client_id=1234&action=w3afHPPReflectToken"> View </a>',
                           ),
              ]

    def test_aspnet1(self):
        cfg = RUN_CONFIG['cfg']
        self._scan(self.target_url, cfg['plugins'])
        vulns = self.kb.get('hpp', 'hpp')
        self.assertEquals(1, len(vulns))


# class Test_MODPERL_VULN(PluginTest):
#
#     target_url = 'http://perltarget/test.pl?a=view&id=1234'
#     MOCK_RESPONSES = [
#               MockResponse(url='http://perltarget/test.pl?a=view%26a%3Dw3afHPPReflectToken&id=1234',
#                            body='<a href="viewemail.pl?client_id=1234&action=ARRAY"> View </a>',
#
#                             ),
#               MockResponse(url='http://perltarget/test.pl?a=view&id=1234',
#                            body='<a href="viewemail.pl?client_id=1234&action=view"> View </a>',
#                            ),
#               MockResponse(url='http://perltarget/test.pl?a=w3afHPPReflectToken&id=1234',
#                            body='<a href="viewemail.pl?client_id=1234&action=w3afHPPReflectToken"> View </a>',
#                            ),
#               ]
#
#     def test_modperl1(self):
#         cfg = RUN_CONFIG['cfg']
#         self._scan(self.target_url, cfg['plugins'])
#         vulns = self.kb.get('hpp', 'hpp')
#         self.assertEquals(1, len(vulns))
