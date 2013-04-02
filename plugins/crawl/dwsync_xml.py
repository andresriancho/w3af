'''
dwsync_xml.py

Copyright 2013 Tomas Velazquez

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
import xml.dom.minidom

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb
import core.data.constants.severity as severity

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.exceptions import w3afException
from core.controllers.core_helpers.fingerprint_404 import is_404
from core.data.db.disk_set import DiskSet
from core.data.kb.vuln import Vuln


class dwsync_xml(CrawlPlugin):
    '''
    Search Dream Waver Sync file (dwsync.xml) and checks for files containing.
    :author: Tomas Velazquez ( tomas.velazquezz@gmail.com )
    '''
    
    def __init__(self):
        CrawlPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = DiskSet()
        self._dwsync = '_notes/dwsync.xml'

    def crawl(self, fuzzable_request):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        :parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''

        for domain_path in fuzzable_request.get_url().get_directories():
            if domain_path not in self._analyzed_dirs:
                self._analyzed_dirs.add( domain_path )

                sitemap_url = domain_path.url_join( self._dwsync )
                response = self._uri_opener.GET( sitemap_url, cache=True )

                # Remember that httpResponse objects have a faster "__in__" 
                # than the one in strings; so string in response.get_body() 
                # is slower than string in response
                if '</dwsync>' in response and not is_404( response ):
                    om.out.debug('Analyzing dwsync.xml file.')

                    for fr in self._create_fuzzable_requests( response ):
                        self.output_queue.put(fr)

                    om.out.debug('Parsing xml file with xml.dom.minidom.')
                    try:
                        dom = xml.dom.minidom.parseString( response.get_body() )
                    except:
                        raise w3afException('Error while parsing dwsync.xml')
                    else:
                        raw_url_list = dom.getElementsByTagName("file")
                        parsed_url_list = set()
                        for url in raw_url_list:
                            try:
                                url = url.getAttribute('name')
                                url = domain_path.url_join( url )
                                parsed_url_list.add(url)
                            except ValueError, ve:
                                msg = 'Sitemap file had an invalid URL: "%s"'
                                om.out.debug(msg % (ve))
                            except:
                                msg = 'Sitemap file had an invalid format'
                                om.out.debug(msg)

                        desc = 'A dwsync.xml file was found at: %s. The contents'\
                               ' of this file disclose filenames'
                        desc = desc % (response.get_url())

                        v = Vuln('dwsync.xml file found', desc, severity.LOW,
                                 response.id, self.get_name())
                        v.set_url(response.get_url())


                        kb.kb.append( self, 'dwsync_xml', v )
                        om.out.vulnerability(v.get_desc(), 
                                              severity=v.get_severity())

                        self.worker_pool.map(self._get_and_parse, parsed_url_list)

    def _get_and_parse(self, url):
        '''
        GET and URL that was found in the dwsync.xml file, and parse it.
        
        :parameter url: The URL to GET.
        :return: None, everything is saved to self.out_queue.
        '''
        try:
            http_response = self._uri_opener.GET( url, cache=True )
        except KeyboardInterrupt, k:
            raise k
        except w3afException, w3:
            msg = ('w3afException while fetching page in crawl.sitemap_xml, '
                   'error: "%s"')
            om.out.debug( msg % (w3))
        else:
            if not is_404( http_response ):
                for fr in self._create_fuzzable_requests( http_response ):
                    self.output_queue.put(fr)

    def get_long_desc( self ):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin searches for the _notes/dwsync.xml file in all the directories 
        and subdirectories that are sent as input and if it finds it will try to
        discover new URLs from its content. The _notes/dwsync.xml file holds 
        information about the list of files in the current directory. These files 
        are created by Adobe Dreamweaver. For example, if the input is:
            - http://host.tld/w3af/index.php
            
        The plugin will perform these requests:
            - http://host.tld/w3af/_notes/dwsync.xml
            - http://host.tld/_notes/dwsync.xml
        
        '''

