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
Config.simplify_objects = 1

#Config.BuildWithNoType = 1
#Config.BuildWithNoNamespacePrefix = 1


def headers():
  '''Return a soap header containing all the needed information.'''
  hd = Types.headerType()
  hd.useragent = Types.stringType("foo")
  return hd

server = SOAPProxy("http://localhost:9900/",header=headers())

adgroupid = 197497504
keyword1 = { 'status': 'Moderate',
		'adGroupId': 197497504,
		'destinationURL': None,
		'language': '',
		'text': 'does not work',
		'negative': bool(0),
		'maxCpc': 50000,
		'type': 'Keyword',
		'id': 1 }
keyword2 = { 'status': 'Moderate',
		'adGroupId': 197497504,
		'destinationURL': None,
		'language': '',
		'text': 'yes it does not',
		'negative': bool(0),
		'maxCpc': 50000,
		'type': 'Keyword',
		'id': 2 }
keylist = [keyword1, keyword2]

# Check that the data goes through properly

retval = server.echo_simple(adgroupid, keylist)

kw1 = retval[1][0]
kw2 = retval[1][1]

assert(retval[0] == adgroupid)

for key in kw1.keys():
  assert(kw1[key]==keyword1[key])

for key in kw2.keys():
  assert(kw2[key]==keyword2[key])

# Check that the header is preserved
retval = server.echo_header((adgroupid, keylist))

assert(retval[1].has_key('useragent'))
assert(retval[1]['useragent'] == 'foo')

server.quit()

print "Success!"

