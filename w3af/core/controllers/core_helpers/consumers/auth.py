"""
auth.py

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

"""
import Queue

from w3af.core.controllers.core_helpers.consumers.base_consumer import (BaseConsumer,
                                                                        task_decorator)
from w3af.core.controllers.core_helpers.consumers.constants import (POISON_PILL,
                                                                    FORCE_LOGIN)


class auth(BaseConsumer):
    """
    Thread that logins into the application every N seconds.
    """

    def __init__(self, auth_plugins, w3af_core, timeout):
        """
        :param in_queue: A queue that's used to communicate with the thread. Items
                         that might appear in this queue are:
                             * POISON_PILL
                             * FORCE_LOGIN
        :param auth_plugins: Instances of auth plugins in a list
        :param w3af_core: The w3af core that we'll use for status reporting
        :param timeout: The time to wait between each login check
        """
        super(auth, self).__init__(auth_plugins, w3af_core,
                                   thread_name='Authenticator')

        self._timeout = timeout

    def run(self):
        """
        Consume the queue items
        """
        while True:

            try:
                action = self.in_queue.get(timeout=self._timeout)
            except Queue.Empty:
                self._login()
            else:

                if action == POISON_PILL:

                    for plugin in self._consumer_plugins:
                        plugin.end()

                    self.in_queue.task_done()
                    break

                elif action == FORCE_LOGIN:

                    self._login()
                    self.in_queue.task_done()

    # Adding task here because we want to let the rest of the world know
    # that we're still doing something. The _task_done below will "undo"
    # this action.
    @task_decorator
    def _login(self):
        """
        This is the method that actually calls the plugins in order to login
        to the web application.
        """
        for plugin in self._consumer_plugins:
            try:
                if not plugin.is_logged():
                    plugin.login()
            except Exception, e:
                self.handle_exception('auth', plugin.get_name(), None, e)
    
    def async_force_login(self):
        self.in_queue_put(FORCE_LOGIN)

    def force_login(self):
        self._login()
