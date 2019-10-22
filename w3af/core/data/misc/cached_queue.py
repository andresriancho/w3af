"""
cached_queue.py

Copyright 2017 Andres Riancho

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

import w3af.core.controllers.output_manager as om

from w3af.core.data.db.disk_dict import DiskDict
from w3af.core.data.misc.smart_queue import QueueSpeedMeasurement


class CachedQueue(Queue.Queue, QueueSpeedMeasurement):
    """
    The framework uses the producer / consumer design pattern extensively.
    In order to avoid high memory usage in the queues connecting the different
    parts of the framework we defined a max size.

    When a queue max size is reached, one or more threads will block. This
    line is printed during a real scan:

        Thread blocked 5.76617312431 seconds waiting for Queue.put() to have space
        in the Grep queue. The queue's maxsize is 20.

    In the case of the Grep consumer / producer the problem with a block is increased
    by the fact that HTTP responses won't reach other parts of the framework
    until the queue has space.

    Increasing the queue size would increase memory usage.

    Using an on-disk queue would increase CPU (serialization) and disk IO.

    The CacheQueue is a mix of in-memory and on-disk queue. The first N items
    are stored in memory, when more items are put() we just write them to
    disk.

    The CacheQueue object implements these methods from QueueSpeedMeasurement:
        * get_input_rpm
        * get_output_rpm

    Which allows users to understand how fast a queue is moving.
    """
    def __init__(self, maxsize=0, name='Unknown'):
        self.name = name
        self.max_in_memory = maxsize
        self.processed_tasks = 0

        QueueSpeedMeasurement.__init__(self)

        # We want to send zero to the maxsize of the Queue implementation
        # here because we can write an infinite number of items
        Queue.Queue.__init__(self, maxsize=0)

    def get_name(self):
        return self.name

    def get_processed_tasks(self):
        return self.processed_tasks

    def next_item_saved_to_memory(self):
        return len(self.memory) < self.max_in_memory

    def _init(self, maxsize):
        """
        Initialize the dicts and pointer
        :param maxsize: The max size for the queue
        """
        self.memory = dict()
        self.disk = DiskDict(table_prefix='%sCachedQueue' % self.name)
        self.get_pointer = 0
        self.put_pointer = 0

    def _qsize(self, _len=len):
        return _len(self.memory) + _len(self.disk)

    def _get_class_name(self, obj):
        try:
            return obj.__class__.__name__
        except:
            return type(obj)

    def _put(self, item):
        """
        Put a new item in the queue
        """
        #
        #   This is very useful information for finding bottlenecks in the
        #   framework / strategy
        #
        if len(self.memory) == self.max_in_memory:
            #
            #   If you see many messages like this in the scan log, then you
            #   might want to experiment with a larger maxsize for this queue
            #
            msg = ('CachedQueue.put() will write a %r item to the %s DiskDict.'
                   ' This uses more CPU and disk IO than storing in memory'
                   ' but will avoid high memory usage issues. The current'
                   ' %s DiskDict size is %s.')
            args = (self._get_class_name(item),
                    self.get_name(),
                    self.get_name(),
                    len(self.disk))
            om.out.debug(msg % args)

        #
        #   And now we just save the item to memory (if there is space) or
        #   disk (if it doesn't fit on memory)
        #
        self.put_pointer += 1

        if len(self.memory) < self.max_in_memory:
            self.memory[self.put_pointer] = item
        else:
            self.disk[self.put_pointer] = item

        self._item_added_to_queue()

    def _get(self):
        """
        Get an item from the queue
        """
        self.get_pointer += 1

        try:
            item = self.memory.pop(self.get_pointer)
        except KeyError:
            item = self.disk.pop(self.get_pointer)

            if len(self.disk):
                #
                #   If you see many messages like this in the scan log, then you
                #   might want to experiment with a larger maxsize for this queue
                #
                msg = ('CachedQueue.get() from %s DiskDict was used to read an'
                       ' item from disk. The current %s DiskDict size is %s.')
                args = (self.get_name(), self.get_name(), len(self.disk))
                om.out.debug(msg % args)

        self._item_left_queue()
        self.processed_tasks += 1
        return item

    def join(self):
        """
        Blocks until all items in the Queue have been read and processed.

        The count of unfinished tasks goes up whenever an item is added to the
        queue. The count goes down whenever a consumer thread calls task_done()
        to indicate the item was retrieved and all work on it is complete.

        When the count of unfinished tasks drops to zero, join() unblocks.
        """
        msg = 'Called join on %s with %s unfinished tasks'
        args = (self.name, self.unfinished_tasks)
        om.out.debug(msg % args)

        self.all_tasks_done.acquire()
        try:
            while self.unfinished_tasks:
                result = self.all_tasks_done.wait(timeout=5)

                if result is None:
                    msg = 'Still have %s unfinished tasks in %s join()'
                    args = (self.unfinished_tasks, self.name)
                    om.out.debug(msg % args)
        finally:
            self.all_tasks_done.release()
