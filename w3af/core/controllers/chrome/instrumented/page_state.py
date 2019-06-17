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
import w3af.core.controllers.output_manager as om


class PageState(object):
    STATE_NONE = 'NONE'
    STATE_LOADING = 'LOADING'
    STATE_LOADED = 'LOADED'
    MIGHT_NAVIGATE = 'MIGHT_NAVIGATE'

    def __init__(self, frame_manager, debugging_id):
        self._frame_manager = frame_manager
        self._debugging_id = debugging_id

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id

    def get(self):
        """
        :return: The current page state, which is one of:
                    * STATE_NONE
                    * STATE_LOADING
                    * STATE_LOADED
                    * MIGHT_NAVIGATE
        """
        main_frame = self._frame_manager.get_main_frame()

        if main_frame is None:
            self._log_page_state(self.STATE_NONE)
            return self.STATE_NONE

        state = main_frame.get_overall_state()
        self._log_page_state(state)
        return state

    def force(self, state):
        main_frame = self._frame_manager.get_main_frame()
        if main_frame is None:
            return

        main_frame.force(state)
        self._log_page_state(state)

    def _log_page_state(self, state):
        main_frame = self._frame_manager.get_main_frame()
        main_frame_id = main_frame.frame_id[:5] if main_frame else None
        children_count = len(main_frame.child_frames) if main_frame else None

        msg = 'Main frame %s state is: %s (did: %s, children: %s)'
        args = (main_frame_id,
                state,
                self._debugging_id,
                children_count)
        om.out.debug(msg % args)
