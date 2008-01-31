#!/usr/bin/env python
#
# Copyright (c) 2001 actzero, inc. All rights reserved.

import sys
sys.path.insert(1, "..")

from SOAPpy import *

# Uncomment to see outgoing HTTP headers and SOAP and incoming
Config.dumpSOAPIn = 1
Config.dumpSOAPOut = 1
Config.debug = 1

# specify name of authorization function
Config.authMethod = "_authorize"

# Set this to 0 to test authorization
allowAll = 1

# ask for returned SOAP responses to be converted to basic python types
Config.simplify_objects = 1


# provide a mechanism to stop the server
run = 1
def quit():
    global run
    run=0;


if Config.SSLserver:
    from M2Crypto import SSL
    
def _authorize(*args, **kw):
    global allowAll, Config

    if Config.debug:
        print "Authorize (function) called! (result = %d)" % allowAll
        print "Arguments: %s" % kw
    
    if allowAll:
        return 1
    else:
        return 0

# Simple echo
def echo(s):
    global Config
    
    # Test of context retrieval
    ctx = Server.GetSOAPContext()
    if Config.debug:
        print "SOAP Context: ", ctx
        
    return s + s

# An echo class
class echoBuilder2:
    def echo2(self, val):
        return val * 3

# A class that has an instance variable which is an echo class
class echoBuilder:
    def __init__(self):
        self.prop = echoBuilder2()

    def echo_ino(self, val):
        return val + val
    def _authorize(self, *args, **kw):
        global allowAll, Config

        if Config.debug:
            print "Authorize (method) called with arguments:"
            print "*args=%s" % str(args)
            print "**kw =%s" % str(kw)
            print "Approved -> %d" % allowAll
        
        if allowAll:
            return 1
        else:
            return 0

# Echo with context
def echo_wc(s, _SOAPContext):
    global Config
    
    c = _SOAPContext

    sep = '-' * 72

    # The Context object has extra info about the call
    if Config.debug:
        print "-- XML", sep[7:]
        # The original XML request
        print c.xmldata     

        print "-- Header", sep[10:]
        # The SOAP Header or None if not present
        print c.header      

        if c.header:
            print "-- Header.mystring", sep[19:]
            # An element of the SOAP Header
            print c.header.mystring         

        print "-- Body", sep[8:]
        # The whole Body object
        print c.body        

        print "-- Peer", sep[8:]
        if not GSI:
            # The socket object, useful for
            print c.connection.getpeername()    
        else:
            # The socket object, useful for
            print c.connection.get_remote_address() 
            ctx = c.connection.get_security_context()
            print ctx.inquire()[0].display()

        print "-- SOAPAction", sep[14:]
        # The SOAPaction HTTP header
        print c.soapaction                  

        print "-- HTTP headers", sep[16:]
        # All the HTTP headers
        print c.httpheaders                 

    return s + s

# Echo with keyword arguments
def echo_wkw(**kw):
    return kw['first'] + kw['second'] + kw['third']

# Simple echo
def echo_simple(*arg):
    return arg

def echo_header(s, _SOAPContext):
    global Config
    
    c = _SOAPContext
    return s, c.header


addr = ('localhost', 9900)
GSI = 0
SSL = 0
if len(sys.argv) > 1 and sys.argv[1] == '-s':
    SSL = 1
    if not Config.SSLserver:
        raise RuntimeError, \
            "this Python installation doesn't have OpenSSL and M2Crypto"
    ssl_context = SSL.Context()
    ssl_context.load_cert('validate/server.pem')
    server = SOAPServer(addr, ssl_context = ssl_context)
    prefix = 'https'
elif len(sys.argv) > 1 and sys.argv[1] == '-g':
    GSI = 1
    from SOAPpy.GSIServer import GSISOAPServer
    server = GSISOAPServer(addr)
    prefix = 'httpg'
else:
    server = SOAPServer(addr)
    prefix = 'http'

print "Server listening at: %s://%s:%d/" % (prefix, addr[0], addr[1])

# register the method
server.registerFunction(echo)
server.registerFunction(echo, path = "/pathtest")
server.registerFunction(_authorize)
server.registerFunction(_authorize, path = "/pathtest")

# Register a whole object
o = echoBuilder()
server.registerObject(o, path = "/pathtest")
server.registerObject(o)

# Register a function which gets called with the Context object
server.registerFunction(MethodSig(echo_wc, keywords = 0, context = 1),
                        path = "/pathtest")
server.registerFunction(MethodSig(echo_wc, keywords = 0, context = 1))

# Register a function that takes keywords
server.registerKWFunction(echo_wkw, path = "/pathtest")
server.registerKWFunction(echo_wkw)

server.registerFunction(echo_simple)
server.registerFunction(MethodSig(echo_header, keywords=0, context=1))
server.registerFunction(quit)

# Start the server
try:
    while run:
        server.handle_request()
except KeyboardInterrupt:
    pass
