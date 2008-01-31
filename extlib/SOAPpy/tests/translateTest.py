#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.
ident = '$Id: translateTest.py,v 1.5 2003/05/21 14:52:37 warnes Exp $'

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

server = SOAPProxy("http://services.xmethods.com:80/perl/soaplite.cgi",
                   http_proxy=proxy)
babel = server._ns('urn:xmethodsBabelFish#BabelFish')

print babel.BabelFish(translationmode = "en_fr",
    sourcedata = "The quick brown fox did something or other")
