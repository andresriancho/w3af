#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

import sys
sys.path.insert(1, "..")

from SOAPpy import *
from SOAPpy import Parser

# Uncomment to see outgoing HTTP headers and SOAP and incoming 
#Config.debug = 1

if len(sys.argv) > 1 and sys.argv[1] == '-s':
    server = SOAPProxy("https://localhost:9900")
else:
    server = SOAPProxy("http://localhost:9900")


# BIG data:

big = repr('.' * (1<<18) )

# ...in an object
print "server.echo_ino(big):..",
tmp = server.echo_ino(big)
print "done"

# ...in an object in an object
print "server.prop.echo2(big)..",
tmp = server.prop.echo2(big)
print "done"

# ...with keyword arguments 
print 'server.echo_wkw(third = big, first = "one", second = "two")..',
tmp = server.echo_wkw(third = big, first = "one", second = "two")
print "done"

# ...with a context object
print "server.echo_wc(big)..",
tmp =  server.echo_wc(big)
print "done"

# ...with a header
hd = headerType(data = {"mystring": "Hello World"})
print "server._hd(hd).echo_wc(big)..",
tmp = server._hd(hd).echo_wc(big)
print "done"

server.quit()
