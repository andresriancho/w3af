#!/usr/bin/env python
# Copyright (c) 2001, actzero, inc.
import sys
sys.path.insert(1,"..")
from SOAPpy import SOAP
#SOAP.Config.debug = 1
serverstring = "SOAP.py (actzero.com) running "+sys.platform
NUMBUYS = 0
NUMSIMPLEBUYS = 0
NUMREQUESTS = 0
NUMPINGS = 0

def SimpleBuy(Address, ProductName, Quantity):
    # currently, this type-checks the params, and makes sure
    # the strings are of len > 0
    global NUMSIMPLEBUYS
    NUMSIMPLEBUYS += 1
    if Quantity < 1: raise ValueError, "must order at least one"
    else:  return "Receipt for %d %s(s) bought from %s" % (int(Quantity), ProductName, serverstring) 


def RequestForQuote(ProductName, Quantity):
    # type-checks and makes sure Quantity >= 1
    global NUMREQUESTS
    NUMREQUESTS += 1
    if Quantity < 1: raise ValueError, "must order at least 1"
    else:
        import whrandom
        mult = whrandom.random()
        times = 0
        while mult > 0.25:
            mult = mult - 0.25
            times += 1
        mult += 0.5
        mult = round(mult, 3)
        print mult, times
        return SOAP.doubleType(round(mult*int(Quantity),2))

    
def Buy(**kw):
    
    global NUMBUYS
    NUMBUYS += 1
    try:
        PurchaseOrder = kw["PurchaseOrder"]
    except:
        PurchaseOrder = kw["PO"]
    try:
        POkeys = PurchaseOrder['_keyord']
        POkeys.sort()
        POkeys_expected = ["shipTo","billTo","items","poID","createDate"]
        POkeys_expected.sort()
        if POkeys != POkeys_expected:
            raise ValueError, "struct 'PurchaseOrder' needs %s, %s, %s, %s, and %s" % tuple(POkeys_expected)
    except:
        raise TypeError, "'PurchaseOrder' missing one or more element(s)"

    try:
        btkeys = PurchaseOrder["billTo"]["_keyord"]
        btkeys.sort()
        btkeys_expected = ["address","zipCode","name","state","city"]
        btkeys_expected.sort()
    except:
        raise TypeError, "'billTo' missing one or more elements"

    try:
        stkeys = PurchaseOrder["shipTo"]["_keyord"]
        stkeys.sort()
        stkeys_expected = ["address","zipCode","name","state","city"]
        stkeys_expected.sort()
    except:
        raise TypeError, "'shipTo' missing one or more elements"
        
    
    try:
        items =  PurchaseOrder["items"].__dict__
        data = items["data"]
        retstring = ""
        for item in data:
            itemdict = item["_asdict"]
            q = itemdict["quantity"]
            p = itemdict["price"]
            name = itemdict["name"]
            if retstring != "":
                retstring += ", "
            else:
                retstring = "bought "
            retstring += "%d %s(s) for %.2f" % (q,name,p)
        retstring += " from "+serverstring 
        return retstring
    
    except:
        raise TypeError, "items must be an array of 'item' structs"

def Ping():
    global NUMPINGS
    NUMPINGS += 1
    return

def Monitor(str):
    if str=="actzero":
        global NUMBUYS
        global NUMREQUESTS
        global NUMSIMPLEBUYS
        global NUMPINGS
        return "(Buys, RequestForQuote(s),SimpleBuy(s), Ping(s)) = " + \
               repr( (NUMBUYS,NUMREQUESTS,NUMSIMPLEBUYS, NUMPINGS) )
    else:
        raise ValueError, "not the right string"

def Clear(str):
    if str=="actzero":
        global NUMBUYS
        global NUMREQUESTS
        global NUMSIMPLEBUYS
        global NUMPINGS
        NUMBUYS = 0
        NUMREQUESTS = 0
        NUMSIMPLEBUYS = 0
        NUMPINGS = 0
        return "(Buys, RequestForQuote(s),SimpleBuy(s), Ping(s)) = " + \
               repr( (NUMBUYS,NUMREQUESTS,NUMSIMPLEBUYS, NUMPINGS) )
    else:
        raise ValueError, "not the right string"

    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port not in range(2000,15000): raise ValueError
        except:
            print "port must be a number between 2000 and 15000"
            sys.exit(1)
    else: port = 9000
    namespace = "http://www.soapinterop.org/Bid"
    server = SOAP.SOAPServer( ('zoo',port) )

    server.registerKWFunction(SimpleBuy, namespace )
    server.registerKWFunction(RequestForQuote, namespace )
    server.registerKWFunction(Buy, namespace )
    server.registerKWFunction(Ping, namespace )
    server.registerKWFunction(Monitor, namespace )
    server.registerKWFunction(Clear, namespace )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
