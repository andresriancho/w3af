"""
seed.py

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
import traceback

from multiprocessing.dummy import Queue, Process

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af.core.controllers.exceptions import (ScanMustStopException,
                                         ScanMustStopOnUrlError)
from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.request.factory import create_fuzzable_requests


class seed(Process):
    """
    Consumer thread that takes fuzzable requests from a Queue that's populated
    by the crawl plugins and identified vulnerabilities by performing various
    requests.
    """

    def __init__(self, w3af_core):
        """
        :param w3af_core: The w3af core that we'll use for status reporting
        """
        super(seed, self).__init__(name='SeedController')
        self.name = 'Seed'

        self._w3af_core = w3af_core

        # See documentation in the property below
        self._out_queue = Queue()

    def get_result(self, timeout=0.5):
        return self._out_queue.get_nowait()

    def has_pending_work(self):
        return self._out_queue.qsize() != 0

    def join(self):
        return

    def terminate(self):
        return

    def seed_output_queue(self, target_urls):
        """
        Create the first fuzzable request objects based on the targets and put
        them in the output Queue.

        This will start the whole discovery process, since plugins are going
        to consume from that Queue and then put their results in it again in
        order to continue discovering.
        """
        # We only want to scan pages that are in current scope
        in_scope = lambda fr: fr.get_url().get_domain() == url.get_domain()

        for url in target_urls:
            try:
                #
                #    GET the initial target URLs in order to save them
                #    in a list and use them as our bootstrap URLs
                #
                response = self._w3af_core.uri_opener.GET(url, cache=True)
            except (ScanMustStopOnUrlError, BaseFrameworkException, ScanMustStopException), w3:
                om.out.error('The target URL: %s is unreachable.' % url)
                om.out.error('Error description: %s' % w3)
            except Exception, e:
                om.out.error('The target URL: %s is unreachable '
                             'because of an unhandled exception.' % url)
                om.out.error('Error description: "%s". See debug '
                             'output for more information.' % e)
                om.out.error('Traceback for this error: %s' %
                             traceback.format_exc())
            else:
                all_fuzzable_requests = create_fuzzable_requests(response)
                filtered_seeds = filter(in_scope, all_fuzzable_requests)

                for seed in filtered_seeds:
                    self._out_queue.put((None, None, seed))

                    # Update the set that lives in the KB
                    kb.kb.add_fuzzable_request(seed)

        self._out_queue.put(POISON_PILL)
