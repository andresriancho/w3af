"""
frame.py

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

from w3af.core.data.misc.variable_value_timeout import VariableValueTimeout


class Frame(object):
    STATE_NONE = 'NONE'
    STATE_LOADING = 'LOADING'
    STATE_LOADED = 'LOADED'
    MIGHT_NAVIGATE = 'MIGHT_NAVIGATE'

    # Max time that a page can be in "might navigate" state
    MAX_SECONDS_IN_MIGHT_NAVIGATE = 2

    def __init__(self, frame_id, parent_frame, debugging_id=None):
        self.frame_id = frame_id
        self.parent_frame = parent_frame
        self._debugging_id = debugging_id

        self.child_frames = dict()

        # state
        self._network_idle_event = False
        self._dom_content_loaded = False
        self._navigated_within_document = False
        self._navigated = False
        self._forced_state = VariableValueTimeout(value=None)

    def __repr__(self):
        args = (self.get_short_frame_id(),
                self.get_short_parent_frame_id(),
                self.get_short_child_frame_ids())

        return '<Frame (id: %s, parent: %s, children: %s)>' % args

    def set_navigated(self):
        self._navigated = True

        self._network_idle_event = False
        self._dom_content_loaded = False
        self._navigated_within_document = False

        if self._forced_state.get() in (self.MIGHT_NAVIGATE, self.STATE_LOADING):
            # The forced state is overwritten by the real state: Navigated!
            self._forced_state = VariableValueTimeout(value=None)

    def force(self, state):
        """
        :param state: Force the frame state to be `state`
        :return: None
        """
        if state == self.MIGHT_NAVIGATE:
            self._forced_state = VariableValueTimeout(value=self.MIGHT_NAVIGATE,
                                                      timeout=self.MAX_SECONDS_IN_MIGHT_NAVIGATE,
                                                      after_timeout=None)

        elif state in (self.STATE_LOADED, self.STATE_NONE):
            self._forced_state = VariableValueTimeout(value=state)

        elif state == self.STATE_LOADING:
            # This is used in load_url() to make sure that wait_for_load() does
            # not exit
            self._forced_state = VariableValueTimeout(value=state,
                                                      timeout=1.0,
                                                      after_timeout=None)

    def get_state(self):
        state = None
        forced_state = self._forced_state.get()

        if forced_state is not None:
            msg = 'Frame %s has forced state: %s'
            args = (self.get_short_frame_id(), forced_state)
            om.out.debug(msg % args)

            state = forced_state

        elif self._network_idle_event and self._dom_content_loaded:
            state = self.STATE_LOADED

        elif self._navigated_within_document:
            state = self.STATE_LOADED

        elif self._navigated:
            state = self.STATE_LOADING

        self._log_frame_state(state)
        return state

    def get_overall_state(self):
        """
        Query the state of current frame and his children, return the overall
        state:

            * If the parent frame has a forced state, return that state
            * If at least one of the frames is still loading: return STATE_LOADING
            * If all frames have loaded: return STATE_LOADED

        :return: The page state constant
        """
        forced_state = self._forced_state.get()

        if forced_state is not None:
            msg = 'Frame %s has forced state: %s'
            args = (self.get_short_frame_id(), forced_state)
            om.out.debug(msg % args)

            return forced_state

        #
        # Get all the frame states, including self and all child frames
        #
        all_states = {self.get_state()}

        for child in self.child_frames.values()[:]:
            all_states.add(child.get_overall_state())

        msg = 'Frame %s all_states: %s'
        args = (self.get_short_frame_id(), ', '.join(str(i) for i in all_states))
        om.out.debug(msg % args)

        #
        # In order to be in STATE_LOADED we need all frames to be in that state
        # anything different will yield STATE_NONE of STATE_LOADING
        #
        if self.STATE_NONE in all_states:
            return self.STATE_NONE

        if self.STATE_LOADING in all_states:
            return self.STATE_LOADING

        if {self.STATE_LOADED} == all_states:
            return self.STATE_LOADED

    def detach(self, frame_manager):
        #
        # detach() all child frames, and their child frames
        #
        for child_frame_id, child_frame in self.child_frames.iteritems():
            child_frame.detach(frame_manager)

            # Remove from the parent (self instance) and frame manager
            self.child_frames.pop(child_frame_id, None)
            frame_manager.remove_frame(child_frame_id)

        #
        # remove myself from the parent
        #
        if self.parent_frame is not None:
            self.parent_frame.child_frames.pop(self.frame_id, None)

        #
        # remove myself from the frame manager
        #
        frame_manager.remove_frame(self.frame_id)

    def on_navigated_within_document(self, message):
        """
        Handle Page.navigatedWithinDocument events.

        See FrameManager._on_navigated_within_document for more detailed
        information about this event.

        :param message: A message received from the chrome websocket. A dict
                        with the following format:

                        {"params": {"url": "https://react-icons-kit.now.sh/guide",
                                    "frameId": "719977C1A7DEFC2EB63EE086E716CC9D"},
                                    "method": "Page.navigatedWithinDocument"}
        :return: None
        """
        #
        # When an event is dispatched self._force_might_navigate_state() is called
        # to force the PageState.MIGHT_NAVIGATE state.
        #
        # When the dispatched event triggers an Page.navigatedWithinDocument we
        # want to catch it to quickly update the page state. Navigations within
        # the same document are quick and the framework can read the new DOM
        # immediately after.
        #
        self._navigated_within_document = True

        #
        # If there was a forced state, such as MIGHT_NAVIGATE, we remove it
        # because we already know the real state: navigated within document
        #
        self._forced_state = VariableValueTimeout(value=None)

    def handle_event(self, message):
        """
        Handle Page.lifecycleEvent events for this specific frame.

        The FrameManager._on_life_cycle_event() makes sure that this method
        only receives events that are targeted for `self.frame_id`.

        Example events are:

            {"params":
                {"timestamp": 2141.264719,
                 "loaderId": "293C999A1ED5611B0345E301698CE573",
                 "name": "load",
                 "frameId": "024CFB067AB9EF2537F39250DFD2AD5B"},
             "method": "Page.lifecycleEvent"}


            {"params":
                {"frameId": "024CFB067AB9EF2537F39250DFD2AD5B"},
             "method": "Page.frameStoppedLoading"}

        :param message: A message received from the chrome websocket
        :return: None
        """
        param_name = message.get('params', {}).get('name', '')

        if param_name == 'networkIdle':
            self._network_idle_event = True

        elif param_name == 'DOMContentLoaded':
            self._dom_content_loaded = True

    def get_short_frame_id(self):
        return self.frame_id[:5]

    def get_short_parent_frame_id(self):
        return self.parent_frame.frame_id[:5] if self.parent_frame else None

    def get_short_child_frame_ids(self):
        return [str(c.get_short_frame_id()) for c in self.child_frames.itervalues()]

    def _log_frame_state(self, state):
        msg = 'Frame %s state is: %s (did: %s, parent: %s, children: %s, oid: %s)'
        args = (self.get_short_frame_id(),
                state,
                self._debugging_id,
                self.get_short_parent_frame_id(),
                self.get_short_child_frame_ids(),
                id(self))
        om.out.debug(msg % args)
