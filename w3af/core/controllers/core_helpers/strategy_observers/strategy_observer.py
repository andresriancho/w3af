"""
strategy_observer.py

Copyright 2015 Andres Riancho

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


class StrategyObserver(object):
    """
    When you want to listen to the activity inside the CoreStrategy simply
    inherit from this class and call CoreStrategy.add_observer(). When the scan
    runs the methods in this class are called.
    """
    def crawl(self, craw_consumer, fuzzable_request):
        pass

    def audit(self, audit_consumer, fuzzable_request):
        pass

    def bruteforce(self, bruteforce_consumer, fuzzable_request):
        pass

    def grep(self, grep_consumer, request, response):
        pass

    def end(self):
        """
        Called when the strategy is about to end, useful for clearing
        memory, removing temp files, stopping threads, etc.

        :return: None
        """
        pass
