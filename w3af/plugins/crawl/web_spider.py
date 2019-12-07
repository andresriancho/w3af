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
import Queue
import threading
import itertools

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.config as cf
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.constants.response_codes as http_constants

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.itertools_toolset import unique_justseen
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.chrome.crawler.main import ChromeCrawler
from w3af.core.controllers.chrome.pool import ChromePool
from w3af.core.controllers.threads.threadpool import add_traceback_string

from w3af.core.data.parsers.utils.header_link_extract import headers_url_generator
from w3af.core.data.db.variant_db import VariantDB
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.dc.headers import Headers
from w3af.core.data.dc.factory import dc_from_form_params
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.dc.cookie import Cookie
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, REGEX, INT, LIST
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
        self._enable_js_crawler = True
        self._chrome_processes = ChromePool.MAX_INSTANCES

        # Chrome crawler
        self._chrome_crawler_inst = None
        self._chrome_crawler_exception = None
        self._http_traffic_queue = Queue.Queue()
        self._chrome_identified_http_requests = 0
        self._queue_handler_thread = None

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
        http_response = self._uri_opener.send_mutant(fuzzable_request,
                                                     debugging_id=debugging_id)

        # Nothing to do here...
        if http_response.get_code() == http_constants.UNAUTHORIZED:
            return

        # Nothing to do here...
        if http_response.is_image():
            return

        # And we don't trust what comes from the core, check if 404
        if is_404(http_response):
            return

        self._extract_html_forms(fuzzable_request, http_response, debugging_id)
        self._extract_links_and_verify(fuzzable_request, http_response, debugging_id)
        self._crawl_with_chrome(fuzzable_request, http_response, debugging_id)

    def _extract_html_forms(self, fuzzable_req, http_response, debugging_id):
        """
        Parses the HTTP response body and extract HTML forms, resulting forms
        are put() on the output queue.

        :param fuzzable_req: The HTTP request that generated the response
        :param http_response: The HTTP response
        """
        # Try to find forms in the document
        try:
            dp = parser_cache.dpc.get_document_parser_for(http_response)
        except BaseFrameworkException:
            # Failed to find a suitable parser for the document
            return

        # Create one FuzzableRequest for each form variant
        mode = cf.cf.get('form_fuzzing_mode')
        for form_params in dp.get_forms():

            # Form exclusion #15161
            form_id_json = form_params.get_form_id().to_json()
            args = (form_id_json, debugging_id)
            om.out.debug('A new form was found! Form-id is: "%s" (did: %s)' % args)

            if not self._uri_allowed_by_user_config(form_params.get_action()):
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
        #     self._target_domain = cf.cf.get('targets')[0].get_domain()
        #
        # Changing it to something awful but bug-free.
        targets = cf.cf.get('targets')
        if not targets:
            return

        self._target_domain = targets[0].get_domain()
                
    def _urls_to_verify_generator(self, fuzzable_request, http_response, debugging_id):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        :param http_response: HTTP response object
        :param fuzzable_request: The HTTP request that generated the response
        """
        chain = itertools.chain(self._url_path_url_generator(fuzzable_request, http_response),
                                self._body_url_generator(fuzzable_request, http_response),
                                headers_url_generator(fuzzable_request, http_response))
        
        for url, fuzzable_req, original_resp, possibly_broken in chain:

            # Ignore self reference
            if url == http_response.get_uri():
                continue

            if not self._should_verify_extracted_url(url):
                continue

            yield (url,
                   fuzzable_req,
                   original_resp,
                   possibly_broken,
                   debugging_id)

    def _url_path_url_generator(self, fuzzable_request, http_response):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        :param http_response: HTTP response object
        :param fuzzable_request: The HTTP request that generated the response
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
        dirs = http_response.get_url().get_directories()

        for ref in unique_justseen(dirs):
            yield ref, fuzzable_request, http_response, False

    def _body_url_generator(self, fuzzable_request, http_response):
        """
        Yields tuples containing:
            * Newly found URL
            * The FuzzableRequest instance passed as parameter
            * The HTTPResponse generated by the FuzzableRequest
            * Boolean indicating if we trust this reference or not

        The newly found URLs are extracted from the http response body using
        one of the framework's parsers.

        :param fuzzable_request: The HTTP request that generated the response
        :param http_response: HTTP response object
        """
        #
        # Note: I WANT to follow links that are in the 404 page.
        #
        try:
            doc_parser = parser_cache.dpc.get_document_parser_for(http_response)
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

            dirs = http_response.get_url().get_directories()
            only_re_refs = set(re_refs) - set(dirs + parsed_refs)

            all_refs = itertools.chain(parsed_refs, re_refs)
            resp_is_404 = is_404(http_response)

            for ref in unique_justseen(sorted(all_refs)):
                possibly_broken = resp_is_404 or (ref in only_re_refs)
                yield ref, fuzzable_request, http_response, possibly_broken

    def _uri_allowed_by_user_config(self, url):
        """
        :param url: A URL instance to match against the user configured filters
        :return: True if we should navigate to this URL
        """
        # I don't want w3af sending requests to 3rd parties!
        if url.get_domain() != self._target_domain:
            msg = 'web_spider will ignore %s (different domain name)'
            args = (url.get_domain(),)
            om.out.debug(msg % args)
            return False

        # Filter the URL according to the configured regular expressions
        if not self._compiled_follow_re.match(url.url_string):
            msg = 'web_spider will ignore %s (not match follow regex)'
            args = (url.url_string,)
            om.out.debug(msg % args)
            return False

        if self._compiled_ignore_re is not None:
            if self._compiled_ignore_re.match(url.url_string):
                msg = 'web_spider will ignore %s (match ignore regex)'
                args = (url.url_string,)
                om.out.debug(msg % args)
                return False

        if self._has_ignored_extension(url):
            msg = 'web_spider will ignore %s (match ignore extensions)'
            args = (url.url_string,)
            om.out.debug(msg % args)
            return False

        # Implementing only forward
        if self._only_forward and not self._is_forward(url):
            msg = 'web_spider will ignore %s (is not forward)'
            args = (url.url_string,)
            om.out.debug(msg % args)
            return False

        return True

    def _has_ignored_extension(self, new_url):
        if not self._ignore_extensions:
            return False

        return new_url.get_extension().lower() in self._ignore_extensions

    def _should_verify_extracted_url(self, url):
        """
        :param url: A newly found URL

        :return: Boolean indicating if I should send this new reference to the
                 core.
        """
        if not self._uri_allowed_by_user_config(url):
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
        fuzzable_request = FuzzableRequest(url)
        if self._variant_db.append(fuzzable_request):
            return True

        return False

    def _extract_links_and_verify(self, fuzzable_req, http_response, debugging_id):
        """
        This is a very basic method that will send the work to different
        threads. Work is generated by the _urls_to_verify_generator

        :param http_response: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        :param debugging_id: A unique identifier for this call to discover()
        """
        self.worker_pool.map_multi_args(
            self._verify_reference,
            self._urls_to_verify_generator(fuzzable_req, http_response, debugging_id)
        )

    @property
    def _chrome_crawler(self):
        if self._chrome_crawler_inst is None:
            #
            # The ChromeCrawler instance, only one should be used during the whole
            # scan. State is stored in the instance to reduce the number of events
            # being sent
            #
            self._chrome_crawler_inst = ChromeCrawler(self._uri_opener,
                                                      max_instances=self._chrome_processes)

        return self._chrome_crawler_inst

    def _crawl_with_chrome(self, fuzzable_request, http_response, debugging_id):
        """
        Crawl the URL using Chrome.

        :param fuzzable_request: The HTTP request to use as starting point
        :param http_response: The HTTP response for fuzzable_req (retrieved with uri opener)
        :param debugging_id: A unique identifier for this call to discover()
        :return: None, new fuzzable requests are written to the output queue
        """
        if not self._enable_js_crawler:
            return

        # Note that this is an async call, tasks will be queued but we don't
        # wait for the result. The result is processed in _process_chrome_queue
        self._chrome_crawler.crawl(fuzzable_request,
                                   http_response,
                                   self._http_traffic_queue,
                                   debugging_id=debugging_id,
                                   _async=True)

        # process _http_traffic_queue data
        self._start_queue_handler_thread()

        # raise exceptions in the main thread for better handling
        self._raise_chrome_crawler_exception()

    def has_pending_work(self):
        """
        Plugins might start tasks in async threads. Those tasks might be running
        after the call to audit() or discover() exits. This method is called by
        the framework to check if any of those tasks is still running.

        self._chrome_crawler.crawl(...) does start async threads to crawl the
        site using Chrome.

        This method needs to return quickly in order to prevent blocking the
        caller thread in strategy.py

        :return: True if there are async threads started by the plugin still running
        """
        if self._chrome_crawler.has_pending_work():
            return True

        if self._http_traffic_queue.qsize():
            return True

        return False

    def _start_queue_handler_thread(self):
        """
        Starts a thread that will process the data from the http_traffic_queue

        :return: None
        """
        if self._queue_handler_thread is not None:
            return

        self._queue_handler_thread = threading.Thread(target=self._process_chrome_queue,
                                                      name='QueueHandlerThread')
        self._queue_handler_thread.daemon = False
        self._queue_handler_thread.start()

    def _process_chrome_queue(self):
        """
        Process HTTP requests and responses that were found by Chrome.

        :return: None
        """
        while self._chrome_crawler_inst is not None:

            try:
                queue_data = self._http_traffic_queue.get(timeout=2.0)
            except Queue.Empty:
                continue

            b = queue_data[1]

            if isinstance(b, Exception):
                handler = self._handle_exception_from_chrome_queue
            else:
                handler = self._handle_http_traffic_from_chrome_queue

            try:
                handler(queue_data)
            except Exception as e:
                add_traceback_string(e)
                om.out.debug('Exception raised while handling data from the HTTP traffic queue: "%s"' % e)
                self._chrome_crawler_exception = e

    def _handle_http_traffic_from_chrome_queue(self, queue_data):
        request, response, debugging_id = queue_data

        self._chrome_identified_http_requests += 1

        msg = ('A total of %s HTTP requests have been read by the web_spider'
               ' from the ChromeCrawler queue')
        om.out.debug(msg % self._chrome_identified_http_requests)

        # ignore useless responses
        if response.get_code() in (404, 403, 401):
            return

        #
        # dom_dump renders the HTTP response in Chrome, then compares the DOM
        # with the static HTML received from the wire. If they are very different
        # then force_parsing is set in the HTTP response and sent to the queue.
        #
        # These HTTP responses need to be parsed here, because if we just send
        # the fuzzable request that generated it to the core, the rendered DOM
        # (which is the valuable data) will be lost
        #
        if response.force_parsing:
            if self._uri_allowed_by_user_config(response.get_uri()):

                msg = 'web_spider is parsing chrome-rendered DOM for %s (did: %s)'
                args = (response.get_uri(), debugging_id)
                om.out.debug(msg % args)

                self._extract_html_forms(request, response, debugging_id)
                self._extract_links_and_verify(request, response, debugging_id)

        #
        # All the other traffic captured in the HTTP response queue gets here;
        # this traffic might contain HTML pages that were rendered but do not
        # differ from the response received over the wire, javascript, css,
        # calls to REST APIs performed by SPA, etc.
        #
        # Check if they should be sent to the core and then add them to the
        # plugin's output queue
        #
        if not self._should_verify_extracted_url(response.get_uri()):
            return

        self.output_queue.put(request)

    def _handle_exception_from_chrome_queue(self, queue_data):
        fuzzable_request, exception, debugging_id = queue_data

        args = (fuzzable_request.get_uri(), exception, debugging_id)
        msg = 'Failed to crawl %s using chrome crawler: "%s" (did: %s)'
        om.out.debug(msg % args)

        # Exceptions will be raised in the next call to _raise_chrome_crawler_exception
        # which is made from the main thread. This allows the framework's
        # exception handler to do its job
        self._chrome_crawler_exception = exception

    def _raise_chrome_crawler_exception(self):
        if self._chrome_crawler_exception is None:
            return

        # Set to None to only raise once
        exception = self._chrome_crawler_exception
        self._chrome_crawler_exception = None
        raise exception

    def _verify_reference(self,
                          reference,
                          original_request,
                          original_response,
                          possibly_broken,
                          debugging_id,
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
        http_response = self._uri_opener.GET(reference,
                                             cache=True,
                                             headers=headers,
                                             grep=False,
                                             debugging_id=debugging_id)

        if not is_404(http_response):
            msg = '[web_spider] Found new link "%s" at "%s" (did: %s)'
            args = (reference, original_response.get_url(), debugging_id)
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
            for args in self._urls_to_verify_generator(original_request,
                                                       http_response,
                                                       debugging_id):
                self._verify_reference(*args, be_recursive=False)

        # Store the broken links
        if not possibly_broken and http_response.get_code() not in self.UNAUTH_FORBID:
            t = (http_response.get_url(), original_request.get_uri())
            self._broken_links.add(t)

    def end(self):
        """
        Called when the process ends, prints out the list of broken links.
        """
        if self._chrome_crawler_inst is not None:
            self._chrome_crawler_inst.terminate()
            self._chrome_crawler_inst = None

        self._log_broken_links()

    def _log_broken_links(self):
        if not self._broken_links:
            return

        msg = ('The following is a list of broken links that were found by'
               ' the web_spider plugin:')
        om.out.information(msg)

        def sort_by_first(a, b):
            return cmp(a[0], b[0])

        broken_links = [i for i in self._broken_links]
        broken_links.sort(sort_by_first)

        for broken, where in broken_links:
            msg = '- %s [ referenced from: %s ]'
            args = (broken, where)
            om.out.information(msg % args)

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

        d = 'Only crawl links inside the target URL'
        h = ('For example, when the target URL is set to http://abc/def/'
             ' and only_forward is set, http://abc/def/123 will be crawled'
             ' but http://abc/xyz/ will not. When only_forward is disabled'
             ' both links will be crawled.')
        o = opt_factory('only_forward', self._only_forward, d, BOOL, help=h)
        ol.add(o)

        d = 'Only crawl links that match this regular expression'
        h = 'The ignore_regex configuration parameter has precedence over follow_regex'
        o = opt_factory('follow_regex', self._follow_regex, d, REGEX, help=h)
        ol.add(o)

        d = 'DO NOT crawl links that match this regular expression'
        h = 'The ignore_regex configuration parameter has precedence over follow_regex'
        o = opt_factory('ignore_regex', self._ignore_regex, d, REGEX, help=h)
        ol.add(o)

        d = 'DO NOT crawl links that use these extensions.'
        h = ('This configuration parameter is commonly used to ignore'
             ' static files such as zip, pdf, jpeg, etc. It is possible to'
             ' ignore these files using `ignore_regex`, but configuring'
             ' this parameter is easier and performs case insensitive'
             ' matching.')
        o = opt_factory('ignore_extensions', self._ignore_extensions, d, LIST, help=h)
        ol.add(o)

        d = 'Enable / disable the JavaScript crawler'
        o = opt_factory('enable_js_crawler', self._enable_js_crawler, d, BOOL)
        ol.add(o)

        d = 'Control the number of concurrent Chrome (or Chromium) processes'
        h = ('More Chrome processes will increase the crawling speed, but will'
             ' also consume more resources (mainly memory).')
        opt = {'max': ChromePool.MAX_INSTANCES * 3,
               'min': ChromePool.MIN_INSTANCES}
        o = opt_factory('chrome_processes', self._chrome_processes, d, INT, help=h, options=opt)
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
        self._save_ignore_regex_to_config()

        self._enable_js_crawler = options_list['enable_js_crawler'].get_value()
        self._chrome_processes = options_list['chrome_processes'].get_value()

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
            self._compiled_ignore_re = None

        # Compilation of this regex can't fail because it was already
        # verified as valid at regex_option.py: see REGEX in get_options()
        self._compiled_follow_re = re.compile(self._follow_regex)

    def _save_ignore_regex_to_config(self):
        """
        This code works together with blacklist.py, where the regular expression
        is applied to outgoing HTTP request URLs and some requests are dropped.

        The problem I'm trying to solve with this code is:

            * User configures web_spider to ignore a set of URLs

            * crawl.web_spider ignores these URLs: it knows about and respects
              the ignore_regex configuration setting

            * crawl.foobar sends requests to any URLs: it is unaware of the
              web_spider configuration or how to use it

        A potential solution to this problem was to add a new exclusion setting
        to misc_settings.py, something similar to blacklist_http_request or
        blacklist_audit. The problem with that alternative is that I was
        duplicating configuration settings: web_spider had one exclusion regex
        and misc-settings had another.

        :return: None
        """
        cf.cf.save('ignore_regex', self._compiled_ignore_re)

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin is a classic web spider, it will request a URL and extract
        all links and forms from the response.

        These configurable parameters control the crawler:
            - only_forward
            - follow_regex
            - ignore_regex
            - ignore_extensions

        ignore_regex and follow_regex are commonly used to configure the
        web_spider to crawl all URLs except "/logout" or some more
        exciting link like "Reboot appliance" that would greatly reduce
        the scan test coverage.

        By default ignore_regex is an empty string (nothing is ignored) and
        follow_regex is '.*' (everything is followed). Both regular expressions
        are compiled with Python's re module and applied to URLs (with query
        string included).
        
        The ignore_extensions configuration parameter is commonly used to ignore
        static files such as zip, jpeg and pdf.

        These parameters control the JavaScript crawler:
            - enable_js_crawler
            - chrome_processes
        
        enable_js_crawler enables and disables the JavaScript crawler. By default
        the crawler is enabled and allows the scanner to identify more resources
        in the target web application.
        
        chrome_processes controls the number of concurrent Chrome (or Chromium)
        processes that the scanner will use to crawl the site. More processes
        will increase the crawl speed, but also consume more resources (mainly
        memory usage).
        """
