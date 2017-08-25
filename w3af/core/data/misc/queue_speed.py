"""
queue_speed.py

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
import Queue
import time

import w3af.core.controllers.output_manager as om


class QueueSpeed(object):
    
    MAX_SIZE = 100
    
    def __init__(self, maxsize=0, name='Unknown'):
        self.q = Queue.Queue(maxsize=maxsize)

        self._name = name
        self._output_data = [] 
        self._input_data = []

    def get_name(self):
        return self._name

    def clear(self):
        self._output_data = [] 
        self._input_data = []
    
    def _add(self, true_false, data):
        data.append((true_false, time.time()))

        while len(data) >= self.MAX_SIZE:
            data.pop(0)
    
    def _item_left_queue(self):
        self._add(True, self._output_data)

    def _item_added_to_queue(self):
        self._add(True, self._input_data)

    def _calculate_rpm(self, data):
        # Verify that I have everything I need to make the calculations
        if len([True for (added, _) in data if added]) < 1:
            return None
        
        if len(data) < 2:
            return None
        
        # Get the first logged item time, only a real item not a check made
        # by get_input_rpm / get_output_rpm
        first_item_time = [data_time for (added, data_time) in data if added][0]
        
        # Get the last logged item time
        last_item_time = data[-1][1]
        
        # Count all items that were logged
        all_items = len([True for (added, _) in data if added])
        
        time_delta = last_item_time - first_item_time

        if time_delta == 0:
            # https://github.com/andresriancho/w3af/issues/342
            return None

        # Calculate RPM and return it
        return 60.0 * all_items / time_delta

    def get_input_rpm(self):
        self._add(False, self._input_data)

        return self._calculate_rpm(self._input_data)
    
    def get_output_rpm(self):
        self._add(False, self._output_data)

        return self._calculate_rpm(self._output_data)
        
    def get(self, block=True, timeout=None):
        try:
            item = self.q.get(block=block, timeout=timeout)
        except:
            raise
        else:
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

        try:
            put_res = self.q.put(item, block=block, timeout=timeout)
        except:
            raise
        else:
            if block_start_time is not None:
                msg = ('Thread blocked %s seconds waiting for Queue.put() to'
                       ' have space in the %s queue. The queue\'s maxsize is'
                       ' %s.')
                block_time = time.time() - block_start_time
                args = (block_time, self.get_name(), self.q.maxsize)
                om.out.debug(msg % args)

            self._item_added_to_queue()
            return put_res
    
    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        
        return getattr(self.q, attr)
