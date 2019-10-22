"""
payment_webhook_finder.py

Copyright 2019 Andres Riancho

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
from itertools import repeat, izip

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.kb_url_extensions import get_url_extensions_from_kb
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class payment_webhook_finder(CrawlPlugin):
    """
    Find hidden payment gateway webhooks.

    :author: Coiffey Pierre (pierre.coiffey@gmail.com)
    """
    _dirs = {'/',
             '/inc/',
             '/include/',
             '/include/pay/',
             '/includes/',
             '/includes/pay/',
             '/lib/',
             '/libraries/',
             '/module/',
             '/module/pay/',
             '/modules/',
             '/modules/pay/',
             '/payment/',
             '/shop/',
             '/store/',
             '/svc/',
             '/servlet/',
             '/cgi/',
             '/cgi-bin/',
             '/cgibin/'}

    _files = {'pay',
              'payment',
              'success',
              'paymentsuccess',
              'paymentcomplete',
              'paymentsuccessful',
              'successful',
              'paid',
              'return',
              'valid',
              'validpay',
              'validate',
              'validatepayment',
              'validatepay',
              'validation',
              'complete',
              'completepay',
              'completepayment',
              'trxcomplete',
              'transactioncomplete',
              'final',
              'finished'}

    _exts = {'',
             'php',
             'asp',
             'aspx',
             'jsp',
             'py',
             'pl',
             'rb',
             'cgi',
             'php3',
             'php4',
             'php5'}

    _methods = {'GET',
                'POST'}

    MIN_URL_COUNT_FOR_EXTENSION_FILTER = 100

    def __init__(self):
        CrawlPlugin.__init__(self)
        self._already_tested = ScalableBloomFilter()

    def crawl(self, fuzzable_request, debugging_id):
        """
        Searches for new URLs using fuzzing.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        uri = fuzzable_request.get_url()
        url = uri.uri2url()

        exts_to_append = self._get_extensions_for_fuzzing()

        url_generator = self._mutate_path(url,
                                          self._dirs,
                                          self._files,
                                          exts_to_append)
        url_generator = self._test_once_filter(url_generator)

        url_repeater = repeat(url)
        args = izip(url_repeater, url_generator)

        self.worker_pool.map_multi_args(self._send_requests, args)

    def _get_extensions_for_fuzzing(self):
        """
        This method is a performance improvement that reduces the number of HTTP
        requests sent by the plugin.

        When there are enough samples in kb.kb.get_all_known_urls() the method
        will only return a sub-set of the URL filename extensions to perform
        fuzzing on.

        :return: A set containing the extensions to use during fuzzing
        """
        if len(kb.kb.get_all_known_urls()) < self.MIN_URL_COUNT_FOR_EXTENSION_FILTER:
            return self._exts

        site_url_extensions = get_url_extensions_from_kb()
        return site_url_extensions.intersection(self._exts)

    def _send_requests(self, url, mutant):
        """
        Perform a GET and POST request to check if the endpoint exists
        """
        for method in self._methods:
            functor = getattr(self._uri_opener, method)
            self._send_request(functor, url, mutant)

    def _send_request(self, functor, url, mutant):
        response = functor(mutant, cache=True)

        if is_404(response):
            return

        # Create the fuzzable request and send it to the core
        fr = FuzzableRequest.from_http_response(response)
        self.output_queue.put(fr)

        #
        # Save it to the kb!
        #
        desc = 'A potentially interesting URL was found at: "%s".'
        desc %= response.get_url()

        i = Info('Potentially interesting URL',
                 desc,
                 response.id,
                 self.get_name())
        i.set_url(response.get_url())

        kb.kb.append_uniq(self, 'url', i, filter_by='URL')
        om.out.information(i.get_desc())

    def _test_once_filter(self, mutated_url_path_generator):
        for mutated_url_path in mutated_url_path_generator:

            is_new = self._already_tested.add(mutated_url_path)

            if is_new:
                yield mutated_url_path

    def _mutate_path(self, url, dirs_to_append, files_to_append, exts_to_append):
        """
        Mutate the path of the url.

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed as parameter
        """
        url_string = url.url_string

        if url_string.count('/') <= 1:
            return

        # Create the new path
        url_string = url_string[:url_string.rfind('/')]

        for dir_to_append in dirs_to_append:
            for file_to_append in files_to_append:
                for ext_to_append in exts_to_append:

                    if ext_to_append:
                        ext_to_append = '.%s' % ext_to_append

                    args = (url_string, dir_to_append, file_to_append, ext_to_append)
                    url_str = '%s%s%s%s' % args

                    new_url = URL(url_str)

                    yield new_url

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to find payment gateway webhooks, for example if
        the input URL is:
        
            - http://host.tld

        The plugin will request:
        
            - http://host.tld/inc/
            - http://host.tld/include/pay/success.php
            - http://host.tld/cgi/validate/payment.cgi
            ...
            - http://host.tld/modules/pay/paid.py

        If the response is different from the 404 page (whatever it may be,
        automatic detection is performed), then we have found a new URL.

        Useful when performing a black-box security assessment of an e-commerce
        site that has a hidden payment confirmation endpoint which is consumed
        by the payment gateway and not intended for public access.
        
        Warning! This plugin will send *many HTTP requests* and potentially
        increase scan time.
        """