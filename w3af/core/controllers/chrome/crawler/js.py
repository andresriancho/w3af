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
import w3af.core.controllers.output_manager as om

from w3af.core.data.misc.xml_bones import get_xml_bones
from w3af.core.controllers.chrome.instrumented import EventException, EventTimeout
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_equal
from w3af.core.controllers.chrome.devtools.exceptions import ChromeInterfaceException


class ChromeCrawlerJS(object):
    """
    Extract events from the DOM, dispatch events (click, etc.) and crawl
    the page using chrome
    """

    EVENTS_TO_DISPATCH = {'click',
                          'dblclick'}

    MAX_BROWSER_BACK = 50
    EQUAL_RATIO_AFTER_BACK = 0.9

    MAX_EVENT_DISPATCH_ERRORS = 10

    def __init__(self, pool):
        self._pool = pool

        self._event_dispatch_errors = 0

    def get_name(self):
        return 'JS events'

    def crawl(self,
              chrome,
              url,
              debugging_id=None):
        """
        Get all event listeners and click on them.

        :param chrome: The chrome browser where the page is loaded
        :param debugging_id: Debugging ID for easier tracking in logs
        :param url: The URL to crawl
        :return: None, all the information is sent to the core via HTTP traffic
                 captured by the browser's proxy
        """
        try:
            self._crawl_impl(chrome,
                             debugging_id=debugging_id)
        except ChromeInterfaceException as cie:
            msg = ('The JS crawler generated an exception in the chrome'
                   ' interface while crawling %s and will now exit.'
                   ' The exception was: "%s"')
            args = (url, cie)
            om.out.debug(msg % args)

    def _crawl_impl(self,
                    chrome,
                    debugging_id=None):
        """
        Get all event listeners and click on them.

        :param chrome: The chrome browser where the page is loaded
        :param debugging_id: Debugging ID for easier tracking in logs
        :return: None, all the information is sent to the core via HTTP traffic
                 captured by the browser's proxy
        """
        zeroth_navigation_index = chrome.get_navigation_history_index()
        url = chrome.get_url()

        initial_dom = chrome.get_dom()
        initial_bones_xml = None
        back_button_press_count = 0
        processed_events = []

        event_listeners = chrome.get_all_event_listeners(event_filter=self.EVENTS_TO_DISPATCH)

        for event_i, event in enumerate(event_listeners):
            if not self._should_dispatch_event(url, event, processed_events, debugging_id):
                continue

            if self._too_many_errors(url, debugging_id):
                break

            self._print_stats(event_i, processed_events, url, debugging_id)

            # Prevent duplicated processing
            processed_events.append(event)

            # Dispatch the event
            self._dispatch_event(chrome, event, url, debugging_id)

            # Handle any side-effects (such as browsing to a different page)
            handler_result = self._handle_event_trigger_side_effects(chrome,
                                                                     event,
                                                                     url,
                                                                     debugging_id,
                                                                     zeroth_navigation_index,
                                                                     back_button_press_count,
                                                                     initial_dom,
                                                                     initial_bones_xml)

            (dom_changed_after_browser_back,
             initial_bones_xml,
             back_button_press_count) = handler_result

            # Do not send the next event to this new / unknown DOM
            # TODO: Parse and send data to w3af-core
            if dom_changed_after_browser_back:
                msg = ('The crawler detected a big change in the DOM after'
                       ' clicking on the back button to go back to %s, will'
                       ' not send any more events to this URL.')
                args = (url,)
                om.out.debug(msg % args)
                break

    def _too_many_errors(self, url, debugging_id):
        """
        :return: True when the crawling process at _crawl_impl() has found
                 too many errors and should stop.
        """
        if self._event_dispatch_errors > self.MAX_EVENT_DISPATCH_ERRORS:
            msg = ('Too many event dispatch errors were found while crawling %s,'
                   ' the crawling process will stop now (did: %s)')
            args = (url, debugging_id)
            om.out.debug(msg % args)

            return True

        return False

    def _print_stats(self, event_i, processed_events, url, debugging_id):
        event_types = {}

        for processed_event in processed_events:
            event_type = processed_event['event_type']
            if event_type in event_types:
                event_types[event_type] += 1
            else:
                event_types[event_type] = 1

        msg = ('Processing event %s out of (unknown) for %s.'
               ' Event dispatch error count is %s.'
               ' Already processed %s events with types: %r. (did: %s)')
        args = (event_i,
                url,
                self._event_dispatch_errors,
                len(processed_events),
                event_types,
                debugging_id)

        om.out.debug(msg % args)

    def _dispatch_event(self, chrome, event, url, debugging_id):
        selector = event['selector']
        event_type = event['event_type']

        msg = 'Dispatching "%s" on CSS selector "%s" at page %s (did: %s)'
        args = (event_type, selector, url, debugging_id)
        om.out.debug(msg % args)

        try:
            chrome.dispatch_js_event(selector, event_type)
        except EventException:
            msg = ('The "%s" event on CSS selector "%s" at page %s failed'
                   ' to run because the element does not exist anymore'
                   ' (did: %s)')
            args = (event_type, selector, url, debugging_id)
            om.out.debug(msg % args)

            self._event_dispatch_errors += 1

            return False

        except EventTimeout:
            msg = ('The "%s" event on CSS selector "%s" at page %s failed'
                   ' to run in the given time (did: %s)')
            args = (event_type, selector, url, debugging_id)
            om.out.debug(msg % args)

            self._event_dispatch_errors += 1

            return False

        return True

    def _handle_event_trigger_side_effects(self,
                                           chrome,
                                           event,
                                           url,
                                           debugging_id,
                                           zeroth_navigation_index,
                                           back_button_press_count,
                                           initial_dom,
                                           initial_bones_xml):
        """
        :return: If the DOM changed after a browser back button was pressed
        """
        if not chrome.navigation_started(timeout=0.5):
            # This is the easiest case, the event we just dispatched did not
            # trigger a full page reload on the other side
            return False, initial_bones_xml, back_button_press_count

        # The event triggered a full dom reload, wait for the page to
        # finish loading so that we get all the new information in the
        # proxy HTTP requests
        selector = event['selector']
        event_type = event['event_type']

        msg = ('Event %s on CSS selector "%s" at page %s triggered'
               ' a page load. Waiting for page to finish loading'
               ' and going back in history (did: %s)')
        args = (event_type, selector, url, debugging_id)
        om.out.debug(msg % args)

        chrome.wait_for_load()

        # And now we go back to the initial URL that was loaded in chrome
        self._browser_back(chrome,
                           zeroth_navigation_index)

        back_button_press_count += 1

        # The problem we might have now is that when we pressed "back" the
        # page that is loaded is different from the one we initially saw
        #
        # This happens with some applications that keep server-side state
        # such as wizards.
        #
        # To handle this issue we compare the initial_dom with the one we
        # currently have in the browser using get_xml_bones and a fuzzy string
        # match method
        doms_are_equal, initial_bones_xml = self._doms_are_equal(initial_dom,
                                                                 initial_bones_xml,
                                                                 chrome)

        if doms_are_equal:
            # This is the easiest to handle and most common case, nothing
            # else to be done here, we just continue processing the next
            # event
            return False, initial_bones_xml, back_button_press_count

        return True, initial_bones_xml, back_button_press_count

    def _doms_are_equal(self, initial_dom, initial_bones_xml, chrome):
        if initial_bones_xml is None:
            initial_bones_xml = get_xml_bones(initial_dom)

        current_dom = chrome.get_dom()
        current_bones_xml = get_xml_bones(current_dom)

        return fuzzy_equal(initial_bones_xml,
                           current_bones_xml,
                           self.EQUAL_RATIO_AFTER_BACK), initial_bones_xml

    def _browser_back(self, chrome, navigation_index):
        # Now click on the history "back" button and wait for the page
        # to finish loading (for a second time, this is a completely
        # different page than in the line above)
        chrome.navigate_to_history_index(navigation_index)
        chrome.wait_for_load()

    def _should_dispatch_event(self, url, event, processed_events, debugging_id):
        """
        :param event: The event to analyze
        :return: True if this event should be dispatched to the browser
        """
        current_event_type = event['event_type']
        current_event_key = event.get_type_selector()

        # Do not dispatch the same event twice
        for processed_event in processed_events:
            if current_event_key == processed_event.get_type_selector():
                msg = ('Ignoring "%s" event on selector "%s" and URL "%s"'
                       ' because it was already sent. This happens when the'
                       ' application attaches more than one event listener'
                       ' to the same event and element. (did: %s)')
                args = (current_event_type,
                        event['selector'],
                        url,
                        debugging_id)
                om.out.debug(msg % args)
                return False

        # Only dispatch events if type in EVENTS_TO_DISPATCH
        if current_event_type in self.EVENTS_TO_DISPATCH:
            return True

        return False