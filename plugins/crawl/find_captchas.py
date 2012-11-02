'''
find_captchas.py

Copyright 2006 Andres Riancho

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
import hashlib

import core.controllers.outputManager as om

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info
import core.data.parsers.documentParser as documentParser

from core.controllers.plugins.crawl_plugin import CrawlPlugin
from core.controllers.w3afException import w3afException
from core.data.db.disk_set import disk_set


class find_captchas(CrawlPlugin):
    '''
    Identify captcha images on web pages.
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        CrawlPlugin.__init__(self)
        
        self._captchas_found = disk_set()
        
    def crawl(self, fuzzable_request ):
        '''
        Find CAPTCHA images.
        
        @parameter fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        # GET the document, and fetch the images
        images_1 = self._get_images( fuzzable_request )
        
        # Re-GET the document, and fetch the images
        images_2 = self._get_images( fuzzable_request )
        
        # If the number of images in each response is different, don't even bother
        # to perform any analysis since our simplistic approach will fail.
        # TODO: Add something more advanced.
        if len(images_1) == len(images_2):
            
            not_in_2 = []
            
            for img_src_1, img_hash_1 in images_1:
                for _, img_hash_2 in images_2:
                    if img_hash_1 == img_hash_2:
                        # The image is in both lists, can't be a CAPTCHA 
                        break
                else:
                    not_in_2.append( (img_src_1, img_hash_1) )
            
            # Results
            #
            # TODO: This allows for more than one CAPTCHA in the same page. Does
            #       that make sense? When that's found, should I simply declare
            #       defeat and don't report anything?
            for img_src, _ in not_in_2:
                
                if img_src.uri2url() not in self._captchas_found:
                    self._captchas_found.add( img_src.uri2url() )
                    
                    i = info.info()
                    i.setPluginName(self.get_name())
                    i.set_name('Captcha image detected')
                    i.setURI( img_src )
                    i.setMethod( 'GET' )
                    i.set_desc( 'Found a CAPTCHA image at: "%s".' % img_src)
                    kb.kb.append( self, 'CAPTCHA', i )
                    om.out.information( i.get_desc() )
            
        return []
    
    def _get_images( self, fuzzable_request ):
        '''
        Get all img tags and retrieve the src.
        
        @parameter fuzzable_request: The request to modify
        @return: A list with tuples containing (img_src, image_hash)
        '''
        res = []

        try:
            response = self._uri_opener.GET( fuzzable_request.getURI(), cache=False )
        except:
            om.out.debug('Failed to retrieve the page for finding captchas.')
        else:
            # Do not use dpCache here, it's not good since CAPTCHA implementations
            # *might* change the image name for each request of the HTML
            #dp = dpCache.dpc.getDocumentParserFor( response )
            try:
                document_parser = documentParser.documentParser( response )
            except w3afException:
                pass
            else:
                image_path_list = document_parser.getReferencesOfTag('img')
                
                GET = self._uri_opener.GET
                result_iter = self._tm.threadpool.imap_unordered(GET, image_path_list)
                for image_response in result_iter:
                    if image_response.is_image():
                        img_src = image_response.getURI()
                        img_hash = hashlib.sha1(image_response.getBody()).hexdigest()
                        res.append( (img_src, img_hash) ) 
        
        return res

    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds any CAPTCHA images that appear on a HTML document. The
        crawl is performed by requesting the document two times, and comparing
        the image hashes, if they differ, then they may be a CAPTCHA.
        '''
