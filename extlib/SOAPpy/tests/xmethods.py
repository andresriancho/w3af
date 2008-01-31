#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.
ident = '$Id: xmethods.py,v 1.4 2003/12/18 06:31:50 warnes Exp $'

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

 
print "##########################################"
print " SOAP services registered at xmethods.net"
print "##########################################"

server = SOAPProxy("http://www.xmethods.net/interfaces/query",
                        namespace = 'urn:xmethods-delayed-quotes',
                        http_proxy=proxy)

names = server.getAllServiceNames()

for item in names:
    print 'name:',  item['name']
    print 'id  :',  item['id']
    print 
