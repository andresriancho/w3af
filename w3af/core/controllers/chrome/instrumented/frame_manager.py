"""
frame_manager.py

Copyright 2019 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software, you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY, without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af, if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.chrome.instrumented.frame import Frame
from w3af.core.data.fuzzer.utils import rand_alnum


class FrameManager(object):
    """
    This class keeps track of the different frames which are created during the
    process of navigating a page.

    Frames are created when a new iframe is rendered, when a page is loaded,
    when we navigate to an entry in the history, etc.

    The inspiration for this class came from Google's Puppeteer project [0].
    The implementation is not a direct translation to Python, but a customized
    and reduced re-implementation.

    [0] https://bit.ly/2MPlyRu
    """
    def __init__(self, debugging_id):
        self._debugging_id = debugging_id
        self._frames = dict()
        self._main_frame = None

        self._timestamp_set_page_might_nav = None
        self._id = rand_alnum(8)

    def set_debugging_id(self, debugging_id):
        self._debugging_id = debugging_id

    def get_main_frame(self):
        return self._main_frame

    def add_frame(self, frame):
        args = (frame.get_short_frame_id(),
                id(frame),
                self._id)
        om.out.debug('Adding frame %s (oid: %s) to FrameManager(%s)' % args)

        self._frames[frame.frame_id] = frame

    def remove_frame(self, frame_id):
        short_frame_id = frame_id[:5]
        args = (short_frame_id, self._id)
        om.out.debug('Removing %s from FrameManager(%s)' % args)

        self._frames.pop(frame_id)

    def frame_manager_handler(self, message):
        method = message.get('method', None)

        if method is None:
            return

        handlers = {
            'Page.frameAttached': self._on_frame_attached,
            'Page.frameNavigated': self._on_frame_navigated,
            'Page.navigatedWithinDocument': self._on_navigated_within_document,
            'Page.frameDetached': self._on_frame_detached,
            'Page.frameStoppedLoading': self._on_frame_stopped_loading,
            'Runtime.executionContextCreated': self._on_execution_context_created,
            'Runtime.executionContextDestroyed': self._on_execution_context_destroyed,
            'Runtime.executionContextsCleared': self._on_execution_contexts_cleared,
            'Page.lifecycleEvent': self._on_life_cycle_event,
        }

        handler = handlers.get(method, None)

        if handler is None:
            return

        return handler(message)

    def _on_frame_attached(self, message):
        """
        Handle Page.frameAttached events.

            {"method": "Page.frameAttached",
             "params": {"parentFrameId": "1DE1C73010B0A6130395341BE07D0BBF",
                        "frameId": "024CFB067AB9EF2537F39250DFD2AD5B"}}

        :param message: A message received from the chrome websocket
        :return: None
        """
        frame_id = message.get('params', {}).get('frameId', None)
        if frame_id is None:
            return

        # Prevent us from tracking the same frame twice
        if frame_id in self._frames:
            return

        parent_frame_id = message.get('params', {}).get('parentFrameId', None)
        if not parent_frame_id:
            return

        parent_frame = self._frames.get(parent_frame_id, None)
        if parent_frame is None:
            return

        # Create the new frame and track it in the frame manager
        new_frame = Frame(frame_id, parent_frame, debugging_id=self._debugging_id)
        self.add_frame(new_frame)

        # Add the new frame as a child of a parent frame
        parent_frame.child_frames[frame_id] = new_frame

    def _on_frame_navigated(self, message):
        """
        Handle Page.frameNavigated events.

            {"method": "Page.frameNavigated",
             "params":
                {"frame":
                    {"url": "http://127.0.0.1:40195/",
                     "mimeType": "text/html",
                     "loaderId": "1231BA480DA517B7383B47D560AEBBD9",
                     "id": "1DE1C73010B0A6130395341BE07D0BBF",
                     "securityOrigin": "http://127.0.0.1:40195"}}}

        This event changes the whole frame structure because the browser
        navigates to a different page (url in the message above).

        :param message: A message received from the chrome websocket
        :return: None
        """
        frame_info = message.get('params', {}).get('frame', None)
        if frame_info is None:
            return

        parent_id = frame_info.get('parentId', None)
        frame_id = frame_info.get('id', None)
        is_main_frame = parent_id is None

        if is_main_frame:
            frame = self._main_frame
        else:
            frame = self._frames.get(frame_id, None)

        if frame is None and not is_main_frame:
            return

        # Detach all child frames, when the parent frame navigates to a new
        # URL all the child frames are removed from Chrome, we should remove
        # them from our code too to mirror state
        if frame:
            for child_frame_id, child_frame in frame.child_frames:
                child_frame.detach(self)

            frame.set_navigated()

        if is_main_frame and not frame:
            # This is the first time that this frame navigates, it has to
            # be the main frame, for other frames we would see an attach
            # event first
            new_frame = Frame(frame_id, None, debugging_id=self._debugging_id)

            self._main_frame = new_frame
            self._main_frame.set_navigated()

            self.add_frame(new_frame)

    def _on_navigated_within_document(self, message):
        """
        Handle Page.navigatedWithinDocument events.

        This could be used to track the current URL loaded into a frame, but we
        don't really need that for now so using an empty implementation.

        :param message: A message received from the chrome websocket
        :return: None
        """
        pass

    def _on_frame_detached(self, message):
        """
        Handle Page.frameDetached events.

        :param message: A message received from the chrome websocket
        :return: None
        """
        frame_id = message.get('params', {}).get('frameId', None)
        if frame_id is None:
            return

        frame = self._frames.get(frame_id, None)
        if frame is None:
            return

        frame.detach(self)

    def _on_frame_stopped_loading(self, message):
        """
        Handle Page.frameStoppedLoading events.

        This could be used to track when a frame stops loading content,
        but are going to use other events to keep track of that.

        :param message: A message received from the chrome websocket
        :return: None
        """
        pass

    def _on_execution_context_created(self, message):
        """
        Handle Runtime.executionContextCreated events.

            {"params":
                {"context":
                    {"origin": "://",
                     "auxData": {"type": "default",
                                 "isDefault": true,
                                 "frameId": "1DE1C73010B0A6130395341BE07D0BBF"},
                     "id": 1,
                     "name": ""}
                },
             "method": "Runtime.executionContextCreated"}

        Puppeteer uses this to track 'worlds', whatever that means for them.
        At least for now w3af doesn't need 'worlds'

        :param message: A message received from the chrome websocket
        :return: None
        """
        pass

    def _on_execution_context_destroyed(self, message):
        """
        Handle Runtime.executionContextDestroyed events.

        Puppeteer uses this to track 'worlds', whatever that means for them.
        At least for now w3af doesn't need 'worlds'

        :param message: A message received from the chrome websocket
        :return: None
        """
        pass

    def _on_execution_contexts_cleared(self, message):
        """
        Handle Runtime.executionContextDestroyed events.

        Puppeteer uses this to track 'worlds', whatever that means for them.
        At least for now w3af doesn't need 'worlds'

        :param message: A message received from the chrome websocket
        :return: None
        """
        pass

    def _on_life_cycle_event(self, message):
        """
        Handle Page.lifecycleEvent events for all frames.

        These events happen on different frames, thus the frame manager sends
        the event to the corresponding frame for handling.

        Create the new Frame instance when receiving:

            {"method": "Page.lifecycleEvent",
             "params": {"timestamp": 19705.887835,
                        "loaderId": "B87502E3D4D3D284C1C0C6AC513C07F7",
                        "name": "commit",
                        "frameId": "0C73CD33CCAF6D25D143453737A00691"}}

        :param message: A message received from the chrome websocket
        :return: None
        """
        frame_id = message.get('params', {}).get('frameId', None)

        #
        # In some specific cases we might receive a Page.lifecycleEvent for a
        # frame that is not in self._frames. For these cases we create the
        # frame
        #
        name = message.get('params', {}).get('name', None)

        if name == 'commit' and frame_id not in self._frames:
            parent_frame = self._main_frame if self._main_frame else None

            new_frame = Frame(frame_id, parent_frame, debugging_id=self._debugging_id)

            self.add_frame(new_frame)
            self._main_frame = new_frame if self._main_frame is None else None

        #
        # Send the event to the specific frame
        #
        if frame_id is None:
            return

        frame = self._frames.get(frame_id, None)
        if frame is None:
            om.out.debug('Chrome frame %s was not found' % frame_id[:5])
            return

        return frame.handle_event(message)
