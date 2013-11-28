#!/usr/bin/env python

from __future__ import print_function

import os
import time

# See: w3af.core.controllers.ci.moth
FMT = '/tmp/moth-%s.txt'
HTTP_ADDRESS_FILE = FMT % 'http'
HTTPS_ADDRESS_FILE = FMT % 'https'

DELTA = 0.5

wait_time = 0

while True:
    time.sleep(DELTA)
    wait_time += DELTA
    
    if os.path.exists(HTTP_ADDRESS_FILE) and os.path.exists(HTTPS_ADDRESS_FILE):
        print('Started moth in %s seconds.' % wait_time)
        break  
    else:
        print('Waiting %s seconds for moth to start.' % DELTA)
        