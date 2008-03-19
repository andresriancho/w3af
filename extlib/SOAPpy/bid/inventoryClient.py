#!/usr/bin/env python


import getopt
import sys
import string
import re
import time
sys.path.insert(1,"..")
from SOAPpy import SOAP
import traceback

DEFAULT_SERVERS_FILE        = './inventory.servers'

DEFAULT_METHODS =  ('SimpleBuy', 'RequestForQuote','Buy','Ping')

def usage (error = None):
    sys.stdout = sys.stderr

    if error != None:
        print error

    print """usage: %s [options] [server ...]
  If a long option shows an argument is mandatory, it's mandatory for the
  equivalent short option also.

  -?, --help            display this usage
  -d, --debug           turn on debugging in the SOAP library
  -i, --invert          test servers *not* in the list of servers given
  -m, --method=METHOD#[,METHOD#...]
                        call only the given methods, specify a METHOD# of ?
                        for the list of method numbers
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


def readServers (file):
    servers = []
    f = open (file, 'r')

    while 1:
        line = f.readline ()

        if line == '':
            break

        if line[0] in ('#', '\n') or line[0] in string.whitespace:
            continue

        cur = {'nonfunctional': {}}
        tag = None
        servers.append (cur)

        while 1:
            if line[0] in string.whitespace:
                if tag == 'nonfunctional':
                    value = method + ' ' + cur[tag][method]
                else:
                    value = cur[tag]
                value += ' ' + line.strip ()
            else:
                tag, value = line.split (':', 1)

                tag = tag.strip ().lower ()
                value = value.strip ()

                if value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]

            if tag == 'nonfunctional':
                value = value.split (' ', 1) + ['']

                method = value[0]
                cur[tag][method] = value[1]
            else:
                cur[tag] = value

            line = f.readline ()

            if line == '' or line[0] == '\n':
                break

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

def SimpleBuy(serv, sa, epname):
    serv = serv._sa (sa % {'methodname':'SimpleBuy'})
    return serv.SimpleBuy(ProductName="widget", Quantity = 50, Address = "this is my address") #JHawk, Phalanx require this order of params


def RequestForQuote(serv, sa, epname):
    serv = serv._sa (sa % {'methodname':'RequestForQuote'})
    return serv.RequestForQuote(Quantity=3, ProductName = "thing") # for Phalanx, JHawk


def Buy(serv, sa, epname):
    import copy
    serv = serv._sa (sa % {'methodname':'Buy'})
    billTo_d = {"name":"Buyer One", "address":"1 1st Street",
              "city":"New York", "state":"NY", "zipCode":"10000"}
    shipTo_d = {"name":"Buyer One ", "address":"1 1st Street ",
              "city":"New York ", "state":"NY ", "zipCode":"10000 "}
         
    for k,v in shipTo_d.items():
        shipTo_d[k] = v[:-1]
        
    itemd1 = SOAP.structType( {"name":"widg1","quantity":200,"price":SOAP.decimalType(45.99), "_typename":"LineItem"})
    itemd2 = SOAP.structType( {"name":"widg2","quantity":400,"price":SOAP.decimalType(33.45), "_typename":"LineItem"})

    items_d = SOAP.arrayType( [itemd1, itemd2] )
    items_d._ns = "http://www.soapinterop.org/Bid"
    po_d = SOAP.structType( data = {"poID":"myord","createDate":SOAP.dateTimeType(),"shipTo":shipTo_d, "billTo":billTo_d, "items":items_d})
    try:
        # it's called PO by MST (MS SOAP Toolkit), JHawk (.NET Remoting),
        # Idoox WASP, Paul (SOAP::Lite), PranishK (ATL), GLUE, Aumsoft,
        # HP, EasySoap, and Jake (Frontier).  [Actzero accepts either]
        return serv.Buy(PO=po_d) 
    except:
        # called PurchaseOrder by KeithBa 
        return serv.Buy(PurchaseOrder=po_d) 


def Ping(serv, sa, epname):
    serv = serv._sa (sa % {'methodname':'Ping'})
    return serv.Ping()

def main():
    servers = DEFAULT_SERVERS_FILE
    methodnums = None
    output = 'f'
    invert = 0
    succeed = 0
    printtrace = 0
    stats = 1
    total = 0
    fail = 0
    failok = 0
    notimp = 0

    try:
        opts,args = getopt.getopt (sys.argv[1:], '?dm:io:s:t',
                                   ['help', 'method', 'debug', 'invert',
                                    'output', 'servers='])
        for opt, arg in opts:
            if opt in ('-?', '--help'):
                usage ()
            elif opt in ('-d', '--debug'):
                SOAP.Config.debug = 1
            elif opt in ('-i', '--invert'):
                invert = 1
            elif opt in ('-m', '--method'):
                if arg == '?':
                    methodUsage ()
                methodnums = str2list (arg)
            elif opt in ('-o', '--output'):
                output = arg
            elif opt in ('-s', '--servers'):
                servers = arg
            else:
                raise AttributeError, \
                     "Recognized but unimplemented option `%s'" % opt
    except SystemExit:
        raise
    except:
        usage (sys.exc_info ()[1])

    if 'a' in output:
        output = 'fFns'

    servers = readServers(servers)

    if methodnums == None:
        methodnums = range (1, len (DEFAULT_METHODS) + 1)
      
    limitre = re.compile ('|'.join (args), re.IGNORECASE)
    
    for s in servers:
        if (not not limitre.match (s['name'])) == invert:
            continue
        
        serv = SOAP.SOAPProxy(s['endpoint'], namespace = s['namespace'])

        for num in (methodnums):
            if num > len(DEFAULT_METHODS):
                break

            total += 1

            name = DEFAULT_METHODS[num - 1]

            title = '%s: %s (#%d)' % (s['name'], name, num)

            try:
                fn = globals ()[name]
            except KeyboardInterrupt:
                raise
            except:
                if 'n' in output:
                    print title, "test not yet implemented"
                notimp += 1
                continue

            try:
                res = fn (serv, s['soapaction'], s['name'])
                if s['nonfunctional'].has_key (name):
                    print title, "succeeded despite marked nonfunctional"
                elif 's' in output:
                    print title, "succeeded "
                succeed += 1
            except KeyboardInterrupt:
                print "fail"
                raise
            except:
                if s['nonfunctional'].has_key (name):
                    if 'F' in output:
                        t = 'as expected'
                        if s['nonfunctional'][name] != '':
                            t += ', ' + s['nonfunctional'][name]
                        print title, "failed (%s) -" %t, sys.exc_info()[1]
                    failok += 1
                else:
                    if 'f' in output:
                        print title, "failed -", str (sys.exc_info()[1])
                    fail += 1

    if stats:
        print "   Tests ended at:", time.ctime (time.time())
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
    
    

if __name__ == "__main__":
    main()

