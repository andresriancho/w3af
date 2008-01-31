#!/usr/bin/env python

import time
from SOAPpy import SOAP

srv = SOAP.SOAPProxy('http://localhost:10080/')

for p in ('good param', 'ok param'):
    ret = srv.badparam(p)
    if isinstance(ret, SOAP.faultType):
        print ret
    else:
        print 'ok'

dt = SOAP.dateTimeType(time.localtime(time.time()))
print srv.dt(dt)



