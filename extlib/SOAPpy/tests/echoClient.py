#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

import sys
sys.path.insert(1, "..")

from SOAPpy import *

# Uncomment to see outgoing HTTP headers and SOAP and incoming 
#Config.debug = 1
#Config.dumpHeadersIn = 1
#Config.dumpSOAPIn = 1
#Config.dumpSOAPOut = 1

# ask for returned SOAP responses to be converted to basic python types
Config.simplify_objects = 1

#Config.BuildWithNoType = 1
#Config.BuildWithNoNamespacePrefix = 1

if len(sys.argv) > 1 and sys.argv[1] == '-s':
    # Use secure http
    pathserver = SOAPProxy("https://localhost:9900/pathtest")
    server = SOAPProxy("https://localhost:9900")
    
elif len(sys.argv) > 1 and sys.argv[1] == '-g':
    # use Globus for communication
    import pyGlobus 
    pathserver = SOAPProxy("httpg://localhost:9900/pathtest")
    server = SOAPProxy("httpg://localhost:9900")
    
else: 
    # Default: use standard http
    pathserver = SOAPProxy("http://localhost:9900/pathtest")
    server = SOAPProxy("http://localhost:9900")

# Echo...

try:
    print server.echo("MOO")
except Exception, e:
    print "Caught exception: ", e
try:
    print pathserver.echo("MOO")
except Exception, e:
    print "Caught exception: ", e
    
# ...in an object
try:
    print server.echo_ino("moo")
except Exception, e:
    print "Caught exception: ", e
try:
    print pathserver.echo_ino("cow")
except Exception, e:
    print "Caught exception: ", e

# ...in an object in an object
try:
    print server.prop.echo2("moo")
except Exception, e:
    print "Caught exception: ", e

try:
    print pathserver.prop.echo2("cow")
except Exception, e:
    print "Caught exception: ", e

# ...with keyword arguments 
try:
    print server.echo_wkw(third = "three", first = "one", second = "two")
except Exception, e:
    print "Caught exception: ", e
try:
    print pathserver.echo_wkw(third = "three", first = "one", second = "two")
except Exception, e:
    print "Caught exception: ", e

# ...with a context object
try:
    print server.echo_wc("moo")
except Exception, e:
    print "Caught exception: ", e
try:
    print pathserver.echo_wc("cow")
except Exception, e:
    print "Caught exception: ", e

# ...with a header
hd = headerType(data = {"mystring": "Hello World"})
try:
    print server._hd(hd).echo_wc("moo")
except Exception, e:
    print "Caught exception: ", e
try:
    print pathserver._hd(hd).echo_wc("cow")
except Exception, e:
    print "Caught exception: ", e

# close down server
server.quit()
