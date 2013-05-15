'''
genexus_xml.py

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

'''
import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import xml.dom.minidom

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afException
from core.controllers.exceptions import w3afRunOnce
from core.controllers.misc.decorators import runonce
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.kb.info import Info
from core.data.parsers.url import URL


class genexus_xml(CrawlPlugin):
    '''
    Analyze the execute.xml and DeveloperMenu.xml files and find new URLs 
    author: Daniel Maldonado (daniel_5502@yahoo.com.ar) http://caceriadespammers.com.ar
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)

    @runonce(exc_class=w3afRunOnce)
    def crawl(self, fuzzable_request):
        '''
        Get the execute.xml file and parse it.

        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        '''
        dirs = []

        base_url = fuzzable_request.get_url().base_url()
        for file_name in ['execute.xml', 'Developer.xml']:
            execute_url = base_url.url_join(file_name)
            http_response = self._uri_opener.GET(execute_url, cache=True)

            if not is_404(http_response):
                # Save it to the kb!
                desc = 'An execute.xml file was found at: "%s", this file might'\
                       ' expose private URLs and requires a manual review. The'\
                       ' scanner will add all URLs listed in this file to the'\
                       ' crawl queue.'
                desc =  desc % execute_url
            
                i = Info('GeneXus execute.xml file', desc, http_response.id, self.get_name())
                i.set_url(execute_url)
            
                kb.kb.append(self, file_name, i)
                om.out.information(i.get_desc())

                # Extract the links
                om.out.debug('Analyzing "%s" file.'  % file_name)
                for fr in self._create_fuzzable_requests(http_response):
                    self.output_queue.put(fr)

                om.out.debug('Parsing xml file with xml.dot.minidom.')
                try:
                    dom = xml.dom.minidom.parseString(http_response.get_body())
                except:
                    raise w3afException('Error while parsing "%s"' % file_name)
                else:
                    raw_url_list = dom.getElementsByTagName("ObjLink")
                    parsed_url_list = []
                    for url in raw_url_list:
                        try:
                            url = url.childNodes[0].data
                            #url = URL(url)
                            url = base_url.url_join(url)
                        except ValueError, ve:
                            om.out.debug('execute.xml file had an invalid URL "%s"' % ve)
                        except:
                            om.out.debun('execute.xml file had an invalid format')
                        else:
                            parsed_url_list.append(url)
                    self.worker_pool.map(self.http_get_and_parse, parsed_url_list)

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for GeneXus' execute.xml and DeveloperMenu.xml file and parses it.

        By parsing this files, you can get more information about the
        target web application.
        '''
