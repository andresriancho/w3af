'''
grep.py

Copyright 2012 Andres Riancho

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

'''
from core.controllers.core_helpers.consumers.constants import POISON_PILL
from core.controllers.core_helpers.consumers.base_consumer import BaseConsumer


class grep(BaseConsumer):
    '''
    Consumer thread that takes requests and responses from the queue and
    analyzes them using the user-enabled grep plugins.
    '''

    def __init__(self, grep_plugins, w3af_core):
        '''
        :param in_queue: The input queue that will feed the grep plugins
        :param grep_plugins: Instances of grep plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        '''
        super(grep, self).__init__(grep_plugins, w3af_core, create_pool=False)

    def run(self):
        '''
        Consume the queue items
        '''
        while True:

            work_unit = self.in_queue.get()

            if work_unit == POISON_PILL:

                for plugin in self._consumer_plugins:
                    plugin.end()

                self.in_queue.task_done()

                break

            else:
                request, response = work_unit
                
                # Note that I'm NOT processing the grep plugin data in different
                # threads. This is because it makes no sense (these are all CPU
                # bound).
                for plugin in self._consumer_plugins:
                    try:
                        plugin.grep_wrapper(request, response)
                    except Exception, e:
                        self.handle_exception('grep', plugin.get_name(),
                                              request, e)

                self.in_queue.task_done()
