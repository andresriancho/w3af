#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

import sys
sys.path.insert(1, "..")

from SOAPpy import *

# Uncomment to see outgoing HTTP headers and SOAP and incoming 
#Config.debug = 1

Config.BuildWithNoType = 1
Config.BuildWithNoNamespacePrefix = 1



hd = headerType(data = {"mystring": "Hello World"})
server = SOAPProxy("http://localhost:9900/", header=hd) 

print server.echo("Hello world")

server.quit()
