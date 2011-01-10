#!/usr/bin/env python

ident = '$Id: weatherTest.py,v 1.4 2003/05/21 14:52:37 warnes Exp $'

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

SoapEndpointURL	= 'http://services.xmethods.net:80/soap/servlet/rpcrouter'
MethodNamespaceURI = 'urn:xmethods-Temperature'

# Do it inline ala SOAP::LITE, also specify the actually ns

server = SOAPProxy(SoapEndpointURL, http_proxy=proxy)
print "inline", server._ns('ns1', MethodNamespaceURI).getTemp(zipcode='94063')
