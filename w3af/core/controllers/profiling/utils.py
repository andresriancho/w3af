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


def should_profile():
    """
    If the environment variable W3AF_PROFILING is set to 1, then return True
    """
    _should_profile = os.environ.get('W3AF_PROFILING', '0')

    if _should_profile.isdigit() and int(_should_profile) == 1:
        return True

    return False


def get_filename_fmt():
    pid = os.getpid()
    date = datetime.datetime.today().strftime("%Y-%d-%m-%I_%M")

    return pid, date


def dump_data_every_thread(func, delay_minutes, save_thread_ptr):
    """
    This is a thread target which every X minutes
    """
    func()

    save_thread = threading.Timer(delay_minutes * 60,
                                  dump_data_every_thread,
                                  args=(func, delay_minutes, save_thread_ptr))
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
