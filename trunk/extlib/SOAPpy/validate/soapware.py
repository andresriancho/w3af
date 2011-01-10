#!/usr/bin/env python

# This server validates as of 4/23/01 when run with UserLand's SOAP validator
# (http://validator.soapware.org/).

import getopt
import sys

sys.path.insert (1, '..')

from SOAPpy import SOAP

ident = '$Id: soapware.py,v 1.2 2003/03/08 05:10:01 warnes Exp $'

def whichToolkit ():
    return SOAP.SOAPUserAgent ()

def countTheEntities (s):
    counts = {'ctLeftAngleBrackets': 0, 'ctRightAngleBrackets': 0,
        'ctAmpersands': 0, 'ctApostrophes': 0, 'ctQuotes': 0}

    for i in s:
        if i == '<':
            counts['ctLeftAngleBrackets'] += 1
        elif i == '>':
            counts['ctRightAngleBrackets'] += 1
        elif i == '&':
            counts['ctAmpersands'] += 1
        elif i == "'":
            counts['ctApostrophes'] += 1
        elif i == '"':
            counts['ctQuotes'] += 1

    return counts

def easyStructTest (stooges):
    return stooges['larry'] + stooges['moe'] + stooges['curly']

def echoStructTest (myStruct):
    return myStruct

def manyTypesTest (num, bool, state, doub, dat, bin):
    return [num, SOAP.booleanType (bool), state, doub,
        SOAP.dateTimeType (dat), bin]

def moderateSizeArrayCheck (myArray):
    return myArray[0] + myArray[-1]

def nestedStructTest (myStruct):
    return easyStructTest (myStruct.year2000.month04.day01)

def simpleStructReturnTest (myNumber):
    return {'times10': myNumber * 10, 'times100': myNumber * 100,
        'times1000': myNumber * 1000}

namespace = 'http://www.soapware.org/'

DEFAULT_HOST    = 'localhost'
DEFAULT_PORT    = 8080

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
""" % (sys.argv[0], DEFAULT_HOST, DEFAULT_PORT),

    sys.exit (0)

def main ():
    host = DEFAULT_HOST
    port = DEFAULT_PORT

    try:
        opts, args = getopt.getopt (sys.argv[1:], '?h:p:',
            ['help', 'host', 'port'])

        for opt, arg in opts:
            if opt in ('-?', '--help'):
                usage ()
            elif opt in ('-h', '--host'):
                host = arg
            elif opt in ('-p', '--port'):
                port = int (arg)
            else:
                raise AttributeError, \
                     "Recognized but unimplemented option `%s'" % opt
    except SystemExit:
        raise
    except:
        usage (sys.exc_info ()[1])

    server = SOAP.SOAPServer ((host, port))

    server.registerFunction (whichToolkit, namespace)
    server.registerFunction (countTheEntities)
    server.registerFunction (easyStructTest)
    server.registerFunction (echoStructTest)
    server.registerFunction (manyTypesTest)
    server.registerFunction (moderateSizeArrayCheck)
    server.registerFunction (nestedStructTest)
    server.registerFunction (simpleStructReturnTest)

    server.serve_forever()

if __name__ == '__main__':
    try:
        sys.exit (main ())
    except KeyboardInterrupt:
        sys.exit (0)
