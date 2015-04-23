"""
utils.py

Copyright 2014 Andres Riancho

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
import os
import datetime
import threading


def get_filename_fmt():
    pid = os.getpid()
    date = datetime.datetime.today().strftime("%Y-%d-%m-%I_%M")

    return pid, date


def dump_data_every_thread(func, delay_minutes, save_thread_ptr):
    """
    This is a thread target which every X minutes
    """
    try:
        func()
    except KeyboardInterrupt:
        # Ok, this one failed because the user was playing with Ctrl+C, but we
        # queue the next run in the lines below
        pass

    save_thread = threading.Timer(delay_minutes * 60,
                                  dump_data_every_thread,
                                  args=(func, delay_minutes, save_thread_ptr))
    save_thread.name = 'ProfilingDumpData'
    save_thread.daemon = True
    save_thread.start()

    if save_thread_ptr:
        # Remove the old one if it exists in the ptr
        save_thread_ptr.pop(0)

    save_thread_ptr.append(save_thread)


def cancel_thread(save_thread_ptr):
    if save_thread_ptr:
        save_thread = save_thread_ptr[0]
        save_thread.cancel()
        save_thread_ptr.pop(0)
