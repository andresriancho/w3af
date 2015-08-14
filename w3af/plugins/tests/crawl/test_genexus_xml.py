"""
test_genexus_xml.py

Copyright 2013 Andres Riancho

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
from nose.plugins.attrib import attr
from w3af.plugins.tests.helper import PluginTest, PluginConfig, MockResponse


@attr('fails')
class TestGenexusXML(PluginTest):

    target_url = 'http://httpretty-mock/'

    _run_configs = {
        'cfg': {
            'target': target_url,
            'plugins': {'crawl': (PluginConfig('genexus_xml'),)}
        }
    }

    EXECUTE_XML = """<?xml-stylesheet type='text/xsl' href='prgs.xsl'?>
                     <Objects>
                        <Charset>iso-8859-1</Charset>
                        <Path>file:///C:/GeneXus/</Path>
                        <Object>
                            <ObjCls>13</ObjCls>
                            <ObjName>hidden</ObjName>
                            <ObjDesc>Small description</ObjDesc>
                            <ObjLink>hidden.aspx</ObjLink>
                        </Object>
                        <Object>
                            <ObjCls>13</ObjCls>
                            <ObjName>HMaster</ObjName>
                            <ObjDesc>Master description</ObjDesc>
                            <ObjLink>hmaster.aspx</ObjLink>
                        </Object>
                    </Objects>"""
    
    DEVELOPER_MENU_XML = """
    <?xml version="1.0" encoding="iso-8859-1"?>
    <Objects>
       <Charset>iso-8859-1</Charset>
       <Path>file:///C:/GeneXus/</Path>
       <Object>
          <ObjCls>0</ObjCls>
          <ObjName>Faith</ObjName>
          <ObjDesc>Load description</ObjDesc>
          <ObjLink>foobar.aspx</ObjLink>
       </Object>
    </Objects>"""

    MOCK_RESPONSES = [MockResponse('http://httpretty-mock/execute.xml',
                                   EXECUTE_XML,
                                   content_type='application/xml'),
                      MockResponse('http://httpretty-mock/DeveloperMenu.xml',
                                   DEVELOPER_MENU_XML,
                                   content_type='application/xml'),
                      MockResponse('http://httpretty-mock/hidden.aspx',
                                   'Exists'),
                      MockResponse('http://httpretty-mock/foobar.aspx',
                                   'Exists')]

    def test_genexus_xml(self):                
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])

        dev_infos = self.kb.get('genexus_xml', 'DeveloperMenu.xml')
        self.assertEqual(len(dev_infos), 1)
        dev_info = dev_infos[0]
        self.assertEqual(dev_info.get_url().url_string,
                         'http://httpretty-mock/DeveloperMenu.xml')
        
        exec_infos = self.kb.get('genexus_xml', 'execute.xml')
        self.assertEqual(len(exec_infos), 1)
        exec_info = exec_infos[0]
        self.assertEqual(exec_info.get_url().url_string,
                         'http://httpretty-mock/execute.xml')

        urls = self.kb.get_all_known_urls()

        EXPECTED_URLS = {'http://httpretty-mock/hidden.aspx',
                         'http://httpretty-mock/foobar.aspx',
                         'http://httpretty-mock/execute.xml',
                         'http://httpretty-mock/DeveloperMenu.xml',
                         'http://httpretty-mock/'}
        urls = set([u.url_string for u in urls])

        self.assertEqual(EXPECTED_URLS, urls)
