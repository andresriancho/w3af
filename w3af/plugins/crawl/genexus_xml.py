"""
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

"""
import xml.dom.minidom

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.exceptions import RunOnce
from w3af.core.controllers.misc.decorators import runonce
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.kb.info import Info


class genexus_xml(CrawlPlugin):
    """
    Analyze the execute.xml and DeveloperMenu.xml files and find new URLs
    
    :author: Daniel Maldonado (daniel_5502@yahoo.com.ar)
    :url: http://caceriadespammers.com.ar
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

    @runonce(exc_class=RunOnce)
    def crawl(self, fuzzable_request):
        """
        Get the execute.xml file and parse it.

        :param fuzzable_request: A fuzzable_request instance that contains
                                (among other things) the URL to test.
        """
        base_url = fuzzable_request.get_url().base_url()
        
        for file_name in ('execute.xml', 'DeveloperMenu.xml'):
            genexus_url = base_url.url_join(file_name)
            
            http_response = self._uri_opener.GET(genexus_url, cache=True)
            
            if '</ObjLink>' in http_response and not is_404(http_response):
                # Save it to the kb!
                desc = 'The "%s" file was found at: "%s", this file might'\
                       ' expose private URLs and requires a manual review. The'\
                       ' scanner will add all URLs listed in this file to the'\
                       ' crawl queue.'
                desc =  desc % (file_name, genexus_url)
                title_info = 'GeneXus "%s" file' % file_name
            
                i = Info(title_info, desc, http_response.id, self.get_name())
                i.set_url(genexus_url)

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
                    raise BaseFrameworkException('Error while parsing "%s"' % file_name)
                else:
                    raw_url_list = dom.getElementsByTagName("ObjLink")
                    parsed_url_list = []
                    
                    for url in raw_url_list:
                        try:
                            url = url.childNodes[0].data
                            url = base_url.url_join(url)
                        except ValueError, ve:
                            msg = '"%s" file had an invalid URL "%s"'
                            om.out.debug(msg % (file_name,ve))
                        except:
                            msg = '"%s" file had an invalid format'
                            om.out.debug(msg % file_name)
                        else:
                            parsed_url_list.append(url)
                    
                    self.worker_pool.map(self.http_get_and_parse,
                                         parsed_url_list)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin searches for GeneXus' execute.xml and DeveloperMenu.xml
        file and parses it.

        By parsing this files, you can get more information about the
        target web application.
        """