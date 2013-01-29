'''
utils.py

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
import time
import gtk


def refresh_gui(delay=0.0001, wait=0.0001):
    """Use up all the events waiting to be run

    :param delay: Time to wait before using events
    :param wait: Time to wait between iterations of events

    This function will block until all pending events are emitted. This is
    useful in testing to ensure signals and other asynchronous functionality
    is required to take place.
    """
    time.sleep(delay)
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)
        time.sleep(wait)
