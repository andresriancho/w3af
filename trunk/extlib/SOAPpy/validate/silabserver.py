#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

# This is a server for the XMethods matrix
# (http://jake.soapware.org/currentXmethodsResults).

import getopt
import sys

sys.path.insert (1, '..')

from SOAPpy import SOAP

if SOAP.Config.SSLserver:
    from M2Crypto import SSL

ident = '$Id: silabserver.py,v 1.2 2003/03/08 05:10:01 warnes Exp $'

def echoFloat (inputFloat):
    return inputFloat

def echoFloatArray (inputFloatArray):
    return inputFloatArray

def echoInteger (inputInteger):
    return inputInteger

def echoIntegerArray (inputIntegerArray):
    return inputIntegerArray

def echoString (inputString):
    return inputString

def echoStringArray (inputStringArray):
    return inputStringArray

def echoStruct (inputStruct):
    return inputStruct

def echoStructArray (inputStructArray):
    return inputStructArray

def echoVoid ():
    return SOAP.voidType()

def echoDate (inputDate):
    return SOAP.dateTimeType (inputDate)

def echoBase64 (inputBase64):
    return SOAP.binaryType (inputBase64)

namespace = 'http://soapinterop.org/'

DEFAULT_HOST            = 'localhost'
DEFAULT_HTTP_PORT       = 8080
DEFAULT_HTTPS_PORT      = 8443

def usage (error = None):
    sys.stdout = sys.stderr

    if error != None:
        print error

    print """usage: %s [options]
  If a long option shows an argument is mandatory, it's mandatory for the
  equivalent short option also. The default (if any) is shown in brackets.

  -?, --help            display this usage
  -h, --host=HOST       use HOST in the address to listen on [%s]
  -p, --port=PORT       listen on PORT [%d]
""" % (sys.argv[0], DEFAULT_HOST, DEFAULT_HTTP_PORT),

    if SOAP.Config.SSLserver:
        print "  -s, --ssl             serve using SSL"

    sys.exit (0)

def main ():
    host = DEFAULT_HOST
    port = None
    ssl = 0

    try:
        opts = '?h:p:'
        args = ['help', 'host', 'port']

        if SOAP.Config.SSLserver:
            opts += 's'
            args += ['ssl']

        opts, args = getopt.getopt (sys.argv[1:], opts, args)

        for opt, arg in opts:
            if opt in ('-?', '--help'):
                usage ()
            elif opt in ('-h', '--host'):
                host = arg
            elif opt in ('-p', '--port'):
                port = int (arg)
            elif opt in ('-s', '--ssl'):
                ssl = 1
            else:
                raise AttributeError, \
                     "Recognized but unimplemented option `%s'" % opt
    except SystemExit:
        raise
    except:
        usage (sys.exc_info ()[1])

    if port == None:
        port = [DEFAULT_HTTP_PORT, DEFAULT_HTTPS_PORT][ssl]

    if ssl:
        ssl_context = SSL.Context()
        ssl_context.load_cert('server.pem')
    else:
        ssl_context = None

    server = SOAP.SOAPServer ((host, port), namespace = namespace,
        ssl_context = ssl_context)

    server.registerFunction (echoFloat)
    server.registerFunction (echoFloatArray)
    server.registerFunction (echoInteger)
    server.registerFunction (echoIntegerArray)
    server.registerFunction (echoString)
    server.registerFunction (echoStringArray)
    server.registerFunction (echoStruct)
    server.registerFunction (echoStructArray)
    server.registerFunction (echoVoid)
    server.registerFunction (echoDate)
    server.registerFunction (echoBase64)

    server.serve_forever()

if __name__ == '__main__':
    try:
        sys.exit (main ())
    except KeyboardInterrupt:
        sys.exit (0)
