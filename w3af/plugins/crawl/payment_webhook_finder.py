"""
payment_webhook_finder.py

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
from itertools import chain, repeat, izip

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.data.dc.headers import Headers
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class payment_webhook_finder(CrawlPlugin):
    """
    Find hidden payment gateway webhooks.
    :author: Coiffey Pierre (pierre.coiffey@gmail.com)
    """
    _dirs = ('/', '/inc/', '/include/', '/include/pay/', '/includes/', '/includes/pay/', '/lib/',
             '/libraries/', '/module/', '/module/pay/', '/modules/', '/modules/pay/', '/payment/',
             '/shop/', '/store/', '/svc/', '/servlet/', '/cgi/', '/cgi-bin/', '/cgibin/',
    )

    _files = ('pay', 'payment', 'success', 'paymentsuccess', 'paymentcomplete', 'paymentsuccessful',
              'successful', 'paid', 'return', 'valid', 'validpay', 'validate', 'validatepayment',
              'validatepay', 'validation', 'complete', 'completepay', 'completepayment',
              'trxcomplete', 'transactioncomplete', 'final', 'finished',
    )
    _exts = ('', '.php', '.asp', '.aspx', '.jsp', '.py', 
             '.pl', '.rb', '.cgi', '.php3',  '.php4', '.php5',
    )

    def __init__(self):

        CrawlPlugin.__init__(self)

        self._seen = ScalableBloomFilter()

    def crawl(self, fuzzable_request):
        """
        Searches for new Url's using fuzzing.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        url = fuzzable_request.get_url()
        self._headers = Headers([('Referer', url.url_string)])

        if self._first_time:
            self._verify_head_enabled(url)
            self._first_time = False

        # First we need to delete fragments and query strings from URL.
        url = url.uri2url()

        # And we mark this one as a "do not return" URL, because the
        # core already found it using another technique.
        self._seen.add(url)

        self._verify_head_enabled(url)

        if self._head_enabled():
            response = self._uri_opener.HEAD(url, cache=True,
                                             headers=self._headers)
        else:
            response = self._uri_opener.GET(url, cache=True,
                                            headers=self._headers)

        if response.is_text_or_html():
            mutants_chain = chain(self._mutate_path(url))

            url_repeater = repeat(url)
            args = izip(url_repeater, mutants_chain)

            self.worker_pool.map_multi_args(self._do_request, args)

    def _do_request(self, url, mutant):
        """
        Perform a simple GET to see if the result is an error or not, and then
        run the actual fuzzing.
        """
        response = self._uri_opener.GET(mutant, cache=True,
                                        headers=self._headers)

        if (response.get_code() in (403, 401) or not(is_404(response))):

            # Create the fuzzable request and send it to the core
            fr = FuzzableRequest.from_http_response(response)
            self.output_queue.put(fr)
            
            #
            #   Save it to the kb (if new)!
            #
            if response.get_url() not in self._seen and response.get_url().get_file_name():
                desc = 'A potentially interesting url was found : "%s".'
                desc = desc % response.get_url()

                i = Info('Potentially interesting url', desc, response.id,
                         self.get_name())
                i.set_url(response.get_url())
                
                kb.kb.append(self, 'url', i)
                om.out.information(i.get_desc())

                # Report only once
                self._seen.add(response.get_url())

    def _mutate_path(self, url):
        """
        Mutate the path of the url.

        :param url: A URL to transform.
        :return: A list of URL's that mutate the original url passed
                 as parameter.

        >>> from w3af.core.data.parsers.doc.url import URL
        >>> u = payment_webhook_finder()
        >>> url = URL( 'http://www.w3af.com/' )
        >>> list(u._mutate_path(url))
        []

        >>> URL('http://www.w3af.com/inc/payment.php') in mutants
        True
        >>> URL('http://www.w3af.com//module/pay/valid.aspx') in mutants
        True
        >>> URL('http://www.w3af.com/cgi-bin/paymentsuccessful.cgi') in mutants
        True
        """
        url_string = url.url_string

        if url_string.count('/') > 2:
            # Create the new path
            url_string = url_string[:url_string.rfind('/')]

            dir_to_append_list = self._dirs
            file_to_append_list = self._files
            ext_to_append_list = self._exts
            
            for dir_to_append in dir_to_append_list:
                for file_to_append in file_to_append_list:
                    for ext_to_append in ext_to_append_list:
                        newurl = URL(url_string + dir_to_append + file_to_append + ext_to_append)
                        yield newurl

    def _verify_head_enabled(self, url):
        """
        Verifies if the requested URL permits a HEAD request.
        This was saved inside the KB by the plugin allowed_methods

        :return : Sets self._head to the correct value, nothing is returned.
        """
        allowed_methods_infos = kb.kb.get('allowed_methods', 'methods')
        allowed_methods = []
        for info in allowed_methods_infos:
            allowed_methods.extend(info['methods'])
        
        if 'HEAD' in allowed_methods:
            self._head = True
        else:
            self._head = False

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before the
        current one.
        """
        return ['infrastructure.allowed_methods']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin will try to find new URL's based on the input. If the input
        is for example:
            - http://host.tld

        The plugin will request:
            - http://host.tld/inc/
            - http://host.tld/include/pay/success.php
            - http://host.tld/cgi/validate/payment.cgi
            ...
            - http://host.tld/modules/pay/paid.py

        If the response is different from the 404 page (whatever it may be,
        automatic detection is performed), then we have found a new URL. 
        
        Useful if you're pentesting a payement gateway that uses a hidden 
        payment confirmation page which is accessed by the payment
        gateway and not intended for public access.

        """
