#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

# This set of clients validates when run against the servers in
# silab.servers.

import copy
import fileinput
import getopt
import re
import string
import sys
import time
import traceback

sys.path.insert (1, '..')

from SOAPpy import SOAP

SOAP.Config.typesNamespace = SOAP.NS.XSD3
SOAP.Config.typesNamespace = SOAP.NS.XSD3

ident = '$Id: silabclient.py,v 1.2 2003/03/08 05:10:01 warnes Exp $'

DEFAULT_SERVERS_FILE        = 'silab.servers'

DEFAULT_METHODS = \
    (
        'actorShouldPass', 'actorShouldFail',
        'echoDate', 'echoBase64',
        'echoFloat', 'echoFloatArray',
        'echoFloatINF', 'echoFloatNaN',
        'echoFloatNegINF', 'echoFloatNegZero',
        'echoInteger', 'echoIntegerArray',
        'echoString', 'echoStringArray',
        'echoStruct', 'echoStructArray',
        'echoVeryLargeFloat', 'echoVerySmallFloat',
        'echoVoid',
        'mustUnderstandEqualsOne', 'mustUnderstandEqualsZero',
    )


def usage (error = None):
    sys.stdout = sys.stderr

    if error != None:
        print error

    print """usage: %s [options] [server ...]
  If a long option shows an argument is mandatory, it's mandatory for the
  equivalent short option also.

  -?, --help            display this usage
  -d, --debug           turn on debugging in the SOAP library
  -e, --exit-on-failure exit on the first (unexpected) failure
  -h, --harsh           turn on harsh testing:
                        - look for the documented error code from
                          mustUnderstand failures
                        - use non-ASCII strings in the string tests
  -i, --invert          test servers *not* in the list of servers given
  -m, --method=METHOD#[,METHOD#...]
                        call only the given methods, specify a METHOD# of ?
                        for the list of method numbers
  -n, --no-stats, --no-statistics
                        don't display success and failure statistics
  -N, --no-boring-stats, --no-boring-statistics
                        only display unexpected failures and unimplemented
                        tests, and only if non-zero
  -o, --output=TYPE     turn on output, TYPE is one or more of s(uccess),
                        f(ailure), n(ot implemented), F(ailed (as expected)),
                        a(ll)
                        [f]
  -s, --servers=FILE    use FILE as list of servers to test [%s]
  -t, --stacktrace      print a stack trace on each unexpected failure
  -T, --always-stacktrace
                        print a stack trace on any failure
""" % (sys.argv[0], DEFAULT_SERVERS_FILE),

    sys.exit (0)


def methodUsage ():
    sys.stdout = sys.stderr

    print "Methods are specified by number. Multiple methods can be " \
        "specified using a\ncomma-separated list of numbers or ranges. " \
        "For example 1,4-6,8 specifies\nmethods 1, 4, 5, 6, and 8.\n"

    print "The available methods are:\n"

    half = (len (DEFAULT_METHODS) + 1) / 2

    for i in range (half):
        print "%4d. %-25s" % (i + 1, DEFAULT_METHODS[i]),
        if i + half < len (DEFAULT_METHODS):
            print "%4d. %-25s" % (i + 1 + half, DEFAULT_METHODS[i + half]),
        print

    sys.exit (0)


# as borrowed from jake.soapware.org for float compares.
def nearlyeq (a, b, prec = 1e-7):
    return abs (a - b) <= abs (a) * prec

def readServers (file):
    servers = []
    names = {}
    cur = None

    f = fileinput.input(file)

    for line in f:
        if line[0] == '#':
            continue

        if line == '' or line[0] == '\n':
            cur = None
            continue

        if cur == None:
            cur = {'nonfunctional': {}, '_line': f.filelineno(),
                '_file': f.filename()}
            tag = None
            servers.append (cur)

        if line[0] in string.whitespace:
            if tag == 'nonfunctional':
                value = method + ' ' + cur[tag][method]
            else:
                value = cur[tag]
            value += ' ' + line.strip ()
        elif line[0] == '_':
            raise ValueError, \
                "%s, line %d: can't have a tag starting with `_'" % \
                (f.filename(), f.filelineno())
        else:
            tag, value = line.split (':', 1)

            tag = tag.strip ().lower ()
            value = value.strip ()

            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1]

        if tag == 'typed':
            if value.lower() in ('0', 'no', 'false'):
                value = 0
            elif value.lower() in ('1', 'yes', 'false'):
                value = 1
            else:
                raise ValueError, \
                    "%s, line %d: unknown typed value `%s'" % \
                    (f.filename(), f.filelineno(), value)
        elif tag == 'name':
            if names.has_key(value):
                old = names[value]

                raise ValueError, \
                    "%s, line %d: already saw a server named `%s' " \
                    "(on line %d of %s)" % \
                    (f.filename(), f.filelineno(), value,
                        old['_line'], old['_file'])
            names[value] = cur

        if tag == 'nonfunctional':
            value = value.split (' ', 1) + ['']

            method = value[0]
            cur[tag][method] = value[1]
        elif tag == 'functional':
            try:
                del cur['nonfunctional'][value]
            except:
                raise ValueError, \
                    "%s, line %d: `%s' not marked nonfunctional" % \
                    (f.filename(), f.filelineno(), value)
        elif tag == 'like':
            try:
                new = copy.deepcopy(names[value])
            except:
                raise ValueError, \
                    "%s, line %d: don't know about a server named `%s'" % \
                    (f.filename(), f.filelineno(), value)

            # This is so we don't lose the nonfunctional methods in new or
            # in cur

            new['nonfunctional'].update(cur['nonfunctional'])
            del cur['nonfunctional']

            new.update(cur)

            # This is because servers and possibly names has a reference to
            # cur, so we have to keep working with cur so changes are
            # reflected in servers and names.

            cur.update(new)
        else:
            cur[tag] = value

    return servers

def str2list (s):
    l = {}

    for i in s.split (','):
        if i.find ('-') != -1:
            i = i.split ('-')
            for i in range (int (i[0]),int (i[1]) + 1):
                l[i] = 1
        else:
            l[int (i)] = 1

    l = l.keys ()
    l.sort ()

    return l

def testActorShouldPass (server, action, harsh):
    test = 42
    server = server._sa (action % {'methodname': 'echoInteger'})
    hd = SOAP.headerType ()
    hd.InteropTestHeader = SOAP.stringType ("This shouldn't fault because "
        "the mustUnderstand attribute is 0")
    hd.InteropTestHeader._setMustUnderstand (0)
    hd.InteropTestHeader._setActor (
        'http://schemas.xmlsoap.org/soap/actor/next')
    server = server._hd (hd)

    result = server.echoInteger (inputInteger = test)

    if not SOAP.Config.typed:
        result = int (result)

    if result != test:
        raise Exception, "expected %s, got %s" % (test, result)

def testActorShouldFail (server, action, harsh):
    test = 42
    server = server._sa (action % {'methodname': 'echoInteger'})
    hd = SOAP.headerType ()
    hd.InteropTestHeader = SOAP.stringType ("This should fault because "
        "the mustUnderstand attribute is 1")
    hd.InteropTestHeader._setMustUnderstand (1)
    hd.InteropTestHeader._setActor (
        'http://schemas.xmlsoap.org/soap/actor/next')
    server = server._hd (hd)

    try:
        result = server.echoInteger (inputInteger = test)
    except SOAP.faultType, e:
        if harsh and e.faultcode != 'SOAP-ENV:MustUnderstand':
            raise AttributeError, "unexpected faultcode %s" % e.faultcode
        return

    raise Exception, "should fail, succeeded with %s" % result

def testEchoFloat (server, action, harsh):
    server = server._sa (action % {'methodname': 'echoFloat'})

    for test in (0.0, 1.0, -1.0, 3853.33333333):
        result = server.echoFloat (inputFloat = test)

        if not SOAP.Config.typed:
            result = float (result)

        if not nearlyeq (result, test):
            raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoFloatArray (server, action, harsh):
    test = [0.0, 1.0, -1.0, 3853.33333333]
    server = server._sa (action % {'methodname': 'echoFloatArray'})
    result = server.echoFloatArray (inputFloatArray = test)

    for i in range (len (test)):
        if not SOAP.Config.typed:
            result[i] = float (result[i])

        if not nearlyeq (result[i], test[i]):
            raise Exception, "@ %d expected %s, got %s" % \
                  (i, repr (test), repr (result))

def testEchoFloatINF (server, action, harsh):
    try:
        test = float ('INF')
    except:
        test = float (1e300**2)
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if result != test:
        raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoFloatNaN (server, action, harsh):
    try:
        test = float ('NaN')
    except:
        test = float (0.0)
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if result != test:
        raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoFloatNegINF (server, action, harsh):
    try:
        test = float ('-INF')
    except:
        test = float (-1e300**2)
                     
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if result != test:
        raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoFloatNegZero (server, action, harsh):
    test = float ('-0.0')
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if result != test:
        raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoInteger (server, action, harsh):
    server = server._sa (action % {'methodname': 'echoInteger'})

    for test in (0, 1, -1, 3853):
        result = server.echoInteger (inputInteger = test)

        if not SOAP.Config.typed:
            result = int (result)

        if result != test:
            raise Exception, "expected %.8f, got %.8f" % (test, result)

def testEchoIntegerArray (server, action, harsh):
    test = [0, 1, -1, 3853]
    server = server._sa (action % {'methodname': 'echoIntegerArray'})
    result = server.echoIntegerArray (inputIntegerArray = test)

    for i in range (len (test)):
        if not SOAP.Config.typed:
            result[i] = int (result[i])

        if result[i] != test[i]:
            raise Exception, "@ %d expected %s, got %s" % \
                (i, repr (test), repr (result))

relaxedStringTests = ['', 'Hello', '\'<&>"',]
relaxedStringTests = ['Hello', '\'<&>"',]
harshStringTests = ['', 'Hello', '\'<&>"',
    u'\u0041', u'\u00a2', u'\u0141', u'\u2342',
    u'\'<\u0041&>"', u'\'<\u00a2&>"', u'\'<\u0141&>"', u'\'<\u2342&>"',]

def testEchoString (server, action, harsh):
    if harsh:
        test = harshStringTests
    else:
        test = relaxedStringTests
    server = server._sa (action % {'methodname': 'echoString'})

    for test in test:
        result = server.echoString (inputString = test)

        if result != test:
            raise Exception, "expected %s, got %s" % \
                (repr (test), repr (result))

def testEchoStringArray (server, action, harsh):
    if harsh:
        test = harshStringTests
    else:
        test = relaxedStringTests
    server = server._sa (action % {'methodname': 'echoStringArray'})
    result = server.echoStringArray (inputStringArray = test)

    if result != test:
        raise Exception, "expected %s, got %s" % (repr (test), repr (result))

def testEchoStruct (server, action, harsh):
    test = {'varFloat': 2.256, 'varInt': 474, 'varString': 'Utah'}
    server = server._sa (action % {'methodname': 'echoStruct'})
    result = server.echoStruct (inputStruct = test)

    if not SOAP.Config.typed:
        result.varFloat = float (result.varFloat)
        result.varInt = int (result.varInt)

    if not nearlyeq (test['varFloat'], result.varFloat):
        raise Exception, ".varFloat expected %s, got %s" % \
            (i, repr (test['varFloat']), repr (result.varFloat))

    for i in test.keys ():
        if i == 'varFloat':
            continue

        if test[i] != getattr (result, i):
            raise Exception, ".%s expected %s, got %s" % \
                (i, repr (test[i]), repr (getattr (result, i)))


def testEchoStructArray (server, action, harsh):
    test = [{'varFloat': -5.398, 'varInt': -546, 'varString': 'West Virginia'},
        {'varFloat': -9.351, 'varInt': -641, 'varString': 'New Mexico'},
        {'varFloat': 1.495, 'varInt': -819, 'varString': 'Missouri'}]
    server = server._sa (action % {'methodname': 'echoStructArray'})
    result = server.echoStructArray (inputStructArray = test)

    for s in range (len (test)):
        if not SOAP.Config.typed:
            result[s].varFloat = float (result[s].varFloat)
            result[s].varInt = int (result[s].varInt)

        if not nearlyeq (test[s]['varFloat'], result[s].varFloat):
            raise Exception, \
                "@ %d.varFloat expected %s, got %s" % \
                (s, repr (test[s]['varFloat']), repr (result[s].varFloat))

        for i in test[s].keys ():
            if i == 'varFloat':
                continue

            if test[s][i] != getattr (result[s], i):
                raise Exception, "@ %d.%s expected %s, got %s" % \
                    (s, i, repr (test[s][i]), repr (getattr (result[s], i)))

def testEchoVeryLargeFloat (server, action, harsh):
    test = 2.2535e29
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if not nearlyeq (result, test):
        raise Exception, "expected %s, got %s" % (repr (test), repr (result))

def testEchoVerySmallFloat (server, action, harsh):
    test = 2.2535e29
    server = server._sa (action % {'methodname': 'echoFloat'})
    result = server.echoFloat (inputFloat = test)

    if not SOAP.Config.typed:
        result = float (result)

    if not nearlyeq (result, test):
        raise Exception, "expected %s, got %s" % (repr (test), repr (result))

def testEchoVoid (server, action, harsh):
    server = server._sa (action % {'methodname': 'echoVoid'})
    result = server.echoVoid ()

    for k in result.__dict__.keys ():
        if k[0] != '_':
            raise Exception, "expected an empty structType, got %s" % \
                repr (result.__dict__)

def testMustUnderstandEqualsOne (server, action, harsh):
    test = 42
    server = server._sa (action % {'methodname': 'echoInteger'})
    hd = SOAP.headerType ()
    hd.MustUnderstandThis = SOAP.stringType ("This should fault because "
        "the mustUnderstand attribute is 1")
    hd.MustUnderstandThis._setMustUnderstand (1)
    server = server._hd (hd) 

    try:
        result = server.echoInteger (inputInteger = test)
    except SOAP.faultType, e:
        if harsh and e.faultcode != 'SOAP-ENV:MustUnderstand':
            raise AttributeError, "unexpected faultcode %s" % e.faultcode
        return

    raise Exception, "should fail, succeeded with %s" % result

def testMustUnderstandEqualsZero (server, action, harsh):
    test = 42
    server = server._sa (action % {'methodname': 'echoInteger'})
    hd = SOAP.headerType ()
    hd.MustUnderstandThis = SOAP.stringType ("This shouldn't fault because "
        "the mustUnderstand attribute is 0")
    hd.MustUnderstandThis._setMustUnderstand (0)
    server = server._hd (hd) 

    result = server.echoInteger (inputInteger = test)

    if not SOAP.Config.typed:
        result = int (result)

    if result != test:
        raise Exception, "expected %s, got %s" % (test, result)

def testEchoDate (server, action, harsh):
    test = time.gmtime (time.time ())
    server = server._sa (action % {'methodname': 'echoDate'})
    if SOAP.Config.namespaceStyle == '1999':
        result = server.echoDate (inputDate = SOAP.timeInstantType (test))
    else:
        result = server.echoDate (inputDate = SOAP.dateTimeType (test))

    if not SOAP.Config.typed and type (result) in (type (''), type (u'')):
        p = SOAP.SOAPParser()
        result = p.convertDateTime(result, 'timeInstant')

    if result != test[:6]:
        raise Exception, "expected %s, got %s" % (repr (test), repr (result))

def testEchoBase64 (server, action, harsh):
    test = '\x00\x10\x20\x30\x40\x50\x60\x70\x80\x90\xa0\xb0\xc0\xd0\xe0\xf0'
    server = server._sa (action % {'methodname': 'echoBase64'})
    result = server.echoBase64 (inputBase64 = SOAP.base64Type (test))

    if not SOAP.Config.typed:
        import base64
        result = base64.decodestring(result)

    if result != test:
        raise Exception, "expected %s, got %s" % (repr (test), repr (result))


def main ():
    stats = 1
    total = 0
    fail = 0
    failok = 0
    succeed = 0
    exitonfailure = 0
    harsh = 0
    invert = 0
    printtrace = 0
    methodnums = None
    notimp = 0
    output = 'f'
    servers = DEFAULT_SERVERS_FILE

    started = time.time ()

    try:
        opts, args = getopt.getopt (sys.argv[1:], '?dehim:nNo:s:tT',
            ['help', 'debug', 'exit-on-failure', 'harsh', 'invert',
                'method', 'no-stats', 'no-statistics',
                'no-boring-statistics', 'no-boring-stats', 'output',
                'servers=', 'stacktrace', 'always-stacktrace'])

        for opt, arg in opts:
            if opt in ('-?', '--help'):
                usage ()
            elif opt in ('-d', '--debug'):
                SOAP.Config.debug = 1
            elif opt in ('-h', '--harsh'):
                harsh = 1
            elif opt in ('-i', '--invert'):
                invert = 1
            elif opt in ('-e', '--exit-on-failure'):
                exitonfailure = 1
            elif opt in ('-m', '--method'):
                if arg == '?':
                    methodUsage ()
                methodnums = str2list (arg)
            elif opt in ('-n', '--no-stats', '--no-statistics'):
                stats = 0
            elif opt in ('-N', '--no-boring-stats', '--no-boring-statistics'):
                stats = -1
            elif opt in ('-o', '--output'):
                output = arg
            elif opt in ('-s', '--servers'):
                servers = arg
            elif opt in ('-t', '--stacktrace'):
                printtrace = 1
            elif opt in ('-T', '--always-stacktrace'):
                printtrace = 2
            else:
                raise AttributeError, \
                     "Recognized but unimplemented option `%s'" % opt
    except SystemExit:
        raise
    except:
        usage (sys.exc_info ()[1])

    if 'a' in output:
        output = 'fFns'

    servers = readServers (servers)

    if methodnums == None:
        methodnums = range (1, len (DEFAULT_METHODS) + 1)

    limitre = re.compile ('|'.join (args), re.IGNORECASE)

    for s in servers:
        if (not not limitre.match (s['name'])) == invert:
            continue

        try: typed = s['typed']
        except: typed = 1

        try: style = s['style']
        except: style = 1999

        SOAP.Config.typed = typed
        SOAP.Config.namespaceStyle = style

        server = SOAP.SOAPProxy (s['endpoint'], ("m", s['namespace']))

        for num in (methodnums):
            if num > len (DEFAULT_METHODS):
                break

            total += 1

            name = DEFAULT_METHODS[num - 1]

            title = '%s: %s (#%d)' % (s['name'], name, num)

            if SOAP.Config.debug:
                print "%s:" % title

            try:
                fn = globals ()['test' + name[0].upper () + name[1:]]
            except KeyboardInterrupt:
                raise
            except:
                if 'n' in output:
                    print title, "test not yet implemented"
                notimp += 1
                continue

            try:
                fn (server, s['soapaction'], harsh)
                if s['nonfunctional'].has_key (name):
                    print title, \
                        "succeeded despite being marked nonfunctional"
                if 's' in output:
                    print title, "succeeded"
                succeed += 1
            except KeyboardInterrupt:
                raise
            except:
                fault = str (sys.exc_info ()[1])
                if fault[-1] == '\n':
                    fault = fault[:-1]

                if s['nonfunctional'].has_key (name):
                    if 'F' in output:
                        t = 'as expected'
                        if s['nonfunctional'][name] != '':
                            t += ', ' + s['nonfunctional'][name]
                        print title, "failed (%s) -" % t, fault
                    if printtrace > 1:
                        traceback.print_exc ()
                    failok += 1
                else:
                    if 'f' in output:
                        print title, "failed -", fault
                    if printtrace:
                        traceback.print_exc ()
                    fail += 1

                    if exitonfailure:
                        return -1

    if stats:
        print "   Tests started at:", time.ctime (started)
        if stats > 0:
            print "        Total tests: %d" % total
            print "          Successes: %d (%3.2f%%)" % \
                (succeed, 100.0 * succeed / total)
        if stats > 0 or fail > 0:
            print "Failed unexpectedly: %d (%3.2f%%)" % \
                (fail, 100.0 * fail / total)
        if stats > 0:
            print " Failed as expected: %d (%3.2f%%)" % \
                (failok, 100.0 * failok / total)
        if stats > 0 or notimp > 0:
            print "    Not implemented: %d (%3.2f%%)" % \
                (notimp, 100.0 * notimp / total)

    return fail + notimp

if __name__ == '__main__':
    try:
        sys.exit (main ())
    except KeyboardInterrupt:
        sys.exit (0)
