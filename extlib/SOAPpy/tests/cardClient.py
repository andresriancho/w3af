#!/usr/bin/env python

# Copyright (c) 2001 actzero, inc. All rights reserved.

import sys

sys.path.insert (1, '..')

from SOAPpy import *

ident = '$Id: cardClient.py,v 1.4 2004/02/18 21:22:13 warnes Exp $'

endpoint = "http://localhost:12027/xmethodsInterop"
sa = "urn:soapinterop"
ns = "http://soapinterop.org/"

serv = SOAPProxy(endpoint, namespace=ns, soapaction=sa)
try: hand =  serv.dealHand(NumberOfCards = 13, StringSeparator = '\n')
except: print "no dealHand"; hand = 0
try: sortedhand = serv.dealArrangedHand(NumberOfCards=13,StringSeparator='\n')
except: print "no sorted"; sortedhand = 0
try: card = serv.dealCard()
except: print "no card"; card = 0

print "*****hand****\n",hand,"\n*********"
print "******sortedhand*****\n",sortedhand,"\n*********"
print "card:",card

serv.quit()

