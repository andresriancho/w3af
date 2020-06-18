"""
variable_value_timeout.py

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


SAFE_NEVER_DEFAULT = lambda x: x


class VariableValueTimeout(object):
    def __init__(self, value, timeout=None, after_timeout=None):
        self.value = None
        self.timeout = None
        self.set_timestamp = None
        self.after_timeout = after_timeout

        self.set(value,
                 timeout=timeout,
                 after_timeout=after_timeout)

    def set(self, value, timeout=SAFE_NEVER_DEFAULT, after_timeout=SAFE_NEVER_DEFAULT):
        """

        :param value: The value to hold

        :param timeout: If a timeout is specified, the value is returned for
                        each call to get() before `timeout` is reached. The
                        timeout is set in seconds.

        :param after_timeout: After `timeout` is reached the value returned by
                              `get()` is replaced with `after_timeout`

        :return: None
        """
        if timeout is not SAFE_NEVER_DEFAULT:
            msg = 'after_timeout needs to be set if timeout is set'
            assert after_timeout is not SAFE_NEVER_DEFAULT, msg

        if after_timeout is not SAFE_NEVER_DEFAULT:
            msg = 'timeout needs to be set if after_timeout is set'
            assert timeout is not SAFE_NEVER_DEFAULT, msg

        self.value = value
        self.timeout = timeout
        self.after_timeout = after_timeout
        self.set_timestamp = time.time()

    def get(self):
        if self.timeout is None:
            # timeout already expired, no need to perform any special tasks
            # just return the current value
            return self.value

        elapsed_time = time.time() - self.set_timestamp
        if elapsed_time <= self.timeout:
            # still have a few more seconds to keep the value, return the
            # value as-is
            return self.value

        # the timeout has been exceeded!
        self.value = self.after_timeout
        self.timeout = None
        self.set_timestamp = None

        return self.value
