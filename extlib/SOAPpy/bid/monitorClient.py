from SOAPpy import SOAP
import sys
import getopt


def usage():
    print """usage: %s [options]
    -m, --method=METHOD#[,METHOD#...] specify METHOD# of ? for the list
    -p, --port=PORT#  allows to specify PORT# of server
    """
    sys.exit(1)

def methodUsage():
    print "The available methods are:"
    print "1. Monitor \t\t2. Clear"
    sys.exit(0)


port = 12080 
methodnum = 1

try:
    opts, args = getopt.getopt (sys.argv[1:], 'p:m:', ['method','port'])
    for opt, arg in opts:
        if opt in ('-m','--method'):
            if arg == '?':
                methodUsage()
            methodnum = int(arg)
        elif opt in ('-p', '--port'):
            port = int(arg)
        else:
            raise AttributeError, "Recognized but unimpl option '%s'" % opt
except SystemExit:
    raise
except:
    usage ()

ep = "http://208.177.157.221:%d/xmethodsInterop" % (port)
sa = "urn:soapinterop"
ns = "http://www.soapinterop.org/Bid"

serv = SOAP.SOAPProxy(ep, namespace =ns, soapaction = sa)
if methodnum == 1:
    print serv.Monitor(str="actzero")
elif methodnum == 2:
    print serv.Clear(str="actzero")
else:
    print "invalid methodnum"
    methodUsage()

