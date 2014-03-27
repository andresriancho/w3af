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
import itertools
import re

import w3af.core.controllers.output_manager as om
import w3af.core.data.dc.form as form
import w3af.core.data.kb.config as cf
import w3af.core.data.parsers.parser_cache as parser_cache
import w3af.core.data.constants.response_codes as http_constants

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.exceptions import BaseFrameworkException, ScanMustStopOnUrlError
from w3af.core.controllers.misc.itertools_toolset import unique_justseen

from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.db.variant_db import VariantDB
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.dc.headers import Headers
from w3af.core.data.fuzzer.form_filler import smart_fill
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import BOOL, REGEX
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.request.HTTPPostDataRequest import HTTPPostDataRequest


class web_spider(CrawlPlugin):
    """
    Crawl the web application.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    NOT_404 = set([http_constants.UNAUTHORIZED,
                   http_constants.FORBIDDEN])

    def __init__(self):
        CrawlPlugin.__init__(self)

        # Internal variables
        self._compiled_ignore_re = None
        self._compiled_follow_re = None
        self._broken_links = DiskSet()
        self._first_run = True
        self._known_variants = VariantDB()
        self._already_filled_form = ScalableBloomFilter()

        # User configured variables
        self._ignore_regex = ''
        self._follow_regex = '.*'
        self._only_forward = False
        self._compile_re()

    def crawl(self, fuzzable_req):
        """
        Searches for links on the html.

        :param fuzzable_req: A fuzzable_req instance that contains
                             (among other things) the URL to test.
        """
        self._handle_first_run()

        #
        # If it is a form, then smart_fill the parameters to send something that
        # makes sense and will allow us to cover more code.
        #
        if isinstance(fuzzable_req, HTTPPostDataRequest):

            if fuzzable_req.get_url() in self._already_filled_form:
                return

            fuzzable_req = self._fill_form(fuzzable_req)

        # Send the HTTP request,
        resp = self._uri_opener.send_mutant(fuzzable_req)

        # Nothing to do here...
        if resp.get_code() == 401:
            return

        fuzz_req_list = self._create_fuzzable_requests(
            resp,
            request=fuzzable_req,
            add_self=False
        )
        
        for fr in fuzz_req_list:
            self.output_queue.put(fr)

        self._extract_links_and_verify(resp, fuzzable_req)

    def _handle_first_run(self):
        if self._first_run:
            # I have to set some variables, in order to be able to code
            # the "only_forward" feature
            self._first_run = False
            self._target_urls = [i.get_domain_path() for i in cf.cf.get('targets')]

            #    The following line triggered lots of bugs when the "stop" button
            #    was pressed and the core did this: "cf.cf.save('targets', [])"
            #self._target_domain = cf.cf.get('targets')[0].get_domain()
            #    Changing it to something awful but bug-free.
            targets = cf.cf.get('targets')
            if not targets:
                return
            else:
                self._target_domain = targets[0].get_domain()
                
    def _urls_to_verify_generator(self, resp, fuzzable_req):
        """
        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        #
        # Note: I WANT to follow links that are in the 404 page.
        #

        # Modified when I added the PDFParser
        # I had to add this x OR y stuff, just because I don't want
        # the SGML parser to analyze a image file, its useless and
        # consumes CPU power.
        if resp.is_text_or_html() or resp.is_pdf() or resp.is_swf():
            original_url = resp.get_redir_uri()
            try:
                doc_parser = parser_cache.dpc.get_document_parser_for(resp)
            except BaseFrameworkException, w3:
                om.out.debug('Failed to find a suitable document parser. '
                             'Exception "%s"' % w3)
            else:
                # Note:
                # - With parsed_refs I'm 100% that it's really
                # something in the HTML that the developer intended to add.
                #
                # - The re_refs are the result of regular expressions,
                # which in some cases are just false positives.

                parsed_refs, re_refs = doc_parser.get_references()

                # I also want to analyze all directories, if the URL I just
                # fetched is:
                # http://localhost/a/b/c/f00.php I want to GET:
                # http://localhost/a/b/c/
                # http://localhost/a/b/
                # http://localhost/a/
                # http://localhost/
                # And analyze the responses...
                dirs = resp.get_url().get_directories()
                only_re_refs = set(re_refs) - set(dirs + parsed_refs)

                all_refs = itertools.chain(dirs, parsed_refs, re_refs)

                for ref in unique_justseen(sorted(all_refs)):

                    # Ignore myself
                    if ref == resp.get_uri():
                        continue

                    # I don't want w3af sending requests to 3rd parties!
                    if ref.get_domain() != self._target_domain:
                        continue

                    # Filter the URL's according to the configured regexs
                    urlstr = ref.url_string
                    if not self._compiled_follow_re.match(urlstr) or \
                    self._compiled_ignore_re.match(urlstr):
                        continue

                    if self._only_forward:
                        if not self._is_forward(ref):
                            continue

                    # Work with the parsed references and report broken
                    # links. Then work with the regex references and DO NOT
                    # report broken links
                    if self._need_more_variants(ref):
                        self._known_variants.append(ref)
                        possibly_broken = ref in only_re_refs
                        yield ref, fuzzable_req, original_url, possibly_broken

    def _extract_links_and_verify(self, resp, fuzzable_req):
        """
        This is a very basic method that will send the work to different
        threads. Work is generated by the _urls_to_verify_generator

        :param resp: HTTP response object
        :param fuzzable_req: The HTTP request that generated the response
        """
        self.worker_pool.map_multi_args(
            self._verify_reference,
            self._urls_to_verify_generator(resp, fuzzable_req)
        )

    def _fill_form(self, fuzzable_req):
        """
        Fill the HTTP request form that is passed as fuzzable_req.
        :return: A filled form
        """
        self._already_filled_form.add(fuzzable_req.get_url())

        to_send = fuzzable_req.get_dc().copy()

        for param_name in to_send:

            # I do not want to mess with the "static" fields
            if isinstance(to_send, form.Form):
                if to_send.get_type(param_name) in ('checkbox', 'file',
                                                    'radio', 'select'):
                    continue

            # Set all the other fields, except from the ones that have a
            # value set (example: hidden fields like __VIEWSTATE).
            for elem_index in xrange(len(to_send[param_name])):

                # TODO: Should I ignore it because it already has a value?
                if to_send[param_name][elem_index] != '':
                    continue

                # SmartFill it!
                to_send[param_name][elem_index] = smart_fill(param_name)

        fuzzable_req.set_dc(to_send)
        return fuzzable_req

    def _need_more_variants(self, new_reference):
        """
        :param new_reference: The new URL that we want to see if its a variant
            of at most MAX_VARIANTS references stored in self._already_crawled.

        :return: True if I need more variants of ref.

        Basically, the idea is to crawl the whole website, but if we are
        crawling a site like youtube.com that has A LOT of links with the form:
            - http://www.youtube.com/watch?v=xwLNu5MHXFs
            - http://www.youtube.com/watch?v=JEzjwifH4ts
            - ...
            - http://www.youtube.com/watch?v=something_here

        Then we don't actually want to follow all the links to all the videos!
        So we are going to follow a decent number of variant URLs (in this
        case, video URLs) to see if we can find something interesting in those
        links, but after a fixed number of variants, we will start ignoring all
        those variants.
        """
        if self._known_variants.need_more_variants(new_reference):
            return True
        else:
            msg = ('Ignoring new reference "%s" (it is simply a variant).'
                   % new_reference)
            om.out.debug(msg)
            return False

    def _verify_reference(self, reference, original_request,
                          original_url, possibly_broken):
        """
        This method GET's every new link and parses it in order to get
        new links and forms.
        """
        #
        # Remember that this "breaks" the cache=True in most cases!
        #     headers = { 'Referer': original_url }
        #
        # But this does not, and it is friendlier that simply ignoring the
        # referer
        #
        referer = original_url.base_url().url_string
        headers = Headers([('Referer', referer)])

        try:
            resp = self._uri_opener.GET(reference, cache=True,
                                        headers=headers)
        except ScanMustStopOnUrlError:
            pass
        else:
            fuzz_req_list = []

            if is_404(resp):
                # Note: I WANT to follow links that are in the 404 page, but
                # if the page I fetched is a 404 then it should be ignored.
                #
                # add_self will be True when the response code is 401 or 403
                # which is something needed for other plugins to keep poking
                # at that URL
                #
                # add_self will be False in all the other cases, for example
                # in the case where the response code is a 404, because we don't
                # want to return a 404 to the core.
                add_self = resp.get_code() in self.NOT_404
                fuzz_req_list = self._create_fuzzable_requests(resp,
                                                               request=original_request,
                                                               add_self=add_self)
                if not possibly_broken and not add_self:
                    t = (resp.get_url(), original_request.get_uri())
                    self._broken_links.add(t)
            else:
                om.out.debug('Adding relative reference "%s" '
                             'to the result.' % reference)
                frlist = self._create_fuzzable_requests(resp,
                                                        request=original_request)
                fuzz_req_list.extend(frlist)

            # Process the list.
            for fuzz_req in fuzz_req_list:
                fuzz_req.set_referer(referer)
                self.output_queue.put(fuzz_req)

    def end(self):
        """
        Called when the process ends, prints out the list of broken links.
        """
        if len(self._broken_links):

            om.out.information('The following is a list of broken links that '
                               'were found by the web_spider plugin:')
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

        d = 'When crawling only follow links to paths inside the one given'\
            ' as target.'
        o = opt_factory('only_forward', self._only_forward, d, BOOL)
        ol.add(o)

        d = 'When crawling only follow which that match this regular'\
            ' expression. Please note that ignore_regex has precedence over'\
            ' follow_regex.'
        o = opt_factory('follow_regex', self._follow_regex, d, REGEX)
        ol.add(o)

        d = 'When crawling, DO NOT follow links that match this regular'\
            ' expression. Please note that ignore_regex has precedence over'\
            ' follow_regex.'
        o = opt_factory('ignore_regex', self._ignore_regex, d, REGEX)
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

        Three configurable parameter exist:
            - only_forward
            - ignore_regex
            - follow_regex

        ignore_regex and follow_regex are commonly used to configure the
        web_spider to spider all URLs except the "logout" or some other more
        exciting link like "Reboot Appliance" that would make the w3af run
        finish without the expected result.

        By default ignore_regex is an empty string (nothing is ignored) and
        follow_regex is '.*' (everything is followed). Both regular expressions
        are normal regular expressions that are compiled with Python's re module.

        The regular expressions are applied to the URLs that are found using the
        match function.
        """
