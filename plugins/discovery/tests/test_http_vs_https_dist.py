'''
test_http_vs_https_dist.py

Copyright 2011 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

import __builtin__
import copy

from pymock import PyMockTestCase, method, override, set_count, \
    override_prop, dontcare, expr

import plugins.discovery.http_vs_https_dist as hvshsdist

# Translation hack
__builtin__.__dict__['_'] = lambda x: x

class test_http_vs_https_dist(PyMockTestCase):
    '''
    @author: Javier Andalia <jandalia =at= gmail.com>
    '''
    
    test_url = 'http://host.tld'
    tracedict = {'localhost': {1: ('192.168.1.1', False),
                               3: ('200.115.195.33', False),
                               5: ('207.46.47.14', True)}}
    
    def setUp(self):
        # Setup objects
        PyMockTestCase.setUp(self)
        self.plugininst = hvshsdist.http_vs_https_dist()
        self.fuzz_req = self.mock()
    
    def test_discover_override_port(self):
        plugininst = self.plugininst
        override(plugininst, '_has_permission').expects().returns(True)
        method(self.fuzz_req, 'getURL').expects().returns('https://host.tld:4444')
        # HTTPS try
        self._call_traceroute('host.tld', 4444, self.tracedict)
        # HTTP try
        tracedict = copy.deepcopy(self.tracedict)
        tracedict['localhost'][3] = ('200.200.0.0', False) # Set diff hop
        self._call_traceroute('host.tld', 80, tracedict)
        # Mock output manager. Ensure that is called with the proper desc.
        override(hvshsdist.om.out, 'information').expects(expr(lambda x: x.find('host.tld:4444') != -1))
        set_count(exactly=1)

        ## Stop Recording.Time to Play! ##
        self.replay()
        res = plugininst.discover(self.fuzz_req)
        self.assertEquals(res, [])

        ## Verify ##
        self.verify()
    
    def test_discover_eq_routes(self):
        # Start recording
        plugininst = self.plugininst
        override(plugininst, '_has_permission').expects().returns(True)
        method(self.fuzz_req, 'getURL').expects().returns(self.test_url)
        # HTTPS try
        self._call_traceroute('host.tld', 443, self.tracedict)
        # HTTP try
        self._call_traceroute('host.tld', 80, self.tracedict)
        # Output Manager. It must not be called!
        ommock = self.mock(hvshsdist.om)
        ommock.out
        set_count(exactly=0)
        
        ## Stop Recording.Time to Play! ##
        self.replay()
        res = plugininst.discover(self.fuzz_req)
        self.assertEquals(res, [])

        ## Verify ##
        self.verify()
        
    def test_discover_diff_routes(self):
        # Start recording
        plugininst = self.plugininst
        override(plugininst, '_has_permission').expects().returns(True)
        method(self.fuzz_req, 'getURL').expects().returns(self.test_url)
        # HTTPS try
        self._call_traceroute('host.tld', 443, self.tracedict)
        # HTTP try
        tracedict = copy.deepcopy(self.tracedict)
        tracedict['localhost'][3] = ('200.200.0.0', False) # Set diff hop
        self._call_traceroute('host.tld', 80, tracedict)
        # Mock output manager. Ensure that is called with the proper desc.
        override(hvshsdist.om.out, 'information').expects(expr(lambda x: x.find('are different') != -1))
        set_count(exactly=1)
        
        ## Stop Recording. Time to Play! ##
        self.replay()
        res = plugininst.discover(self.fuzz_req)
        self.assertEquals(res, [])

        ## Verify ##
        self.verify()
    
    def test_discover_runonce(self):
        # Discovery routine must be executed only once. Upcoming calls should
        # fail
        from core.controllers.w3afException import w3afRunOnce
        plugininst = self.plugininst
        count = 0
        for i in xrange(10):
            try:
                plugininst.discover(self.fuzz_req)
            except Exception, exc:
                if isinstance(exc, w3afRunOnce):
                    count += 1
        self.assertEquals(count, 9)
    
    def test_not_root_user(self):
        from core.controllers.w3afException import w3afException
        override(self.plugininst, '_has_permission').expects().returns(False)
        self.assertRaises(w3afException, self.plugininst.discover, self.fuzz_req)
        
    ## Helper methods ##
    
    def _call_traceroute(self, dest, dport, trace_resp):
        # Mocks scapy 'traceroute' function
        https_tracerout_obj = self.mock()
        method(https_tracerout_obj, 'get_trace').expects().returns(trace_resp)
        resp_tuple = (https_tracerout_obj, None)
        override(hvshsdist, 'traceroute').expects(dest, dport=dport).returns(resp_tuple)
