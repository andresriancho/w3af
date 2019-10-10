"""
google.py

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
import urllib
import json

from w3af.core.controllers import output_manager as om
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.dc.headers import Headers
from w3af.core.data.search_engines.search_engine import SearchEngine
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.user_agent.random_user_agent import get_random_user_agent


GOOGLE_SORRY_PAGES = {'http://www.google.com/support/bin/answer.py?answer=86640',
                      'http://www.google.com/sorry/index?continue',
                      'Our systems have detected unusual traffic from'}

# Set the order in which the Google API searchers will be called by the
# google class
GOOGLE_PRIORITY_SEARCH_SEQ = ('GAjaxSearch',
                              'GMobileSearch',
                              'GStandardSearch',)


class google(SearchEngine):
    """
    This class is a wrapper for doing google searches. It allows the user to do
    GET requests to the mobile version, the Ajax API and the standard
    www.google.com page.

    :author: Andres Riancho ((andres.riancho@gmail.com))
    :author: Floyd Fuh (floyd_fuh@yahoo.de)
    """

    def __init__(self, uri_opener):
        SearchEngine.__init__(self)
        self._uri_opener = uri_opener

    def get_n_results(self, query, limit=0):
        return self.search(query, 0, count=limit)

    def search(self, query, start, count=10):
        """
        Perform a google search and return the resulting links (URLs).

        :param query: The query that we want to perform in the search engine
        :param start: The first result item
        :param count: How many results to get from start
        """
        return self._do_ordered_search(query, start, count)

    def page_search(self, query, start, count=10):
        """
        Perform a *standard* google search and return the google result
        pages (HTML).

        :param query: The query that we want to perform in the search engine
        :param start: The first result item
        :param count: How many results to get from start
        """
        return GStandardSearch(self._uri_opener, query, start, count).pages

    def _do_ordered_search(self, query, start, count):
        """
        Do the Google search by calling the Google API searchers in the order
        specified in GOOGLE_PRIORITY_SEARCH_SEQ
        """
        res = []
        _globals = globals()
        curr_count = count

        for search_class_str in GOOGLE_PRIORITY_SEARCH_SEQ:

            g_search_class = _globals[search_class_str]
            g_searcher = g_search_class(self._uri_opener, query,
                                        start, curr_count)
            res += g_searcher.links
            len_res = len(res)
            start += len_res
            curr_count -= len_res
            if len_res >= count:
                break

        msg = "Google search for: '%s' returned %s unique results"
        args = (query, len(set(res)))
        om.out.debug(msg % args)

        return res


IS_NEW = 0
FINISHED_OK = 1
FINISHED_BAD = 2
##THERE_IS_MORE = 3


class GoogleAPISearch(object):
    """
    'Abstract' base class for the Google API search implementations. This class
    shouldn't be instantiated.
    """

    def __init__(self, uri_opener):
        self._status = IS_NEW
        self._uri_opener = uri_opener
        # list of HTTPResponse objects
        self._pages = []
        # list of URLs
        self._links = []

    @property
    def status(self):
        return self._status

    @property
    def pages(self):
        if self._status == IS_NEW:
            try:
                self._pages = self._do_google_search()
            except BaseFrameworkException, w3:
                om.out.debug('%s' % w3)
                self._status = FINISHED_BAD
            else:
                self._status = FINISHED_OK
        return self._pages

    @property
    def links(self):
        if self._status == IS_NEW:
            self._links = self._extract_links(self.pages)

        return self._links

    def _do_GET(self, url, with_rand_ua=True):
        if not isinstance(url, URL):
            msg = 'The url parameter of a _do_GET must be of url.URL type.'
            raise ValueError(msg)

        if with_rand_ua:
            random_ua = get_random_user_agent()
            headers = Headers([('User-Agent', random_ua)])
        else:
            # Please note that some tests show that this is useful for the
            # mobile search.
            headers = Headers([('User-Agent', '')])

        return self._uri_opener.GET(url, headers=headers, follow_redirects=True)

    def _do_google_search(self):
        """
        Perform the google search based on implementation. This method has
        to be overridden by subclasses.
        """
        pass

    def _extract_links(self, pages):
        """
        Return list of URLs found in pages. Must be overridden by subclasses.
        """
        pass


class GAjaxSearch(GoogleAPISearch):
    """
    Search the web using Google's AJAX API. Note that Google restricts
    this API to return only the first 64 results.
    """

    GOOGLE_AJAX_SEARCH_URL = 'http://ajax.googleapis.com/ajax/services/search/web?'
    GOOGLE_AJAX_MAX_RES_PER_PAGE = 8
    GOOGLE_AJAX_MAX_START_INDEX = 56

    def __init__(self, uri_opener, query, start=0, count=10):
        """
        :param query: query to perform
        :param start: start index.
        :param count: amount of results to fetch
        """
        GoogleAPISearch.__init__(self, uri_opener)
        self._query = query
        self._start = start
        self._count = count

    def _do_google_search(self):

        res_pages = []
        start = self._start
        max_start = min(start + self._count,
                        self.GOOGLE_AJAX_MAX_START_INDEX +
                        self.GOOGLE_AJAX_MAX_RES_PER_PAGE)

        while start < max_start:
            size = min(max_start - start, self.GOOGLE_AJAX_MAX_RES_PER_PAGE)

            # Build param dict; then encode it
            params_dict = {'v': '1.0', 'q': self._query,
                           'rsz': size, 'start': start}
            params = urllib.urlencode(params_dict)

            google_url_instance = URL(self.GOOGLE_AJAX_SEARCH_URL + params)

            # Do the request
            try:
                resp = self._do_GET(google_url_instance)
            except Exception, e:
                msg = 'Failed to GET google.com AJAX API: "%s"'
                raise BaseFrameworkException(msg % e)

            try:
                # Parse the response. Convert the json string into a py dict.
                parsed_resp = json.loads(resp.get_body())
            except ValueError:
                # ValueError: No JSON object could be decoded
                msg = 'Invalid JSON returned by Google, got "%s"'
                raise BaseFrameworkException(msg % resp.get_body())

            # Expected response code is 200; otherwise raise Exception
            if parsed_resp.get('responseStatus') != 200:
                msg = ('Invalid JSON format returned by Google, response status'
                       ' needs to be 200, got "%s" instead.')
                msg %= parsed_resp.get('responseDetails')
                raise BaseFrameworkException(msg)

            # Update result pages
            res_pages.append(resp)

            # Update 'start' and continue loop
            start += self.GOOGLE_AJAX_MAX_RES_PER_PAGE

        return res_pages

    def _extract_links(self, pages):
        links = []

        for page in pages:
            # Update results list
            parsed_page = json.loads(page.get_body())
            results = parsed_page['responseData']['results']
            links += [GoogleResult(URL(res['url'])) for res in results]

        return links[:self._count]


class GStandardSearch(GoogleAPISearch):
    """
    Search the web with standard Google webpage.
    """

    GOOGLE_SEARCH_URL = 'http://www.google.com/search?'

    # TODO: Update this, it changes!!
    REGEX_STRING = 'class="r"><a href="/url\?q=(.*?)&amp;sa=U'

    # Used to find out if google will return more items
    NEXT_PAGE_STR = '<strong>Next</strong></a></td>'

    def __init__(self, uri_opener, query, start=0, count=10):
        """
        :param query: query to perform
        :param start: start index.
        :param count: amount of results to fetch
        """
        GoogleAPISearch.__init__(self, uri_opener)
        self._query = query
        self._start = start
        self._count = count

    def _do_google_search(self):
        res_pages = []

        start = self._start
        max_start = start + self._count
        there_is_more = True

        while start < max_start and there_is_more:
            params = urllib.urlencode({'hl': 'en',
                                       'q': self._query,
                                       'start': start,
                                       'sa': 'N'})

            google_url_instance = URL(self.GOOGLE_SEARCH_URL + params)
            response = self._do_GET(google_url_instance, with_rand_ua=False)

            # Remember that HTTPResponse objects have a faster "__in__" than
            # the one in strings; so string in response.get_body() is slower
            # than string in response
            for google_sorry_page in GOOGLE_SORRY_PAGES:
                if google_sorry_page in response:
                    msg = 'Google is telling us to stop doing automated tests.'
                    raise BaseFrameworkException(msg)

            if not self._has_more_items(response.get_body()):
                there_is_more = False

            # Save the result page
            res_pages.append(response)

            start += 10

        return res_pages

    def _extract_links(self, pages):
        links = []

        for resp in pages:
            for url in re.findall(self.REGEX_STRING, resp.get_body()):
                # Parse the URL
                url = urllib.unquote_plus(url)

                # Google sometimes returns a result that doesn't have a
                # protocol we add a default protocol (http)
                if not url.startswith('https://') and \
                    not url.startswith('ftp://') and \
                        not url.startswith('http://'):
                    url = 'http://' + url

                # Save the links
                try:
                    url_inst = URL(url)
                except ValueError:
                    msg = ('Google might have changed its output format.'
                           ' The regular expression failed to extract a valid'
                           ' URL from the page. Extracted (invalid) URL'
                           ' is: "%s"')
                    om.out.error(msg % url[:15])
                else:
                    links.append(GoogleResult(url_inst))

        return links[:self._count]

    def _has_more_items(self, google_page_text):
        return self.NEXT_PAGE_STR in google_page_text


class GMobileSearch(GStandardSearch):
    """
    Search the web using Google's Mobile search. Note that Google doesn't
    restrict the access to this page right now.
    """
    GOOGLE_SEARCH_URL = 'http://www.google.com/xhtml?'

    # Used to extract URLs from Google responses
    # Keep me updated!
    REGEX_STRING = 'class="r"><a href="/url\?q=(.*?)&amp;sa=U'

    # Used to find out if google will return more items.
    # Keep me updated!
    NEXT_PAGE_STR = 'Next</span></a></td></tr>'

    def __init__(self, uri_opener, query, start=0, count=10):
        """
        :param query: query to perform
        :param start: start index.
        :param count: amount of results to fetch
        """
        GoogleAPISearch.__init__(self, uri_opener)
        self._query = query
        self._start = start
        self._count = count

    def _do_google_search(self):

        start = self._start
        res_pages = []
        max_start = start + self._count
        param_dict = {'q': self._query, 'start': 0}
        there_is_more = True

        while start < max_start and there_is_more:
            param_dict['start'] = start
            params = urllib.urlencode(param_dict)

            gm_url = self.GOOGLE_SEARCH_URL + params
            gm_url_instance = URL(gm_url)
            response = self._do_GET(gm_url_instance, with_rand_ua=False)

            for google_sorry_page in GOOGLE_SORRY_PAGES:
                if google_sorry_page in response:
                    msg = 'Google is telling us to stop doing automated tests.'
                    raise BaseFrameworkException(msg)

            if not self._has_more_items(response.get_body()):
                there_is_more = False

            res_pages.append(response)
            start += 10

        return res_pages


class GoogleResult(object):
    """
    This is a dummy class that represents a search engine result.
    """
    def __init__(self, url):
        if not isinstance(url, URL):
            msg = ('The url __init__ parameter of a GoogleResult object must'
                   ' be of url.URL type.')
            raise ValueError(msg)

        self.URL = url

    def __str__(self):
        return str(self.URL)
