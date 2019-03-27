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

from w3af.core.controllers.chrome.instrumented import EventException


class ChromeCrawlerJS(object):
    """
    Extract events from the DOM, dispatch events (click, etc.) and crawl
    the page using chrome
    """

    EVENTS_TO_DISPATCH = {'click'}

    def __init__(self, pool):
        self._pool = pool

    def get_name(self):
        return 'JS events'

    def crawl(self,
              chrome,
              url,
              debug=False,
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

        for event in chrome.get_all_event_listeners():
            if not self._should_dispatch_event(event):
                continue

            selector = event['selector']
            event_type = event['event_type']

            msg = 'Dispatching %s on CSS selector "%s" at page %s (did: %s)'
            args = (event_type, selector, url, debugging_id)
            om.out.debug(msg % args)

            try:
                chrome.dispatch_js_event(selector, event_type)
            except EventException:
                msg = ('The %s event on CSS selector "%s" at page %s failed'
                       ' to run because the element does not exist anymore'
                       ' (did: %s)')
                args = (event_type, selector, url, debugging_id)
                om.out.debug(msg % args)

            if chrome.navigation_started(timeout=0.5):
                msg = ('Event %s on CSS selector "%s" at page %s triggered'
                       ' a page load. Waiting for page to finish loading'
                       ' and going back in history (did: %s)')
                args = (event_type, selector, url, debugging_id)
                om.out.debug(msg % args)

                # The event triggered a full dom reload, wait for the page to
                # finish loading so that we get all the new information in the
                # proxy HTTP requests
                chrome.wait_for_load()

                # Now click on the history "back" button and wait for the page
                # to finish loading (for a second time, this is a completely
                # different page than in the line above)
                chrome.navigate_to_history_index(zeroth_navigation_index)
                chrome.wait_for_load()

    def _should_dispatch_event(self, event):
        """
        :param event: The event to analyze
        :return: True if this event should be dispatched to the browser
        """
        event_type = event['event_type']

        if event_type in self.EVENTS_TO_DISPATCH:
            return True

        return False
