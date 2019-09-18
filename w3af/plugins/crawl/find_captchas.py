"""
find_captchas.py

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
import hashlib

from collections import namedtuple

import w3af.core.controllers.output_manager as om

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.parsers.document_parser as DocumentParser

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.kb.info import Info


class find_captchas(CrawlPlugin):
    """
    Identify captcha images on web pages.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        self._captchas_found = DiskSet(table_prefix='find_captchas')

    def crawl(self, fuzzable_request, debugging_id):
        """
        Find CAPTCHA images.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        result, captchas = self._identify_captchas(fuzzable_request)
        
        if not result:
            return

        for captcha in captchas:
            desc = 'Found a CAPTCHA image at: "%s".' % captcha.img_src
            response_ids = [response.id for response in captcha.http_responses]

            i = Info('Captcha image detected', desc, response_ids, self.get_name())
            i.set_uri(captcha.img_src)

            kb.kb.append(self, 'CAPTCHA', i)
            om.out.information(i.get_desc())

    def _identify_captchas(self, fuzzable_request):
        """
        :return: A tuple with the following information:
                    * True indicating that the page has CAPTCHAs
                    * A list with tuples that contain:
                        * The CAPTCHA image source
                        * The http responses used to verify that the image was
                          indeed a CAPTCHA
        """
        found_captcha = False
        captchas = []
        
        # GET the document, and fetch the images
        images_1 = self._get_images(fuzzable_request)

        # Re-GET the document, and fetch the images
        images_2 = self._get_images(fuzzable_request)

        # If the number of images in each response is different, don't even
        # bother to perform any analysis since our simplistic approach will fail
        #
        # TODO: Add something more advanced.
        if len(images_1) != len(images_2):
            return

        not_in_2 = []

        for img_src_1, img_hash_1, http_response_1 in images_1:
            for _, img_hash_2, http_response_2 in images_2:
                if img_hash_1 == img_hash_2:
                    # The image is in both lists, can't be a CAPTCHA
                    break
            else:
                not_in_2.append((img_src_1, img_hash_1, [http_response_1, http_response_2]))

        # Results
        #
        # TODO: This allows for more than one CAPTCHA in the same page. Does
        #       that make sense? When that's found, should I simply declare
        #       defeat and don't report anything?
        for img_src, _, http_responses in not_in_2:

            CaptchaInfo = namedtuple('CaptchaInfo', ['img_src',
                                                     'http_responses'])
            img_src = img_src.uri2url()

            if img_src not in self._captchas_found:
                self._captchas_found.add(img_src)
                found_captcha = True

                captchas.append(CaptchaInfo(img_src, http_responses))
                    
        return found_captcha, captchas
        
    def _get_images(self, fuzzable_request):
        """
        Get all img tags and retrieve the src.

        :param fuzzable_request: The request to modify
        :return: A list with tuples containing (img_src, image_hash, http_response)
        """
        res = []

        try:
            response = self._uri_opener.GET(fuzzable_request.get_uri(),
                                            cache=False)
        except:
            om.out.debug('Failed to retrieve the page for finding captchas.')
        else:
            # Do not use parser_cache here, it's not good since CAPTCHA implementations
            # *might* change the image name for each request of the HTML
            #
            # dp = parser_cache.dpc.get_document_parser_for( response )
            #
            try:
                document_parser = DocumentParser.DocumentParser(response)
            except BaseFrameworkException:
                return []
            
            image_path_list = document_parser.get_references_of_tag('img')

            GET = self._uri_opener.GET
            sha1 = hashlib.sha1
            
            result_iter = self.worker_pool.imap_unordered(GET, image_path_list)
            
            for image_response in result_iter:
                if image_response.is_image():
                    img_src = image_response.get_uri()
                    img_hash = sha1(image_response.get_body()).hexdigest()
                    res.append((img_src, img_hash, response))

        return res

    def end(self):
        self._captchas_found.cleanup()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds any CAPTCHA images that appear on a HTML document. The
        crawl is performed by requesting the document two times, and comparing
        the image hashes, if they differ, then they may be a CAPTCHA.
        """
