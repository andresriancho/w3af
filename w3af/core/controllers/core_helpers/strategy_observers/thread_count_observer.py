"""
thread_count_observer.py

Copyright 2018 Andres Riancho

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
import threading

import w3af.core.controllers.output_manager as om

from .strategy_observer import StrategyObserver


class ThreadCountObserver(StrategyObserver):
    """
    Monitor number of active threads in the framework.

    The goal is to prevent issues such as "Can't start new thread" which are
    common in applications which use a lot of threads (like w3af).
    """
    ANALYZE_EVERY = 30

    def __init__(self):
        super(ThreadCountObserver, self).__init__()
        self.last_call = 0

    def log_thread_count(self, *args):
        # Don't measure threads each time we get called
        current_time = time.time()
        if (current_time - self.last_call) < self.ANALYZE_EVERY:
            return

        self.last_call = current_time

        active_threads = threading.active_count()
        om.out.debug('The framework has %s active threads.' % active_threads)

    crawl = audit = bruteforce = grep = log_thread_count
