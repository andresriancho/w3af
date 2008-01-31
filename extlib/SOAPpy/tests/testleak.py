#!/usr/bin/python 
 
import sys
sys.path.insert(1, "..")
import SOAPpy
import time
import gc 
import types

gc.set_debug(gc.DEBUG_SAVEALL) 

for i in range(400):
    try:
        t = SOAPpy.SOAP.parseSOAPRPC('bad soap payload') 
    except: pass

gc.collect()
if len(gc.garbage):
    print 'still leaking'
else:
    print 'no leak'
