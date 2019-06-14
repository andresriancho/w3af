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

import w3af.core.controllers.output_manager as om


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

        self._loader_id = None
        self._frame_id = None
        self._network_idle_event = None

        self._set_initial_load_handler_state()

    def _set_initial_load_handler_state(self):
        # These keep the internal state of the page based on received events
        self._network_idle_event = None
        self._loader_id = None
        self._frame_id = None

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
        self._track_frame_and_loader_handler(message)
        self._navigation_started_handler(message)
        self._load_url_finished_handler(message)

    def _track_frame_and_loader_handler(self, message):
        """
        Track the frameId and loaderId for the main page. After sending the
        Page.Navigate message:

        {"params":
            {"url": "https://react-shopping-cart-67954.firebaseapp.com/"},
             "id": 7908361,
             "method": "Page.navigate"}

        Chrome sends:

            {"id": 7908361,
             "result": {"loaderId": "4571947E92ECA122DB51208E4353A210",
                        "frameId": "EE10237F95DADA12389C2D63C5D05DA9"}}

        We want to track the loaderId and frameId.

        It is important to notice that many messages contain a loader and frame,
        so we need to make sure that we're parsing the right message.

        :param message: The JSON message received from the websocket
        :return: None
        """
        if message.get('id', None) is None:
            return

        result = message.get('result', None)

        if result is None:
            return

        if not isinstance(result, dict):
            return

        expected_keys = {'loaderId', 'frameId'}
        if expected_keys != set(result.keys()):
            return

        loader_id = result.get('loaderId', None)
        if loader_id is None:
            return

        frame_id = result.get('frameId', None)
        if frame_id is None:
            return

        # Success!
        self._frame_id = frame_id
        self._loader_id = loader_id

    def _message_is_for_tracked_frame_and_loader(self, message):
        """
        In some cases we only care about messages that are targeted to a
        specific frameId.

        This method checks if the message passed as parameter is targeted
        to the `self._frame_id`.

        :param message: The message received from the chrome websocket
        :return: True if the message is for the tracked frameId
        """
        # PageState has not yet seen the messages to identify the current
        # loaderId and frameId
        if self._frame_id is None:
            return False

        if self._loader_id is None:
            return False

        message_str = str(message)

        if self._frame_id not in message_str:
            return False

        if self._loader_id not in message_str:
            return False

        return True

    def _navigation_started_handler(self, message):
        """
        The handler identifies events which are related to a new page being
        loaded in the browser (Page.Navigate or clicking on an element).

        :param message: The message from chrome
        :return: None
        """
        method = message.get('method', None)

        if method is None:
            return

        if not self._message_is_for_tracked_frame_and_loader(message):
            return

        navigator_started_methods = ('Page.frameScheduledNavigation',
                                     'Page.frameStartedLoading',
                                     'Page.frameNavigated')

        if method in navigator_started_methods:
            self._network_idle_event = False
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

        if method != 'Page.lifecycleEvent':
            return

        if not self._message_is_for_tracked_frame_and_loader(message):
            return

        param_name = message.get('params', {}).get('name', '')

        if param_name != 'networkIdle':
            return

        # Success!
        self._network_idle_event = True
        self._page_state = self.PAGE_STATE_LOADED

        msg = 'Page state changed to LOADED for frame %s and loader %s'
        args = (self._frame_id, self._loader_id)
        om.out.debug(msg % args)
