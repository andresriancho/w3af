"""
monkey_patch_debug.py

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
import multiprocessing
import w3af.core.controllers.output_manager as om
import w3af.core.controllers.threads.threadpool as threadpool
import w3af.core.controllers.threads.pool276 as pool276


def new_debug(msg, *args):
    om_msg = msg % args
    om_msg = '[threadpool] %s' % om_msg
    om.out.debug(om_msg)


def monkey_patch_debug():
    multiprocessing.util.original_debug = multiprocessing.util.debug
    threadpool.original_debug = new_debug
    pool276.original_debug = new_debug

    multiprocessing.util.debug = new_debug
    threadpool.debug = new_debug
    pool276.debug = new_debug


def remove_monkey_patch_debug():
    if not hasattr(multiprocessing.util, 'original_debug'):
        return

    multiprocessing.util.debug = multiprocessing.util.original_debug
    threadpool.debug = threadpool.original_debug
    pool276.debug = pool276.original_debug
