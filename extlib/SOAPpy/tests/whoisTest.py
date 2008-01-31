#!/usr/bin/env python

ident = '$Id: whoisTest.py,v 1.4 2003/05/21 14:52:37 warnes Exp $'

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

server = SOAPProxy("http://www.SoapClient.com/xml/SQLDataSoap.WSDL",
                   http_proxy=proxy)

print "whois>>", server.ProcessSRL(SRLFile="WHOIS.SRI",
                                   RequestName="whois",
                                   key = "microsoft.com")

