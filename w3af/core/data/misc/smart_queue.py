"""
smart_queue.py

Copyright 2013 Andres Riancho

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
import Queue


class QueueSpeedMeasurement(object):

    MAX_SIZE = 20000
    MAX_SECONDS_IN_THE_PAST = 600

    def __init__(self):
        self._output_timestamps = []
        self._input_timestamps = []

    def clear(self):
        self._output_timestamps = []
        self._input_timestamps = []

    def get_input_rpm(self):
        return self._calculate_rpm(self._input_timestamps)

    def get_output_rpm(self):
        return self._calculate_rpm(self._output_timestamps)

    def _item_left_queue(self):
        self._add(self._output_timestamps)

    def _item_added_to_queue(self):
        self._add(self._input_timestamps)

    def _add(self, data):
        data.append(time.time())

        while len(data) >= self.MAX_SIZE:
            data.pop(0)

    def _calculate_rpm(self, data):
        # We're only going to analyze the last MAX_SECONDS_IN_THE_PAST seconds
        max_past_time = time.time() - self.MAX_SECONDS_IN_THE_PAST
        data = [ts for ts in data if ts > max_past_time]

        if len(data) == 0:
            # The last MAX_SECONDS_IN_THE_PAST seconds had no activity,
            # the RPM is zero!
            return 0.0

        if len(data) == 1:
            # The last MAX_SECONDS_IN_THE_PAST seconds only had one
            # read / write action
            return 60.0 / self.MAX_SECONDS_IN_THE_PAST

        #
        # We have at least two read / write actions in the last
        # MAX_SECONDS_IN_THE_PAST seconds calculate the RPM!
        #
        first_item = data[0]

        # Get the last logged item time
        last_item = data[-1]

        # Count all items that were logged in the last MAX_SECONDS_IN_THE_PAST
        all_items = len(data)

        time_delta = last_item - first_item

        # Protect against cases in which the two items were added "at the same
        # time" such as https://github.com/andresriancho/w3af/issues/342
        if time_delta == 0:
            time_delta = 0.01

        # Calculate RPM and return it
        return 60.0 * all_items / time_delta


class SmartQueue(QueueSpeedMeasurement):
    """
    This queue is mostly used for debugging producer / consumer implementations,
    you shouldn't use this queue in production.

    The queue has the following features:
        * Log how much time a thread waited to put() and item
        * Log how much time an item waited in the queue to get out
    """
    def __init__(self, maxsize=0, name='Unknown'):
        super(SmartQueue, self).__init__()
        self.q = Queue.Queue(maxsize=maxsize)

        self._name = name

    def get_name(self):
        return self._name

    def get(self, block=True, timeout=None):
        try:
            data = self.q.get(block=block, timeout=timeout)
        except:
            raise
        else:
            if data is None:
                return data

            timestamp, item = data
            import w3af.core.controllers.output_manager as om

            msg = 'Item waited %.2f seconds to get out of the %s queue. Items in queue: %s / %s'
            block_time = time.time() - timestamp
            args = (round(block_time, 2), self.get_name(), self.q.qsize(), self.q.maxsize)
            om.out.debug(msg % args)

            self._item_left_queue()
            return item
    
    def put(self, item, block=True, timeout=None):
        #
        #   This is very useful information for finding bottlenecks in the
        #   framework / strategy
        #
        #   The call to .full() is not 100% accurate since another thread might
        #   read from the queue and the put() might not lock, but it is good
        #   enough for debugging.
        #
        block_start_time = None

        import w3af.core.controllers.output_manager as om

        if self.q.full() and block:
            #
            #   If you see maxsize messages like this at the end of your scan
            #   log and the scan has freezed, then you need to report a bug!
            #
            msg = ('Thread will block waiting for Queue.put() to have space in'
                   ' the %s queue. (maxsize=%s, timeout=%s)')
            args = (self.get_name(), self.q.maxsize, timeout)
            om.out.debug(msg % args)
            block_start_time = time.time()

        timestamp = time.time()

        try:
            put_res = self.q.put((timestamp, item), block=block, timeout=timeout)
        except:
            raise
        else:
            if block_start_time is not None:
                msg = ('Thread blocked %.2f seconds waiting for Queue.put() to'
                       ' have space in the %s queue. The queue\'s maxsize is'
                       ' %s.')
                block_time = time.time() - block_start_time
                args = (round(block_time, 2), self.get_name(), self.q.maxsize)
                om.out.debug(msg % args)

            self._item_added_to_queue()
            return put_res
    
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        
        return getattr(self.q, attr)
