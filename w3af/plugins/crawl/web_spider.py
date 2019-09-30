"""
web_spider.py

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
import re
import itertools

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.constants.response_codes as http_constants

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.itertools_toolset import unique_justseen
from w3af.core.controllers.exceptions import BaseFrameworkException

from w3af.core.data.parsers.utils.header_link_extract import headers_url_generator
from w3af.core.data.db.variant_db import VariantDB
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.factory import dc_from_form_params
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, REGEX, LIST
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class web_spider(CrawlPlugin):
    """
    Crawl the web application.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    UNAUTH_FORBID = {http_constants.UNAUTHORIZED, http_constants.FORBIDDEN}

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._compiled_ignore_re = None
        self._compiled_follow_re = None
        self._broken_links = DiskSet(table_prefix='web_spider')
        self._first_run = True
        self._target_urls = []
        self._target_domain = None
        self._already_filled_form = ScalableBloomFilter()
        self._variant_db = VariantDB()

        # User configured variables
        self._ignore_regex = ''
        self._follow_regex = '.*'
        self._only_forward = False
        self._ignore_extensions = []
        self._compile_re()

    def crawl(self, fuzzable_request, debugging_id):
        """
        Searches for links on the html.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_req instance that contains
                                 (among other things) the URL to test.
        """
        self._handle_first_run()

        #
        # If it is a form, then smart_fill the parameters to send something that
        # makes sense and will allow us to cover more code.
        #
        data_container = fuzzable_request.get_raw_data()
        if isinstance(data_container, Form):

            if fuzzable_request.get_url() in self._already_filled_form:
                return

            self._already_filled_form.add(fuzzable_request.get_url())
            data_container.smart_fill()

        # Send the HTTP request
        resp = self._uri_opener.send_mutant(fuzzable_request)

        # Nothing to do here...
        if resp.get_code() == http_constants.UNAUTHORIZED:
            return

        # Nothing to do here...
        if resp.is_image():
            return

        # And we don't trust what comes from the core, check if 404
        if is_404(resp):
            return

        self._extract_html_forms(resp, fuzzable_request)
        self._extract_links_and_verify(resp, fuzzable_request)

    def _extract_html_forms(self, resp, fuzzable_req):
        """
        Parses the HTTP response body and extract HTML forms, resulting forms
        are put() on the output queue.
        """
        # Try to find forms in the document
        try:
            dp = parser_cache.dpc.get_document_parser_for(resp)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        # Create one FuzzableRequest for each form variant
        mode = cf.cf.get('form_fuzzing_mode')
        for form_params in dp.get_forms():

            # Form exclusion #15161
            form_id_json = form_params.get_form_id().to_json()
            om.out.debug('A new form was found! Form-id is: "%s"' % form_id_json)

            if not self._should_analyze_url(form_params.get_action()):
                continue

            headers = fuzzable_req.get_headers()

            for form_params_variant in form_params.get_variants(mode):
                data_container = dc_from_form_params(form_params_variant)

                # Now data_container is one of Multipart of URLEncoded form
                # instances, which is a DataContainer. Much better than the
                # FormParameters instance we had before in form_params_variant
                r = FuzzableRequest.from_form(data_container, headers=headers)
                self.output_queue.put(r)

    def _handle_first_run(self):
        if not self._first_run:
            return

        # I have to set some variables, in order to be able to code
        # the "only_forward" feature
        self._first_run = False
        self._target_urls = [i.uri2url() for i in cf.cf.get('targets')]

        # The following line triggered lots of bugs when the "stop" button
        # was pressed and the core did this: "cf.cf.save('targets', [])"
        #
        #self._target_domain = cf.cf.get('targets')[0].get_domain()
        #
        #    Changing it to something awful but bug-free.
        targets = cf.cf.get('targets')
        if not targets:
            return

        self._target_domain = targets[0].get_domain()
                
    def _urls_to_verify_generator(self, resp, fuzzable_req):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        gen = itertools.chain(self._url_path_url_generator(resp, fuzzable_req),
                              self._body_url_generator(resp, fuzzable_req),
                              headers_url_generator(resp, fuzzable_req))
        
        for ref, fuzzable_req, original_resp, possibly_broken in gen:
            if self._should_verify_extracted_url(ref, original_resp):
                yield ref, fuzzable_req, original_resp, possibly_broken

    def _url_path_url_generator(self, resp, fuzzable_req):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        # Analyze all directories, if the URL w3af just found is:
        #
        #   http://localhost/a/b/c/f00.php
        #
        # I want to GET:
        #
        #   http://localhost/a/b/c/
        #   http://localhost/a/b/
        #   http://localhost/a/
        #   http://localhost/
        #
        # And analyze the responses...
        dirs = resp.get_url().get_directories()

        for ref in unique_justseen(dirs):
            yield ref, fuzzable_req, resp, False

    def _body_url_generator(self, resp, fuzzable_req):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        The newly found URLs are extracted from the http response body using
        one of the framework's parsers.

        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        #
        # Note: I WANT to follow links that are in the 404 page.
        #
        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(resp)
        except BaseFrameworkException, w3:
            om.out.debug('Failed to find a suitable document parser. '
                         'Exception "%s"' % w3)
        else:
            # Note:
            #
            # - With parsed_refs I'm 100% that it's really
            #   something in the HTML that the developer intended to add.
            #
            # - The re_refs are the result of regular expressions,
            #   which in some cases are just false positives.
            parsed_refs, re_refs = doc_parser.get_references()

            dirs = resp.get_url().get_directories()
            only_re_refs = set(re_refs) - set(dirs + parsed_refs)

            all_refs = itertools.chain(parsed_refs, re_refs)
            resp_is_404 = is_404(resp)

            for ref in unique_justseen(sorted(all_refs)):
                possibly_broken = resp_is_404 or (ref in only_re_refs)
                yield ref, fuzzable_req, resp, possibly_broken

    def _should_analyze_url(self, ref):
        """
        :param ref: A URL instance to match against the user configured filters
        :return: True if we should navigate to this URL
        """
        # I don't want w3af sending requests to 3rd parties!
        if ref.get_domain() != self._target_domain:
            msg = 'web_spider will ignore %s (different domain name)'
            args = (ref.get_domain(),)
            om.out.debug(msg % args)
            return False

        # Filter the URL according to the configured regular expressions
        if not self._compiled_follow_re.match(ref.url_string):
            msg = 'web_spider will ignore %s (not match follow regex)'
            args = (ref.url_string,)
            om.out.debug(msg % args)
            return False

        if self._compiled_ignore_re.match(ref.url_string):
            msg = 'web_spider will ignore %s (match ignore regex)'
            args = (ref.url_string,)
            om.out.debug(msg % args)
            return False

        if self._has_ignored_extension(ref):
            msg = 'web_spider will ignore %s (match ignore extensions)'
            args = (ref.url_string,)
            om.out.debug(msg % args)
            return False

        # Implementing only forward
        if self._only_forward and not self._is_forward(ref):
            msg = 'web_spider will ignore %s (is not forward)'
            args = (ref.url_string,)
            om.out.debug(msg % args)
            return False

        return True

    def _has_ignored_extension(self, new_url):
        if not self._ignore_extensions:
            return False

        return new_url.get_extension().lower() in self._ignore_extensions

    def _should_verify_extracted_url(self, ref, resp):
        """
        :param ref: A newly found URL
        :param resp: The HTTP response where the URL was found

        :return: Boolean indicating if I should send this new reference to the
                 core.
        """
        # Ignore myself
        if ref == resp.get_uri():
            return False

        if not self._should_analyze_url(ref):
            return False

        #
        # I tried to have only one VariantDB in the framework instead of two,
        # but after some tests and architecture considerations it was better
        # to duplicate the data.
        #
        # In the future I'll run plugins in different processes than the core,
        # so it makes sense to have independent plugins.
        #
        # If I remove the web_spider VariantDB and just leave the one in the
        # core the framework keeps working but this method
        # (_should_verify_extracted_url) will return True much more often, which
        # leads to extra HTTP requests for URLs which we already checked and the
        # core will dismiss anyway
        #
        fuzzable_request = FuzzableRequest(ref)
        if self._variant_db.append(fuzzable_request):
            return True

        return False

    def _extract_links_and_verify(self, resp, fuzzable_req):
        """
        This is a very basic method that will send the work to different
        threads. Work is generated by the _urls_to_verify_generator

        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        self.worker_pool.map_multi_args(
            self._verify_reference,
            self._urls_to_verify_generator(resp, fuzzable_req))

    def _verify_reference(self, reference, original_request,
                          original_response, possibly_broken,
                          be_recursive=True):
        """
        The parameters are:
            * Newly found URL
            * The FuzzableRequest instance which generated the response where
              the new URL was found
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        This method GET's every new link and parses it in order to get
        new links and forms.
        """
        #
        # Remember that this "breaks" the cache=True in most cases!
        #     headers = { 'Referer': original_url }
        #
        # But this does not, and it is friendlier than simply ignoring the
        # referer
        #
        referer = original_response.get_url().base_url().url_string
        headers = Headers([('Referer', referer)])

        # Note: We're not grep'ing this HTTP request/response now because it
        #       has high probability of being a 404, and the grep plugins
        #       already got enough 404 responses to analyze (from is_404 for
        #       example). If it's not a 404 then we'll push it to the core
        #       and it will come back to this plugin's crawl() where it will
        #       be requested with grep=True
        resp = self._uri_opener.GET(reference, cache=True, headers=headers,
                                    grep=False)

        if not is_404(resp):
            msg = '[web_spider] Found new link "%s" at "%s"'
            args = (reference, original_response.get_url())
            om.out.debug(msg % args)

            fuzz_req = FuzzableRequest(reference, headers=headers)

            # These next steps are simple, but actually allows me to set the
            # referer and cookie for the FuzzableRequest instances I'm sending
            # to the core, which will then allow the fuzzer to create
            # CookieMutant and HeadersMutant instances.
            #
            # Without setting the Cookie, the CookieMutant would never have any
            # data to modify; remember that cookies are actually set by the
            # urllib2 cookie handler when the request already exited the
            # framework.
            cookie = Cookie.from_http_response(original_response)

            fuzz_req.set_referer(referer)
            fuzz_req.set_cookie(cookie)

            self.output_queue.put(fuzz_req)
            return

        # Note: I WANT to follow links that are in the 404 page, but
        # DO NOT return the 404 itself to the core.
        #
        # This will parse the 404 response and add the 404-links in the
        # output queue, so that the core can get them
        #
        if be_recursive:
            #
            # Only follow one level of links in 404 pages, this limits the
            # potential issue when this is found:
            #
            #   http://foo.com/abc/ => 404
            #   Body: <a href="def/">link</a>
            #
            # Which would lead to this function to perform requests to:
            #   * http://foo.com/abc/
            #   * http://foo.com/abc/def/
            #   * http://foo.com/abc/def/def/
            #   * http://foo.com/abc/def/def/def/
            #   * ...
            #

            # Do not use threads here, it will dead-lock (for unknown
            # reasons). This is tested in TestDeadLock unittest.
            for args in self._urls_to_verify_generator(resp, original_request):
                self._verify_reference(*args, be_recursive=False)

        # Store the broken links
        if not possibly_broken and resp.get_code() not in self.UNAUTH_FORBID:
            t = (resp.get_url(), original_request.get_uri())
            self._broken_links.add(t)

    def end(self):
        """
        Called when the process ends, prints out the list of broken links.
        """
        if len(self._broken_links):

            om.out.information('The following is a list of broken links that'
                               ' were found by the web_spider plugin:')
            for broken, where in unique_justseen(self._broken_links.ordered_iter()):
                om.out.information('- %s [ referenced from: %s ]' %
                                   (broken, where))
        
        self._broken_links.cleanup()

    def _is_forward(self, reference):
        """
        Check if the reference is inside the target directories.

        :return: True if reference is an URL inside the directory structure of
                 at least one of the target URLs.
        """
        for domain_path in self._target_urls:
            if reference.url_string.startswith(domain_path.url_string):
                return True

        return False

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Only crawl links to paths inside the URL given as target.'
        o = opt_factory('only_forward', self._only_forward, d, BOOL)
        ol.add(o)

        d = ('Only crawl links that match this regular expression.'
             ' Note that ignore_regex has precedence over follow_regex.')
        o = opt_factory('follow_regex', self._follow_regex, d, REGEX)
        ol.add(o)

        d = ('DO NOT crawl links that match this regular expression.'
             ' Note that ignore_regex has precedence over follow_regex.')
        o = opt_factory('ignore_regex', self._ignore_regex, d, REGEX)
        ol.add(o)

        d = 'DO NOT crawl links that use these extensions.'
        h = ('This configuration parameter is commonly used to ignore'
             ' static files such as zip, pdf, jpeg, etc. It is possible to'
             ' ignore these files using `ignore_regex`, but configuring'
             ' this parameter is easier and performs case insensitive'
             ' matching.')
        o = opt_factory('ignore_extensions', self._ignore_extensions, d, LIST, help=h)
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._only_forward = options_list['only_forward'].get_value()

        self._ignore_regex = options_list['ignore_regex'].get_value()
        self._follow_regex = options_list['follow_regex'].get_value()
        self._compile_re()

        self._ignore_extensions = options_list['ignore_extensions'].get_value()
        self._ignore_extensions = [ext.lower() for ext in self._ignore_extensions]

    def _compile_re(self):
        """
        Compile the regular expressions that are going to be used to ignore
        or follow links.
        """
        if self._ignore_regex:
            # Compilation of this regex can't fail because it was already
            # verified as valid at regex_option.py: see REGEX in get_options()
            self._compiled_ignore_re = re.compile(self._ignore_regex)
        else:
            # If the self._ignore_regex is empty then I don't have to ignore
            # anything. To be able to do that, I simply compile an re with "abc"
            # as the pattern, which won't match any URL since they will all
            # start with http:// or https://
            self._compiled_ignore_re = re.compile('abc')

        # Compilation of this regex can't fail because it was already
        # verified as valid at regex_option.py: see REGEX in get_options()
        self._compiled_follow_re = re.compile(self._follow_regex)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin is a classic web spider, it will request a URL and extract
        all links and forms from the response.

        Four configurable parameter exist:
            - only_forward
            - follow_regex
            - ignore_regex
            - ignore_extensions

        ignore_regex and follow_regex are commonly used to configure the
        web_spider to crawl all URLs except "/logout" or some more
        exciting link like "Reboot Appliance" that would greatly reduce
        the scan test coverage.

        By default ignore_regex is an empty string (nothing is ignored) and
        follow_regex is '.*' (everything is followed). Both regular expressions
        are compiled with Python's re module and applied to URLs (with query
        string included).
        
        The ignore_extensions configuration parameter is commonly used to ignore
        static files such as zip, jpeg, pdf, etc.
        """
