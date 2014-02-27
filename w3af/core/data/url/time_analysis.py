"""
time_analysis.py

Copyright 2006 Andres Riancho

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
import w3af.core.controllers.output_manager as om

# Define two internal variables
# AVERAGE_CALCULATION is used to define how many request/response values
# are used to calculate the average time it takes to get a response.
AVERAGE_CALCULATION = 3

# TIME_DEVIATION_MULTIPLIER , big name for a simple thing :)
# If average time is 1 second, TIME_DEVIATION_MULTIPLIER is 3 and the time of
# the current request being analized is 4, then we report a vulnerability
# ( current > TIME_DEVIATION_MULTIPLIER * avg )
TIME_DEVIATION_MULTIPLIER = 25


class time_analysis:
    """
    This class analyzes the response time of a GET/POST .
    It is usefull for finding possible DoS's to Web Apps, buffer overflows, etc.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        self._numberOfRequests = 0
        self._outgoingRequests = {}
        self._incomingResponses = {}
        self._average = 0

    def pre_request(self, uri, method, dc={}):
        """
        It is called before the actual request is done. This method registers all
        outgoing requests with their corresponding time.

        :param uri: This is the url to register.
        :param method: GET/POST
        :param dc: This is the data container that ExtendedUrllib is going to send.
        :return: No value is returned.
        """
        if self._numberOfRequests < AVERAGE_CALCULATION:
            # The first 3 requests are used to calculate the average time that the
            # response takes to return to w3af
            self._calculateAvg(uri, method, dc)
        else:
            self._registerRequest(uri, method, dc)

    def post_request(self, uri, method, dc={}):
        """
        It is called before the actual request is done. This method registers all
        outgoing requests with their corresponding time.

        :param uri: This is the url to register.
        :param method: GET/POST
        :param dc: This is the data container that ExtendedUrllib is going to send.
        :return: No value is returned.
        """
        if self._numberOfRequests < AVERAGE_CALCULATION:
            # The first 3 requests are used to calculate the average time that the
            # response takes to return to w3af
            self._calculateAvg(uri, method, dc)
        else:
            # I'll compare the average with the current value
            receiveTime = time.time()
            sentTime = self._getRequestTime(uri, method, dc)
            self._removeRequest(uri, method, dc)

            if (receiveTime - sentTime) > (self._average * TIME_DEVIATION_MULTIPLIER):
                # The time deviation was to big, report it.
                ### TODO: Check WHY this AINT working and enable output again
                #om.out.vulnerability('time_analysis detected a big time deviation when ' +
                #'requesting the URI: ' + uri + ' with method: ' + method +
                #' and the following data: ' + str(dc) + ' . The average time for a response is: ' +
                #str(self._average) + ' , this response took: ' + str(receiveTime - sentTime))
                pass

    def _calculateAvg(self, uri, method, dc):
        """
        This method calculates the AVG time.

        :param uri: This is the url to register.
        :param method: GET/POST
        :param dc: This is the data container that ExtendedUrllib is going to send.
        :return: No value is returned.
        """
        if (uri, method, str(dc)) not in self._outgoingRequests.keys():
            # This tuple hasnt been registered as an outgoing request.
            # It should be registered now.
            self._registerRequest(uri, method, dc)
        elif (uri, method, str(dc)) not in self._incomingResponses.keys():
            # This tuple has been registered before and now it has arrived for analysis
            self._numberOfRequests += 1
            self._registerResponse(uri, method, dc)
        else:
            # Something went really wrong, the tuple aint registered anywhere
            om.out.error('time_analysis plugin detected an internal error.')

        if self._numberOfRequests == AVERAGE_CALCULATION:
            # Now we are going to calculate the average time
            reqTime = 0
            resTime = 0
            for req in self._outgoingRequests.keys():
                reqTime += self._outgoingRequests[req]
                del self._outgoingRequests[req]

            for res in self._incomingResponses.keys():
                resTime += self._incomingResponses[res]
                del self._incomingResponses[res]

            self._average = (resTime - reqTime) / AVERAGE_CALCULATION

    def _registerRequest(self, uri, method, dc):
        sentTime = time.time()  # Return the current clock
        self._outgoingRequests[(uri, method, str(dc))] = sentTime

    def _registerResponse(self, uri, method, dc):
        receiveTime = time.time()
        self._incomingResponses[(uri, method, str(dc))] = receiveTime

    def _getRequestTime(self, uri, method, dc):
        return self._outgoingRequests[(uri, method, str(dc))]

    def _removeRequest(self, uri, method, dc):
        del self._outgoingRequests[(uri, method, str(dc))]
