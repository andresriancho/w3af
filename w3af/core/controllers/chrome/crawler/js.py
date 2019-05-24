"""
js.py

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
# pylint: disable=E0401
from darts.lib.utils.lru import SynchronizedLRUDict
# pylint: enable=E0401

import w3af.core.controllers.output_manager as om

from w3af.core.data.misc.xml_bones import get_xml_bones
from w3af.core.controllers.chrome.instrumented.exceptions import EventException, EventTimeout
from w3af.core.controllers.chrome.crawler.state import CrawlerState
from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceException
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal

NEW_STATE_FOUND = 0
TOO_MANY_PAGE_RELOAD = 1
CONTINUE_WITH_NEXT_EVENTS = 2


class ChromeCrawlerJS(object):
    """
    Extract events from the DOM, dispatch events (click, etc.) and crawl
    the page using chrome
    """

    EVENTS_TO_DISPATCH = {'click',
                          'dblclick'}

    MAX_PAGE_RELOAD = 50
    EQUAL_RATIO_AFTER_BACK = 0.9

    MAX_CONSECUTIVE_EVENT_DISPATCH_ERRORS = 10

    MAX_INITIAL_STATES = 3

    #
    # After clicking on a tag the browser might navigate to a different URL
    # wait WAIT_FOR_LOAD_TIMEOUT seconds (max) until the URL has loaded
    #
    WAIT_FOR_LOAD_TIMEOUT = 2

    #
    # Only dispatch MAX_SIMILAR_EVENT_DISPATCH similar events and ignore the rest.
    #
    # They are similar when they match EventListener.fuzzy_matches()
    #
    MAX_SIMILAR_EVENT_DISPATCH = 5

    def __init__(self, pool, crawler_state, debugging_id):
        """
        :param pool: Chrome pool
        :param crawler_state: Crawler state instance used to share information across
                              multiple instances of ChromeCrawlerJS
        :param debugging_id: Debugging ID for easier tracking in logs
        """
        self._pool = pool
        self._debugging_id = debugging_id

        self._chrome = None
        self._url = None
        self._initial_dom = None
        self._initial_bones_xml = None
        self._reloaded_base_url_count = 0
        self._visited_urls = set()
        self._cached_xml_bones = SynchronizedLRUDict(2)

        #
        # There are two different instances of CrawlerState:
        #
        #   * Local: Stores information about the current execution and events
        #            being dispatched to the browser. Useful for understanding
        #            if the dispatched events are failing because of DOM changes,
        #            stats and logging.
        #
        #   * Global: Stores information across ChromeCrawlerJS, useful to prevent
        #             clicking on the same HTML tag that is shown in all footers
        #             of all HTML responses in a site.
        #
        self._local_crawler_state = CrawlerState()
        self._global_crawler_state = crawler_state

    def get_name(self):
        return 'JS events'

    def crawl(self,
              chrome,
              url):
        """
        Crawl the page dispatching events in chrome

        :param chrome: The chrome browser where the page is loaded
        :param url: The URL to crawl

        :return: None, all the information is sent to the core via the HTTP
                 traffic queue associated with the chrome instance. This
                 traffic was captured by the browser's proxy and holds all
                 the information for further testing and crawling.
        """
        self._chrome = chrome
        self._url = chrome.get_url()

        try:
            self._crawl_all_states()
        except ChromeInterfaceException as cie:
            msg = ('The JS crawler generated an exception in the chrome'
                   ' interface while crawling %s and will now exit.'
                   ' The exception was: "%s"')
            args = (url, cie)
            om.out.debug(msg % args)

    def _crawl_all_states(self):
        """
        In the JS crawler a state is represented by the browser's DOM. The crawler
        will perform these steps:

             * Load initial URL
             * Retrieve an initial state (DOM)
             * Dispatch events until the initial state changes
             * Start again by loading the initial URL

        Most applications will render the exact same DOM each time a URL is
        requested, other applications which maintain state (that can be changed
        by the event dispatch process) might render different DOMs for the same
        initial URL.

        :return: None, all the information is sent to the core via the HTTP
                 traffic queue associated with the chrome instance. This
                 traffic was captured by the browser's proxy and holds all
                 the information for further testing and crawling.
        """
        successfully_completed = False
        initial_state_counter = 0

        while not successfully_completed and initial_state_counter < self.MAX_INITIAL_STATES:
            try:
                successfully_completed = self._crawl_one_state()
            except MaxPageReload:
                break
            else:
                initial_state_counter += 1

    def _cached_get_xml_bones(self, dom_str):
        try:
            return self._cached_xml_bones[dom_str]
        except KeyError:
            xml_bones = get_xml_bones(dom_str)
            self._cached_xml_bones[dom_str] = xml_bones
            return xml_bones

    def _crawl_one_state(self):
        """
        Dispatch events in one state (DOM) until the state changes enough that
        it makes no sense to keep dispatching events.

        :return: None, all the information is sent to the core via the HTTP
                 traffic queue associated with the chrome instance. This
                 traffic was captured by the browser's proxy and holds all
                 the information for further testing and crawling.
        """
        self._initial_dom = self._chrome.get_dom()
        self._initial_bones_xml = self._cached_get_xml_bones(self._initial_dom)

        event_listeners = self._chrome.get_all_event_listeners(event_filter=self.EVENTS_TO_DISPATCH)

        for event_i, event in enumerate(event_listeners):

            if not self._should_dispatch_event(event):
                continue

            # Dispatch the event
            self._dispatch_event(event)

            # Logging
            self._print_stats(event_i)

            # Handle any side-effects (such as browsing to a different page or
            # big DOM changes that will break the next event dispatch calls)
            result = self._handle_event_dispatch_side_effects()

            if result == CONTINUE_WITH_NEXT_EVENTS:
                continue

            elif result == NEW_STATE_FOUND:
                # It makes no sense to keep sending events to this state because
                # the current DOM is very different from the one we initially
                # inspected to retrieve the event listeners from
                return False

            elif result == TOO_MANY_PAGE_RELOAD:
                # Too many full page reloads, need to exit
                raise MaxPageReload()

        #
        # All events were dispatched without hitting:
        #   * NEW_STATE_FOUND
        #   * TOO_MANY_PAGE_RELOAD
        #
        # But there is one more thing we need to take care of! Some events
        # might have failed to run.
        #
        # See comment in _should_dispatch_event() for a detailed explanation
        # of how this works.
        #
        if self._get_total_dispatch_error_count():
            om.out.debug('%s errors found while dispatching events. Going'
                         ' to call crawl_one_state again' % self._get_total_dispatch_error_count())
            return False

        #
        # We were able to send all events to initial state and no more states
        # were identified nor need testing
        #
        # Give the browser a second to finish up processing of all the events
        # we just fired, the last event might have triggered some action that
        # is not completed yet and we don't want to miss
        #
        self._chrome.wait_for_load(0.5)
        self._chrome.navigation_started(0.5)

        return True

    def _conditional_wait_for_load(self):
        """
        This method handles the following case:

            * Dispatched event forces browser to navigate to URL A
            * URL A was never seen before
            * We want to wait for the browser to load it in order to
              gain as much information as possible from the HTTP requests
              it generates

            ... many other actions ...

            * Dispatched event forces browser to navigate to URL A
            * URL A was seen before
            * Don't wait for the page to load, we already gathered this
              information before

        :return: None
        """
        potentially_new_url = self._chrome.get_url()

        if potentially_new_url in self._visited_urls:
            return

        self._visited_urls.add(potentially_new_url)
        self._chrome.wait_for_load(timeout=self.WAIT_FOR_LOAD_TIMEOUT)

    def _handle_event_dispatch_side_effects(self):
        """
        The algorithm was designed to dispatch a lot of events without performing
        a strict check on how that affects the DOM, or if the browser navigates
        to a different URL.

        Algorithms that performed strict checks after dispatching events all
        ended up in slow beasts.

        The key word here is *strict*. This algorithm DOES perform checks to
        verify if the DOM has changed / the page navigated to a different URL,
        but these checks are performed in a non-blocking way:

            Never wait for any specific lifeCycle event that the browser might
            or might not send!

        :return: One of the following:
                    - NEW_STATE_FOUND
                    - TOO_MANY_PAGE_RELOAD
                    - CONTINUE_WITH_NEXT_EVENTS
        """
        try:
            current_dom = self._chrome.get_dom()
        except ChromeInterfaceException:
            #
            # We get here when the DOM is not loaded yet. This is most likely
            # because the event triggered a page navigation, wait a few seconds
            # for the page to load (this will give the w3af core more info to
            # process and more crawling points) and then go back to the initial
            # URL
            #
            self._conditional_wait_for_load()
            self._reload_base_url()
            current_dom = self._chrome.get_dom()
        else:
            #
            # We get here in two cases
            #
            #   a) The browser navigated to a different URL *really quickly*
            #      and was able to create a DOM for us in that new URL
            #
            #   b) The browser is still in the initial URL and the DOM we're
            #      seeing is the one associated with that URL
            #
            # If we're in a), we want to reload the initial URL
            #
            potentially_new_url = self._chrome.get_url()

            if potentially_new_url != self._url:
                #
                # Let this new page load for 1 second so that new information
                # reaches w3af's core, and after that render the initial URL
                # again
                #
                self._conditional_wait_for_load()
                self._reload_base_url()
                current_dom = self._chrome.get_dom()

        current_bones_xml = self._cached_get_xml_bones(current_dom)

        #
        # The DOM did change! Something bad happen!
        #
        if not self._bones_xml_are_equal(self._initial_bones_xml, current_bones_xml):
            msg = ('The JS crawler noticed a big change in the DOM.'
                   ' This usually happens when the application changes state or'
                   ' when the dispatched events heavily modify the DOM.'
                   ' This happen while crawling %s, the algorithm will'
                   ' load a new DOM and continue from there (did: %s)')
            args = (self._url, self._debugging_id)
            om.out.debug(msg % args)

            #
            # Before returning NEW_STATE_FOUND we'll load the base URL in order
            # to "set the new state" in the chrome browser so that the next
            # call to _crawl_one_state() has a good start.
            #
            # Having this responsibility here is bad, but found no better way
            # to do it without adding complexity
            #
            self._reload_base_url()

            return NEW_STATE_FOUND

        #
        # Checks that might break the for loop
        #
        if self._reloaded_base_url_count > self.MAX_PAGE_RELOAD:
            msg = ('The JS crawler had to perform more than %s page reloads'
                   ' while crawling %s, the process will stop (did: %s)')
            args = (self._url, self.MAX_PAGE_RELOAD, self._debugging_id)
            om.out.debug(msg % args)
            return TOO_MANY_PAGE_RELOAD

        last_dispatch_results = self._local_crawler_state[:self.MAX_CONSECUTIVE_EVENT_DISPATCH_ERRORS]
        last_dispatch_results = [el.state for el in last_dispatch_results]

        all_failed = True
        for state in last_dispatch_results:
            if state != EventDispatchLogUnit.FAILED:
                all_failed = False
                break

        if all_failed:
            msg = ('Too many consecutive event dispatch errors were found while'
                   ' crawling %s, the process will stop (did: %s)')
            args = (self._url, self._debugging_id)
            om.out.debug(msg % args)
            return NEW_STATE_FOUND

        return CONTINUE_WITH_NEXT_EVENTS

    def _bones_xml_are_equal(self, bones_xml_a, bones_xml_b):
        return fuzzy_equal(bones_xml_a,
                           bones_xml_b,
                           self.EQUAL_RATIO_AFTER_BACK)

    def _print_stats(self, event_i):
        event_types = {}

        for event_dispatch_log_unit in self._local_crawler_state:
            event_type = event_dispatch_log_unit.event['event_type']
            if event_type in event_types:
                event_types[event_type] += 1
            else:
                event_types[event_type] = 1

        msg = ('Processing event %s out of (unknown) for %s.'
               ' Event dispatch error count is %s.'
               ' Already processed %s events with types: %r. (did: %s)')
        args = (event_i,
                self._url,
                self._get_total_dispatch_error_count(),
                self._get_total_dispatch_count(),
                event_types,
                self._debugging_id)

        om.out.debug(msg % args)

    def _get_total_dispatch_error_count(self):
        return len([i for i in self._local_crawler_state if i.state == EventDispatchLogUnit.FAILED])

    def _get_total_dispatch_count(self):
        return len([i for i in self._local_crawler_state if i.state != EventDispatchLogUnit.IGNORED])

    def _dispatch_event(self, event):
        selector = event['selector']
        event_type = event['event_type']

        msg = 'Dispatching "%s" on CSS selector "%s" at page %s (did: %s)'
        args = (event_type, selector, self._url, self._debugging_id)
        om.out.debug(msg % args)

        try:
            self._chrome.dispatch_js_event(selector, event_type)
        except EventException:
            msg = ('The "%s" event on CSS selector "%s" at page %s failed'
                   ' to run because the element does not exist anymore'
                   ' (did: %s)')
            args = (event_type, selector, self._url, self._debugging_id)
            om.out.debug(msg % args)

            self._append_event_to_logs(event, EventDispatchLogUnit.FAILED)

            return False

        except EventTimeout:
            msg = ('The "%s" event on CSS selector "%s" at page %s failed'
                   ' to run in the given time (did: %s)')
            args = (event_type, selector, self._url, self._debugging_id)
            om.out.debug(msg % args)

            self._append_event_to_logs(event, EventDispatchLogUnit.FAILED)

            return False

        self._append_event_to_logs(event, EventDispatchLogUnit.SUCCESS)

        return True

    def _append_event_to_logs(self, event, state):
        url = self._url[:]
        event_dispatch_log_unit = EventDispatchLogUnit(event, state, url)

        self._local_crawler_state.append_event_to_log(event_dispatch_log_unit)
        self._global_crawler_state.append_event_to_log(event_dispatch_log_unit)

    def _reload_base_url(self):
        self._reloaded_base_url_count += 1
        self._chrome.load_url(self._url)
        return self._chrome.wait_for_load()

    def _ignore_event(self, event):
        self._append_event_to_logs(event, EventDispatchLogUnit.IGNORED)

    def _should_dispatch_event(self, event):
        """
        Filters the event listeners returned from the browser using the
        event dispatch log to:

            * Prevent duplicated events (exactly equal and fuzzy matching)
              from being sent

            * Retry failed events

        At the beginning all the events are returned as they arrive from the
        browser, but after a few events are dispatched the event dispatch log
        starts to filter which events will be returned.

        Use cases this covers:

            1. Simple page: There are 10 event listeners, in the first call
                            to _crawl_one_state() we're able to successfully
                            dispatch all events.

                            None of the tags that had event listeners at the
                            moment of calling get_all_event_listeners() were
                            removed from the DOM after dispatching one of
                            those 10 events.

                            We got 100% test coverage in the first call to
                            _crawl_one_state().

            2. Complex page: There are 10 event listeners, in the first call
                             to _crawl_one_state() two of the dispatched events
                             fail to run: the selectors were unable to find the
                             tag which was associated with the event.

                             This is most likely because one of the 8 events that
                             was dispatched modified the DOM and removed that
                             tag.

                             The first call to _crawl_one_state() finishes with
                             80% test coverage (2 out of 10 were not triggered).

                             A new call to _crawl_one_state() is made. In this
                             second call we check the event dispatch log and make
                             sure that the events that failed in the previous
                             call are run (if they still exist in the current
                             DOM) and the ones that were successfully sent in the
                             past are NOT.

                             The second call to _crawl_one_state() will run the
                             2 missing events, achieving 100% test coverage, and
                             then run any new event that is yield by
                             get_all_event_listeners().

        :param event: The event to analyze
        :return: True if this event should be dispatched to the browser
        """
        current_event_type = event['event_type']

        #
        # Only dispatch events if type in EVENTS_TO_DISPATCH
        #
        if current_event_type not in self.EVENTS_TO_DISPATCH:
            self._ignore_event(event)
            return False

        #
        # Do not dispatch similar events more than MAX_SIMILAR_EVENT_DISPATCH
        # times, and don't dispatch the exact same event twice
        #
        similar_successfully_dispatched = 0

        # Iterate in reverse, similar events were most likely sent a few seconds
        # ago by this or other crawler instance
        for event_dispatch_log_unit in reversed(self._global_crawler_state):
            if event_dispatch_log_unit.state in (EventDispatchLogUnit.FAILED,
                                                 EventDispatchLogUnit.IGNORED):
                continue

            if event_dispatch_log_unit.event == event and event_dispatch_log_unit.uri == self._url:
                break

            if event_dispatch_log_unit.event.fuzzy_matches(event):
                similar_successfully_dispatched += 1

            if similar_successfully_dispatched >= self.MAX_SIMILAR_EVENT_DISPATCH:
                break
        else:
            # Was able to complete the whole for loop without hitting the "break"
            # clause, this means that there are no similar events in the log and
            # the current event should be dispatched
            return True

        msg = ('Ignoring "%s" event on selector "%s" and URL "%s" because'
               ' the same event, or a very similar one, was already'
               ' dispatched (did: %s)')
        args = (current_event_type,
                event['selector'],
                self._url,
                self._debugging_id)
        om.out.debug(msg % args)

        self._ignore_event(event)
        return False


class EventDispatchLogUnit(object):
    IGNORED = 0
    SUCCESS = 1
    FAILED = 2

    __slots__ = (
        'state',
        'event',
        'uri'
    )

    def __init__(self, event, state, uri):
        assert state in (self.IGNORED, self.SUCCESS, self.FAILED), 'Invalid state'

        self.state = state
        self.event = event
        self.uri = uri

    def get_state_as_string(self):
        if self.state == EventDispatchLogUnit.IGNORED:
            return 'IGNORED'

        if self.state == EventDispatchLogUnit.SUCCESS:
            return 'SUCCESS'

        if self.state == EventDispatchLogUnit.FAILED:
            return 'FAILED'

    def __repr__(self):
        state = self.get_state_as_string()
        return '<EventDispatchLogUnit %s %s>' % (state, self.event)


class MaxPageReload(Exception):
    pass
