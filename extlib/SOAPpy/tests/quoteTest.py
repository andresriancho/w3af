#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.
ident = '$Id: quoteTest.py,v 1.5 2003/12/18 06:31:50 warnes Exp $'

import os, re
import sys
sys.path.insert(1, "..")

from SOAPpy import SOAPProxy

# Check for a web proxy definition in environment
try:
   proxy_url=os.environ['http_proxy']
   phost, pport = re.search('http://([^:]+):([0-9]+)', proxy_url).group(1,2)
   proxy = "%s:%s" % (phost, pport)
except:
   proxy = None

# Three ways to do namespaces, force it at the server level

server = SOAPProxy("http://services.xmethods.com:9090/soap",
                        namespace = 'urn:xmethods-delayed-quotes',
                        http_proxy=proxy)

print "IBM>>", server.getQuote(symbol = 'IBM')

# Do it inline ala SOAP::LITE, also specify the actually ns

server = SOAPProxy("http://services.xmethods.com:9090/soap",
                        http_proxy=proxy)
print "IBM>>", server._ns('ns1',
    'urn:xmethods-delayed-quotes').getQuote(symbol = 'IBM')

# Create a namespaced version of your server

dq = server._ns('urn:xmethods-delayed-quotes')
print "IBM>>", dq.getQuote(symbol='IBM')
print "ORCL>>", dq.getQuote(symbol='ORCL')
print "INTC>>", dq.getQuote(symbol='INTC')
