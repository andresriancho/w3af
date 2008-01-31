"""
Check handing of unicode.
"""

import sys
sys.path.insert(1, "..")
from SOAPpy import *

# Uncomment to see outgoing HTTP headers and SOAP and incoming 
#Config.debug = 1
#Config.dumpHeadersIn = 1
#Config.dumpSOAPIn = 1
#Config.dumpSOAPOut = 1

# ask for returned SOAP responses to be converted to basic python types
Config.simplify_objects = 0

#Config.BuildWithNoType = 1
#Config.BuildWithNoNamespacePrefix = 1

server = SOAPProxy("http://localhost:9900/")

x = u'uMOO' # Single unicode string
y = server.echo_simple((x,))
assert( x==y[0] )

x = [u'uMoo1',u'uMoo2'] # array of unicode strings
y = server.echo_simple(x)
assert( x[0] == y[0] )
assert( x[1] == y[1] )

x = {
     u'A':1,
     u'B':u'B',
     'C':u'C',
     'D':'D'
     }
y = server.echo_simple(x)

for key in x.keys():
  assert( x[key] == y[0][key] )

print "Success"
