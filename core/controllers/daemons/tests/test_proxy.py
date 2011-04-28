import urllib2

from pymock import PyMockTestCase

from ..proxy import proxy, w3afProxyHandler
from core.controllers.misc.levenshtein import relative_distance_ge
from core.data.url.xUrllib import xUrllib


class TestProxy(PyMockTestCase):
    
    IP = '127.0.0.1'
    PORT = 44445
    
    def setUp(self):
        PyMockTestCase.setUp(self)
        
        # Start the proxy server
        self._proxy = proxy(self.IP, self.PORT, xUrllib(), w3afProxyHandler)
        self._proxy.start()
        
        # Build the proxy opener
        self.proxy_opener = urllib2.build_opener(
                    urllib2.ProxyHandler(
                        {"http": "http://%s:%s" % (self.IP, self.PORT)}),
                    urllib2.HTTPHandler)
    
    def test_do_req_through_proxy(self):
        resp_body = self.proxy_opener.open('http://www.google.com').read()
        self.assertTrue(len(resp_body) > 0)
    
    def test_prox_req_ok(self):
        '''Test if the responses either using a proxy or not are the same'''
        # Get response using the proxy
        proxy_resp = self.proxy_opener.open('http://www.google.com').read()
        # Get it the other way
        resp = urllib2.urlopen('http://www.google.com').read()
        # They must be very similar
        self.assertTrue(relative_distance_ge(resp, proxy_resp, 0.9))
    
    def tearDown(self):
        PyMockTestCase.tearDown(self)
        # Shutdown the proxy server
        self._proxy.stop()
    