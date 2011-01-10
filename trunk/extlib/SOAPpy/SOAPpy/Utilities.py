"""
################################################################################
# Copyright (c) 2003, Pfizer
# Copyright (c) 2001, Cayce Ullman.
# Copyright (c) 2001, Brian Matthews.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of actzero, inc. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
"""

ident = '$Id: Utilities.py,v 1.4 2004/01/31 04:20:06 warnes Exp $'
from version import __version__

import exceptions
import copy
import re
import string
import sys
from types import *

# SOAPpy modules
from Errors import *

################################################################################
# Utility infielders
################################################################################
def collapseWhiteSpace(s):
    return re.sub('\s+', ' ', s).strip()

def decodeHexString(data):
    conv = {
            '0': 0x0, '1': 0x1, '2': 0x2, '3': 0x3, '4': 0x4,
            '5': 0x5, '6': 0x6, '7': 0x7, '8': 0x8, '9': 0x9,
            
            'a': 0xa, 'b': 0xb, 'c': 0xc, 'd': 0xd, 'e': 0xe,
            'f': 0xf,
            
            'A': 0xa, 'B': 0xb, 'C': 0xc, 'D': 0xd, 'E': 0xe,
            'F': 0xf,
            }
    
    ws = string.whitespace

    bin = ''

    i = 0

    while i < len(data):
        if data[i] not in ws:
            break
        i += 1

    low = 0

    while i < len(data):
        c = data[i]

        if c in string.whitespace:
            break

        try:
            c = conv[c]
        except KeyError:
            raise ValueError, \
                "invalid hex string character `%s'" % c

        if low:
            bin += chr(high * 16 + c)
            low = 0
        else:
            high = c
            low = 1

        i += 1

    if low:
        raise ValueError, "invalid hex string length"

    while i < len(data):
        if data[i] not in string.whitespace:
            raise ValueError, \
                "invalid hex string character `%s'" % c

        i += 1

    return bin

def encodeHexString(data):
    h = ''

    for i in data:
        h += "%02X" % ord(i)

    return h

def leapMonth(year, month):
    return month == 2 and \
        year % 4 == 0 and \
        (year % 100 != 0 or year % 400 == 0)

def cleanDate(d, first = 0):
    ranges = (None, (1, 12), (1, 31), (0, 23), (0, 59), (0, 61))
    months = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    names = ('year', 'month', 'day', 'hours', 'minutes', 'seconds')

    if len(d) != 6:
        raise ValueError, "date must have 6 elements"

    for i in range(first, 6):
        s = d[i]

        if type(s) == FloatType:
            if i < 5:
                try:
                    s = int(s)
                except OverflowError:
                    if i > 0:
                        raise
                    s = long(s)

                if s != d[i]:
                    raise ValueError, "%s must be integral" % names[i]

                d[i] = s
        elif type(s) == LongType:
            try: s = int(s)
            except: pass
        elif type(s) != IntType:
            raise TypeError, "%s isn't a valid type" % names[i]

        if i == first and s < 0:
            continue

        if ranges[i] != None and \
            (s < ranges[i][0] or ranges[i][1] < s):
            raise ValueError, "%s out of range" % names[i]

    if first < 6 and d[5] >= 61:
        raise ValueError, "seconds out of range"

    if first < 2:
        leap = first < 1 and leapMonth(d[0], d[1])

        if d[2] > months[d[1]] + leap:
            raise ValueError, "day out of range"

def debugHeader(title):
    s = '*** ' + title + ' '
    print s + ('*' * (72 - len(s)))

def debugFooter(title):
    print '*' * 72
    sys.stdout.flush()
