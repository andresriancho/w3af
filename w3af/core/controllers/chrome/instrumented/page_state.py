"""
page_state.py

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
import time


class PageState(object):
    PAGE_STATE_NONE = 0
    PAGE_STATE_LOADING = 1
    PAGE_STATE_LOADED = 2
    PAGE_MIGHT_NAVIGATE = 3

    # Max time that a page can be in "might navigate" state
    MAX_SECONDS_IN_MIGHT_NAVIGATE = 2

    def __init__(self):
        self._page_state = self.PAGE_STATE_NONE
        self._timestamp_set_page_might_nav = None
        self._set_initial_load_handler_state()

    def _set_initial_load_handler_state(self):
        # These keep the internal state of the page based on received events
        self._frame_stopped_loading_event = None
        self._network_almost_idle_event = None
        self._execution_context_created = None

    def get(self):
        """
        :return: The current page state, which is one of:
                    * PAGE_STATE_NONE
                    * PAGE_STATE_LOADING
                    * PAGE_STATE_LOADED
                    * PAGE_MIGHT_NAVIGATE

                 If the page state has been in PAGE_MIGHT_NAVIGATE for more than
                 MAX_SECONDS_IN_MIGHT_NAVIGATE then the state is changed back
                 to PAGE_STATE_LOADED.
        """
        if self._timestamp_set_page_might_nav is None:
            return self._page_state

        time_in_might_navigate = time.time() - self._timestamp_set_page_might_nav
        if time_in_might_navigate >= self.MAX_SECONDS_IN_MIGHT_NAVIGATE:
            self._timestamp_set_page_might_nav = None
            self._page_state = self.PAGE_STATE_LOADED

        return self._page_state

    def force(self, state):
        self._timestamp_set_page_might_nav = None

        if state == self.PAGE_MIGHT_NAVIGATE:
            self._timestamp_set_page_might_nav = time.time()

        self._page_state = state
        self._set_initial_load_handler_state()

    def page_state_handler(self, message):
        """
        This handler defines the current page state:
            * Null: Nothing has been loaded yet
            * Loading: Chrome is loading the page
            * Done: Chrome has completed loading the page

        :param message: The message as received from chrome
        :return: None
        """
        self._navigation_started_handler(message)
        self._load_url_finished_handler(message)

    def _navigation_started_handler(self, message):
        """
        The handler identifies events which are related to a new page being
        loaded in the browser (Page.Navigate or clicking on an element).

        :param message: The message from chrome
        :return: None
        """
        method = message.get('method', None)

        navigator_started_methods = ('Page.frameScheduledNavigation',
                                     'Page.frameStartedLoading',
                                     'Page.frameNavigated')

        if method in navigator_started_methods:
            self._frame_stopped_loading_event = False
            self._network_almost_idle_event = False
            self._execution_context_created = False

            self._page_state = self.PAGE_STATE_LOADING

    def _load_url_finished_handler(self, message):
        """
        Knowing when a page has completed loading is difficult

        This handler will wait for these chrome events:
            * Page.frameStoppedLoading
            * Page.lifecycleEvent with name networkIdle

        And set the corresponding flags so that wait_for_load() can return.

        :param message: The message from chrome
        :return: True when the two events were received
                 False when one or none of the events were received
        """
        method = message.get('method', None)

        if method is None:
            return

        elif method == 'Page.frameStoppedLoading':
            self._frame_stopped_loading_event = True

        elif method == 'Runtime.executionContextCreated':
            self._execution_context_created = True

        elif method == 'Page.lifecycleEvent':
            param_name = message.get('params', {}).get('name', '')

            if param_name == 'networkAlmostIdle':
                self._network_almost_idle_event = True

        received_all = all([self._network_almost_idle_event,
                            self._frame_stopped_loading_event,
                            self._execution_context_created])

        if received_all:
            self._page_state = self.PAGE_STATE_LOADED
