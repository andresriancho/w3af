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

from __future__ import nested_scopes

ident = '$Id: Types.py,v 1.19 2005/02/22 04:29:43 warnes Exp $'
from version import __version__

import UserList
import base64
import cgi
import urllib
import copy
import re
import time
from types import *

# SOAPpy modules
from Errors    import *
from NS        import NS
from Utilities import encodeHexString, cleanDate
from Config    import Config

###############################################################################
# Utility functions
###############################################################################

def isPrivate(name): return name[0]=='_'
def isPublic(name):  return name[0]!='_'

###############################################################################
# Types and Wrappers
###############################################################################

class anyType:
    _validURIs = (NS.XSD, NS.XSD2, NS.XSD3, NS.ENC)

    def __init__(self, data = None, name = None, typed = 1, attrs = None):
        if self.__class__ == anyType:
            raise Error, "anyType can't be instantiated directly"

        if type(name) in (ListType, TupleType):
            self._ns, self._name = name
        else:
            self._ns = self._validURIs[0]
            self._name = name
            
        self._typed = typed
        self._attrs = {}

        self._cache = None
        self._type = self._typeName()

        self._data = self._checkValueSpace(data)

        if attrs != None:
            self._setAttrs(attrs)

    def __str__(self):
        if hasattr(self,'_name') and self._name:
            return "<%s %s at %d>" % (self.__class__, self._name, id(self))
        return "<%s at %d>" % (self.__class__, id(self))

    __repr__ = __str__

    def _checkValueSpace(self, data):
        return data

    def _marshalData(self):
        return str(self._data)

    def _marshalAttrs(self, ns_map, builder):
        a = ''

        for attr, value in self._attrs.items():
            ns, n = builder.genns(ns_map, attr[0])
            a += n + ' %s%s="%s"' % \
                (ns, attr[1], cgi.escape(str(value), 1))

        return a

    def _fixAttr(self, attr):
        if type(attr) in (StringType, UnicodeType):
            attr = (None, attr)
        elif type(attr) == ListType:
            attr = tuple(attr)
        elif type(attr) != TupleType:
            raise AttributeError, "invalid attribute type"

        if len(attr) != 2:
            raise AttributeError, "invalid attribute length"

        if type(attr[0]) not in (NoneType, StringType, UnicodeType):
            raise AttributeError, "invalid attribute namespace URI type"

        return attr

    def _getAttr(self, attr):
        attr = self._fixAttr(attr)

        try:
            return self._attrs[attr]
        except:
            return None

    def _setAttr(self, attr, value):
        attr = self._fixAttr(attr)

        if type(value) is StringType:
            value = unicode(value)

        self._attrs[attr] = value
            

    def _setAttrs(self, attrs):
        if type(attrs) in (ListType, TupleType):
            for i in range(0, len(attrs), 2):
                self._setAttr(attrs[i], attrs[i + 1])

            return

        if type(attrs) == DictType:
            d = attrs
        elif isinstance(attrs, anyType):
            d = attrs._attrs
        else:
            raise AttributeError, "invalid attribute type"

        for attr, value in d.items():
            self._setAttr(attr, value)

    def _setMustUnderstand(self, val):
        self._setAttr((NS.ENV, "mustUnderstand"), val)

    def _getMustUnderstand(self):
        return self._getAttr((NS.ENV, "mustUnderstand"))

    def _setActor(self, val):
        self._setAttr((NS.ENV, "actor"), val)

    def _getActor(self):
        return self._getAttr((NS.ENV, "actor"))

    def _typeName(self):
        return self.__class__.__name__[:-4]

    def _validNamespaceURI(self, URI, strict):
        if not hasattr(self, '_typed') or not self._typed:
            return None
        if URI in self._validURIs:
            return URI
        if not strict:
            return self._ns
        raise AttributeError, \
            "not a valid namespace for type %s" % self._type

class voidType(anyType):
    pass

class stringType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type:" % self._type

        return data

class untypedType(stringType):
    def __init__(self, data = None, name = None, attrs = None):
        stringType.__init__(self, data, name, 0, attrs)

class IDType(stringType): pass
class NCNameType(stringType): pass
class NameType(stringType): pass
class ENTITYType(stringType): pass
class IDREFType(stringType): pass
class languageType(stringType): pass
class NMTOKENType(stringType): pass
class QNameType(stringType): pass

class tokenType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3)
    __invalidre = '[\n\t]|^ | $|  '

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        if type(self.__invalidre) == StringType:
            self.__invalidre = re.compile(self.__invalidre)

            if self.__invalidre.search(data):
                raise ValueError, "invalid %s value" % self._type

        return data

class normalizedStringType(anyType):
    _validURIs = (NS.XSD3,)
    __invalidre = '[\n\r\t]'

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        if type(self.__invalidre) == StringType:
            self.__invalidre = re.compile(self.__invalidre)

            if self.__invalidre.search(data):
                raise ValueError, "invalid %s value" % self._type

        return data

class CDATAType(normalizedStringType):
    _validURIs = (NS.XSD2,)

class booleanType(anyType):
    def __int__(self):
        return self._data

    __nonzero__ = __int__

    def _marshalData(self):
        return ['false', 'true'][self._data]

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if data in (0, '0', 'false', ''):
            return 0
        if data in (1, '1', 'true'):
            return 1
        raise ValueError, "invalid %s value" % self._type

class decimalType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType, FloatType):
            raise Error, "invalid %s value" % self._type

        return data

class floatType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType, FloatType) or \
            data < -3.4028234663852886E+38 or \
            data >  3.4028234663852886E+38:
            raise ValueError, "invalid %s value: %s" % (self._type, repr(data))

        return data

    def _marshalData(self):
        return "%.18g" % self._data # More precision

class doubleType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType, FloatType) or \
            data < -1.7976931348623158E+308 or \
            data  > 1.7976931348623157E+308:
            raise ValueError, "invalid %s value: %s" % (self._type, repr(data))

        return data

    def _marshalData(self):
        return "%.18g" % self._data # More precision

class durationType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        try:
            # A tuple or a scalar is OK, but make them into a list

            if type(data) == TupleType:
                data = list(data)
            elif type(data) != ListType:
                data = [data]

            if len(data) > 6:
                raise Exception, "too many values"

            # Now check the types of all the components, and find
            # the first nonzero element along the way.

            f = -1

            for i in range(len(data)):
                if data[i] == None:
                    data[i] = 0
                    continue

                if type(data[i]) not in \
                    (IntType, LongType, FloatType):
                    raise Exception, "element %d a bad type" % i

                if data[i] and f == -1:
                    f = i

            # If they're all 0, just use zero seconds.

            if f == -1:
                self._cache = 'PT0S'

                return (0,) * 6

            # Make sure only the last nonzero element has a decimal fraction
            # and only the first element is negative.

            d = -1

            for i in range(f, len(data)):
                if data[i]:
                    if d != -1:
                        raise Exception, \
                            "all except the last nonzero element must be " \
                            "integers"
                    if data[i] < 0 and i > f:
                        raise Exception, \
                            "only the first nonzero element can be negative"
                    elif data[i] != long(data[i]):
                        d = i

            # Pad the list on the left if necessary.

            if len(data) < 6:
                n = 6 - len(data)
                f += n
                d += n
                data = [0] * n + data

            # Save index of the first nonzero element and the decimal
            # element for _marshalData.

            self.__firstnonzero = f
            self.__decimal = d

        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            t = 0

            if d[self.__firstnonzero] < 0:
                s = '-P'
            else:
                s = 'P'

            t = 0

            for i in range(self.__firstnonzero, len(d)):
                if d[i]:
                    if i > 2 and not t:
                        s += 'T'
                        t = 1
                    if self.__decimal == i:
                        s += "%g" % abs(d[i])
                    else:
                        s += "%d" % long(abs(d[i]))
                    s += ['Y', 'M', 'D', 'H', 'M', 'S'][i]

            self._cache = s

        return self._cache

class timeDurationType(durationType):
    _validURIs = (NS.XSD, NS.XSD2, NS.ENC)

class dateTimeType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.time()

            if (type(data) in (IntType, LongType)):
                data = list(time.gmtime(data)[:6])
            elif (type(data) == FloatType):
                f = data - int(data)
                data = list(time.gmtime(int(data))[:6])
                data[5] += f
            elif type(data) in (ListType, TupleType):
                if len(data) < 6:
                    raise Exception, "not enough values"
                if len(data) > 9:
                    raise Exception, "too many values"

                data = list(data[:6])

                cleanDate(data)
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = "%04d-%02d-%02dT%02d:%02d:%02d" % ((abs(d[0]),) + d[1:])
            if d[0] < 0:
                s = '-' + s
            f = d[5] - int(d[5])
            if f != 0:
                s += ("%g" % f)[1:]
            s += 'Z'

            self._cache = s

        return self._cache

class recurringInstantType(anyType):
    _validURIs = (NS.XSD,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = list(time.gmtime(time.time())[:6])
            if (type(data) in (IntType, LongType)):
                data = list(time.gmtime(data)[:6])
            elif (type(data) == FloatType):
                f = data - int(data)
                data = list(time.gmtime(int(data))[:6])
                data[5] += f
            elif type(data) in (ListType, TupleType):
                if len(data) < 1:
                    raise Exception, "not enough values"
                if len(data) > 9:
                    raise Exception, "too many values"

                data = list(data[:6])

                if len(data) < 6:
                    data += [0] * (6 - len(data))

                f = len(data)

                for i in range(f):
                    if data[i] == None:
                        if f < i:
                            raise Exception, \
                                "only leftmost elements can be none"
                    else:
                        f = i
                        break

                cleanDate(data, f)
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            e = list(d)
            neg = ''

            if not e[0]:
                e[0] = '--'
            else:
                if e[0] < 0:
                    neg = '-'
                    e[0] = abs(e[0])
                if e[0] < 100:
                    e[0] = '-' + "%02d" % e[0]
                else:
                    e[0] = "%04d" % e[0]

            for i in range(1, len(e)):
                if e[i] == None or (i < 3 and e[i] == 0):
                    e[i] = '-'
                else:
                    if e[i] < 0:
                        neg = '-'
                        e[i] = abs(e[i])

                    e[i] = "%02d" % e[i]

            if d[5]:
                f = abs(d[5] - int(d[5]))

                if f:
                    e[5] += ("%g" % f)[1:]

            s = "%s%s-%s-%sT%s:%s:%sZ" % ((neg,) + tuple(e))

            self._cache = s

        return self._cache

class timeInstantType(dateTimeType):
    _validURIs = (NS.XSD, NS.XSD2, NS.ENC)

class timePeriodType(dateTimeType):
    _validURIs = (NS.XSD2, NS.ENC)

class timeType(anyType):
    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[3:6]
            elif (type(data) == FloatType):
                f = data - int(data)
                data = list(time.gmtime(int(data))[3:6])
                data[2] += f
            elif type(data) in (IntType, LongType):
                data = time.gmtime(data)[3:6]
            elif type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[3:6]
                elif len(data) > 3:
                    raise Exception, "too many values"

                data = [None, None, None] + list(data)

                if len(data) < 6:
                    data += [0] * (6 - len(data))

                cleanDate(data, 3)

                data = data[3:]
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = ''

            s = time.strftime("%H:%M:%S", (0, 0, 0) + d + (0, 0, -1))
            f = d[2] - int(d[2])
            if f != 0:
                s += ("%g" % f)[1:]
            s += 'Z'

            self._cache = s

        return self._cache

class dateType(anyType):
    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[0:3]
            elif type(data) in (IntType, LongType, FloatType):
                data = time.gmtime(data)[0:3]
            elif type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[0:3]
                elif len(data) > 3:
                    raise Exception, "too many values"

                data = list(data)

                if len(data) < 3:
                    data += [1, 1, 1][len(data):]

                data += [0, 0, 0]

                cleanDate(data)

                data = data[:3]
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = "%04d-%02d-%02dZ" % ((abs(d[0]),) + d[1:])
            if d[0] < 0:
                s = '-' + s

            self._cache = s

        return self._cache

class gYearMonthType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[0:2]
            elif type(data) in (IntType, LongType, FloatType):
                data = time.gmtime(data)[0:2]
            elif type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[0:2]
                elif len(data) > 2:
                    raise Exception, "too many values"

                data = list(data)

                if len(data) < 2:
                    data += [1, 1][len(data):]

                data += [1, 0, 0, 0]

                cleanDate(data)

                data = data[:2]
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = "%04d-%02dZ" % ((abs(d[0]),) + d[1:])
            if d[0] < 0:
                s = '-' + s

            self._cache = s

        return self._cache

class gYearType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[0:1]
            elif type(data) in (IntType, LongType, FloatType):
                data = [data]

            if type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[0:1]
                elif len(data) < 1:
                    raise Exception, "too few values"
                elif len(data) > 1:
                    raise Exception, "too many values"

                if type(data[0]) == FloatType:
                    try: s = int(data[0])
                    except: s = long(data[0])

                    if s != data[0]:
                        raise Exception, "not integral"

                    data = [s]
                elif type(data[0]) not in (IntType, LongType):
                    raise Exception, "bad type"
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return data[0]

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = "%04dZ" % abs(d)
            if d < 0:
                s = '-' + s

            self._cache = s

        return self._cache

class centuryType(anyType):
    _validURIs = (NS.XSD2, NS.ENC)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[0:1] / 100
            elif type(data) in (IntType, LongType, FloatType):
                data = [data]

            if type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[0:1] / 100
                elif len(data) < 1:
                    raise Exception, "too few values"
                elif len(data) > 1:
                    raise Exception, "too many values"

                if type(data[0]) == FloatType:
                    try: s = int(data[0])
                    except: s = long(data[0])

                    if s != data[0]:
                        raise Exception, "not integral"

                    data = [s]
                elif type(data[0]) not in (IntType, LongType):
                    raise Exception, "bad type"
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return data[0]

    def _marshalData(self):
        if self._cache == None:
            d = self._data
            s = "%02dZ" % abs(d)
            if d < 0:
                s = '-' + s

            self._cache = s

        return self._cache

class yearType(gYearType):
    _validURIs = (NS.XSD2, NS.ENC)

class gMonthDayType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[1:3]
            elif type(data) in (IntType, LongType, FloatType):
                data = time.gmtime(data)[1:3]
            elif type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[0:2]
                elif len(data) > 2:
                    raise Exception, "too many values"

                data = list(data)

                if len(data) < 2:
                    data += [1, 1][len(data):]

                data = [0] + data + [0, 0, 0]

                cleanDate(data, 1)

                data = data[1:3]
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return tuple(data)

    def _marshalData(self):
        if self._cache == None:
            self._cache = "--%02d-%02dZ" % self._data

        return self._cache

class recurringDateType(gMonthDayType):
    _validURIs = (NS.XSD2, NS.ENC)

class gMonthType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[1:2]
            elif type(data) in (IntType, LongType, FloatType):
                data = [data]

            if type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[1:2]
                elif len(data) < 1:
                    raise Exception, "too few values"
                elif len(data) > 1:
                    raise Exception, "too many values"

                if type(data[0]) == FloatType:
                    try: s = int(data[0])
                    except: s = long(data[0])

                    if s != data[0]:
                        raise Exception, "not integral"

                    data = [s]
                elif type(data[0]) not in (IntType, LongType):
                    raise Exception, "bad type"

                if data[0] < 1 or data[0] > 12:
                    raise Exception, "bad value"
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return data[0]

    def _marshalData(self):
        if self._cache == None:
            self._cache = "--%02d--Z" % self._data

        return self._cache

class monthType(gMonthType):
    _validURIs = (NS.XSD2, NS.ENC)

class gDayType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        try:
            if data == None:
                data = time.gmtime(time.time())[2:3]
            elif type(data) in (IntType, LongType, FloatType):
                data = [data]

            if type(data) in (ListType, TupleType):
                if len(data) == 9:
                    data = data[2:3]
                elif len(data) < 1:
                    raise Exception, "too few values"
                elif len(data) > 1:
                    raise Exception, "too many values"

                if type(data[0]) == FloatType:
                    try: s = int(data[0])
                    except: s = long(data[0])

                    if s != data[0]:
                        raise Exception, "not integral"

                    data = [s]
                elif type(data[0]) not in (IntType, LongType):
                    raise Exception, "bad type"

                if data[0] < 1 or data[0] > 31:
                    raise Exception, "bad value"
            else:
                raise Exception, "invalid type"
        except Exception, e:
            raise ValueError, "invalid %s value - %s" % (self._type, e)

        return data[0]

    def _marshalData(self):
        if self._cache == None:
            self._cache = "---%02dZ" % self._data

        return self._cache

class recurringDayType(gDayType):
    _validURIs = (NS.XSD2, NS.ENC)

class hexBinaryType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        return data

    def _marshalData(self):
        if self._cache == None:
            self._cache = encodeHexString(self._data)

        return self._cache

class base64BinaryType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        return data

    def _marshalData(self):
        if self._cache == None:
            self._cache = base64.encodestring(self._data)

        return self._cache

class base64Type(base64BinaryType):
    _validURIs = (NS.ENC,)

class binaryType(anyType):
    _validURIs = (NS.XSD, NS.ENC)

    def __init__(self, data, name = None, typed = 1, encoding = 'base64',
        attrs = None):

        anyType.__init__(self, data, name, typed, attrs)

        self._setAttr('encoding', encoding)

    def _marshalData(self):
        if self._cache == None:
            if self._getAttr((None, 'encoding')) == 'base64':
                self._cache = base64.encodestring(self._data)
            else:
                self._cache = encodeHexString(self._data)

        return self._cache

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        return data

    def _setAttr(self, attr, value):
        attr = self._fixAttr(attr)

        if attr[1] == 'encoding':
            if attr[0] != None or value not in ('base64', 'hex'):
                raise AttributeError, "invalid encoding"

            self._cache = None

        anyType._setAttr(self, attr, value)


class anyURIType(anyType):
    _validURIs = (NS.XSD3,)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (StringType, UnicodeType):
            raise AttributeError, "invalid %s type" % self._type

        return data

    def _marshalData(self):
        if self._cache == None:
            self._cache = urllib.quote(self._data)

        return self._cache

class uriType(anyURIType):
    _validURIs = (NS.XSD,)

class uriReferenceType(anyURIType):
    _validURIs = (NS.XSD2,)

class NOTATIONType(anyType):
    def __init__(self, data, name = None, typed = 1, attrs = None):

        if self.__class__ == NOTATIONType:
            raise Error, "a NOTATION can't be instantiated directly"

        anyType.__init__(self, data, name, typed, attrs)

class ENTITIESType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) in (StringType, UnicodeType):
            return (data,)

        if type(data) not in (ListType, TupleType) or \
            filter (lambda x: type(x) not in (StringType, UnicodeType), data):
            raise AttributeError, "invalid %s type" % self._type

        return data

    def _marshalData(self):
        return ' '.join(self._data)

class IDREFSType(ENTITIESType): pass
class NMTOKENSType(ENTITIESType): pass

class integerType(anyType):
    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType):
            raise ValueError, "invalid %s value" % self._type

        return data

class nonPositiveIntegerType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or data > 0:
            raise ValueError, "invalid %s value" % self._type

        return data

class non_Positive_IntegerType(nonPositiveIntegerType):
    _validURIs = (NS.XSD,)

    def _typeName(self):
        return 'non-positive-integer'

class negativeIntegerType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or data >= 0:
            raise ValueError, "invalid %s value" % self._type

        return data

class negative_IntegerType(negativeIntegerType):
    _validURIs = (NS.XSD,)

    def _typeName(self):
        return 'negative-integer'

class longType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < -9223372036854775808L or \
            data >  9223372036854775807L:
            raise ValueError, "invalid %s value" % self._type

        return data

class intType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < -2147483648L or \
            data >  2147483647:
            raise ValueError, "invalid %s value" % self._type

        return data

class shortType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < -32768 or \
            data >  32767:
            raise ValueError, "invalid %s value" % self._type

        return data

class byteType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < -128 or \
            data >  127:
            raise ValueError, "invalid %s value" % self._type

        return data

class nonNegativeIntegerType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or data < 0:
            raise ValueError, "invalid %s value" % self._type

        return data

class non_Negative_IntegerType(nonNegativeIntegerType):
    _validURIs = (NS.XSD,)

    def _typeName(self):
        return 'non-negative-integer'

class unsignedLongType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < 0 or \
            data > 18446744073709551615L:
            raise ValueError, "invalid %s value" % self._type

        return data

class unsignedIntType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < 0 or \
            data > 4294967295L:
            raise ValueError, "invalid %s value" % self._type

        return data

class unsignedShortType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < 0 or \
            data > 65535:
            raise ValueError, "invalid %s value" % self._type

        return data

class unsignedByteType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or \
            data < 0 or \
            data > 255:
            raise ValueError, "invalid %s value" % self._type

        return data

class positiveIntegerType(anyType):
    _validURIs = (NS.XSD2, NS.XSD3, NS.ENC)

    def _checkValueSpace(self, data):
        if data == None:
            raise ValueError, "must supply initial %s value" % self._type

        if type(data) not in (IntType, LongType) or data <= 0:
            raise ValueError, "invalid %s value" % self._type

        return data

class positive_IntegerType(positiveIntegerType):
    _validURIs = (NS.XSD,)

    def _typeName(self):
        return 'positive-integer'

# Now compound types

class compoundType(anyType):
    def __init__(self, data = None, name = None, typed = 1, attrs = None):
        if self.__class__ == compoundType:
            raise Error, "a compound can't be instantiated directly"

        anyType.__init__(self, data, name, typed, attrs)
        self._keyord    = []

        if type(data) == DictType:
            self.__dict__.update(data)

    def _aslist(self, item=None):
        if item is not None:
            return self.__dict__[self._keyord[item]]
        else:
            return map( lambda x: self.__dict__[x], self._keyord)

    def _asdict(self, item=None, encoding=Config.dict_encoding):
        if item is not None:
            if type(item) in (UnicodeType,StringType):
                item = item.encode(encoding)
            return self.__dict__[item]
        else:
            retval = {}
            def fun(x): retval[x.encode(encoding)] = self.__dict__[x]

            if hasattr(self, '_keyord'):
                map( fun, self._keyord)
            else:
                for name in dir(self):
                    if isPublic(name):
                        retval[name] = getattr(self,name)
            return retval

 
    def __getitem__(self, item):
        if type(item) == IntType:
            return self.__dict__[self._keyord[item]]
        else:
            return getattr(self, item)

    def __len__(self):
        return len(self._keyord)

    def __nonzero__(self):
        return 1

    def _keys(self):
        return filter(lambda x: x[0] != '_', self.__dict__.keys())

    def _addItem(self, name, value, attrs = None):

        if name in self._keyord:
            if type(self.__dict__[name]) != ListType:
                self.__dict__[name] = [self.__dict__[name]]
            self.__dict__[name].append(value)
        else:
            self.__dict__[name] = value
            self._keyord.append(name)
            
    def _placeItem(self, name, value, pos, subpos = 0, attrs = None):

        if subpos == 0 and type(self.__dict__[name]) != ListType:
            self.__dict__[name] = value
        else:
            self.__dict__[name][subpos] = value

        self._keyord[pos] = name


    def _getItemAsList(self, name, default = []):
        try:
            d = self.__dict__[name]
        except:
            return default

        if type(d) == ListType:
            return d
        return [d]

    def __str__(self):
        return anyType.__str__(self) + ": " + str(self._asdict())

    def __repr__(self):
        return self.__str__()

class structType(compoundType):
    pass

class headerType(structType):
    _validURIs = (NS.ENV,)

    def __init__(self, data = None, typed = 1, attrs = None):
        structType.__init__(self, data, "Header", typed, attrs)

class bodyType(structType):
    _validURIs = (NS.ENV,)

    def __init__(self, data = None, typed = 1, attrs = None):
        structType.__init__(self, data, "Body", typed, attrs)

class arrayType(UserList.UserList, compoundType):
    def __init__(self, data = None, name = None, attrs = None,
        offset = 0, rank = None, asize = 0, elemsname = None):

        if data:
            if type(data) not in (ListType, TupleType):
                raise Error, "Data must be a sequence"

        UserList.UserList.__init__(self, data)
        compoundType.__init__(self, data, name, 0, attrs)

        self._elemsname = elemsname or "item"

        if data == None:
            self._rank = rank

            # According to 5.4.2.2 in the SOAP spec, each element in a
            # sparse array must have a position. _posstate keeps track of
            # whether we've seen a position or not. It's possible values
            # are:
            # -1 No elements have been added, so the state is indeterminate
            #  0 An element without a position has been added, so no
            #    elements can have positions
            #  1 An element with a position has been added, so all elements
            #    must have positions

            self._posstate = -1

            self._full = 0

            if asize in ('', None):
                asize = '0'

            self._dims = map (lambda x: int(x), str(asize).split(','))
            self._dims.reverse()   # It's easier to work with this way
            self._poss = [0] * len(self._dims)      # This will end up
                                                    # reversed too

            for i in range(len(self._dims)):
                if self._dims[i] < 0 or \
                    self._dims[i] == 0 and len(self._dims) > 1:
                    raise TypeError, "invalid Array dimensions"

                if offset > 0:
                    self._poss[i] = offset % self._dims[i]
                    offset = int(offset / self._dims[i])

                # Don't break out of the loop if offset is 0 so we test all the
                # dimensions for > 0.
            if offset:
                raise AttributeError, "invalid Array offset"

            a = [None] * self._dims[0]

            for i in range(1, len(self._dims)):
                b = []

                for j in range(self._dims[i]):
                    b.append(copy.deepcopy(a))

                a = b

            self.data = a


    def _aslist(self, item=None):
        if item is not None:
            return self.data[int(item)]
        else:
            return self.data

    def _asdict(self, item=None, encoding=Config.dict_encoding):
        if item is not None:
            if type(item) in (UnicodeType,StringType):
                item = item.encode(encoding)
            return self.data[int(item)]
        else:
            retval = {}
            def fun(x): retval[str(x).encode(encoding)] = self.data[x]
            
            map( fun, range(len(self.data)) )
            return retval
 
    def __getitem__(self, item):
        try:
            return self.data[int(item)]
        except ValueError:
            return getattr(self, item)

    def __len__(self):
        return len(self.data)

    def __nonzero__(self):
        return 1

    def __str__(self):
        return anyType.__str__(self) + ": " + str(self._aslist())

    def _keys(self):
        return filter(lambda x: x[0] != '_', self.__dict__.keys())

    def _addItem(self, name, value, attrs):
        if self._full:
            raise ValueError, "Array is full"

        pos = attrs.get((NS.ENC, 'position'))

        if pos != None:
            if self._posstate == 0:
                raise AttributeError, \
                    "all elements in a sparse Array must have a " \
                    "position attribute"

            self._posstate = 1

            try:
                if pos[0] == '[' and pos[-1] == ']':
                    pos = map (lambda x: int(x), pos[1:-1].split(','))
                    pos.reverse()

                    if len(pos) == 1:
                        pos = pos[0]

                        curpos = [0] * len(self._dims)

                        for i in range(len(self._dims)):
                            curpos[i] = pos % self._dims[i]
                            pos = int(pos / self._dims[i])

                            if pos == 0:
                                break

                        if pos:
                            raise Exception
                    elif len(pos) != len(self._dims):
                        raise Exception
                    else:
                        for i in range(len(self._dims)):
                            if pos[i] >= self._dims[i]:
                                raise Exception

                        curpos = pos
                else:
                    raise Exception
            except:
                raise AttributeError, \
                    "invalid Array element position %s" % str(pos)
        else:
            if self._posstate == 1:
                raise AttributeError, \
                    "only elements in a sparse Array may have a " \
                    "position attribute"

            self._posstate = 0

            curpos = self._poss

        a = self.data

        for i in range(len(self._dims) - 1, 0, -1):
            a = a[curpos[i]]

        if curpos[0] >= len(a):
            a += [None] * (len(a) - curpos[0] + 1)

        a[curpos[0]] = value

        if pos == None:
            self._poss[0] += 1

            for i in range(len(self._dims) - 1):
                if self._poss[i] < self._dims[i]:
                    break

                self._poss[i] = 0
                self._poss[i + 1] += 1

            if self._dims[-1] and self._poss[-1] >= self._dims[-1]:
                #self._full = 1
                #FIXME: why is this occuring?
                pass

    def _placeItem(self, name, value, pos, subpos, attrs = None):
        curpos = [0] * len(self._dims)

        for i in range(len(self._dims)):
            if self._dims[i] == 0:
                curpos[0] = pos
                break

            curpos[i] = pos % self._dims[i]
            pos = int(pos / self._dims[i])

            if pos == 0:
                break

        if self._dims[i] != 0 and pos:
            raise Error, "array index out of range"

        a = self.data

        for i in range(len(self._dims) - 1, 0, -1):
            a = a[curpos[i]]

        if curpos[0] >= len(a):
            a += [None] * (len(a) - curpos[0] + 1)

        a[curpos[0]] = value

class typedArrayType(arrayType):
    def __init__(self, data = None, name = None, typed = None, attrs = None,
        offset = 0, rank = None, asize = 0, elemsname = None, complexType = 0):

        arrayType.__init__(self, data, name, attrs, offset, rank, asize,
            elemsname)

        self._typed = 1
        self._type = typed
        self._complexType = complexType

class faultType(structType, Error):
    def __init__(self, faultcode = "", faultstring = "", detail = None):
        self.faultcode = faultcode
        self.faultstring = faultstring
        if detail != None:
            self.detail = detail

        structType.__init__(self, None, 0)

    def _setDetail(self, detail = None):
        if detail != None:
            self.detail = detail
        else:
            try: del self.detail
            except AttributeError: pass

    def __repr__(self):
        if getattr(self, 'detail', None) != None:
            return "<Fault %s: %s: %s>" % (self.faultcode,
                                           self.faultstring,
                                           self.detail)
        else:
            return "<Fault %s: %s>" % (self.faultcode, self.faultstring)

    __str__ = __repr__

    def __call__(self):
        return (self.faultcode, self.faultstring, self.detail)        

class SOAPException(Exception):
    def __init__(self, code="", string="", detail=None):
        self.value = ("SOAPpy SOAP Exception", code, string, detail)
        self.code = code
        self.string = string
        self.detail = detail

    def __str__(self):
        return repr(self.value)

class RequiredHeaderMismatch(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class MethodNotFound(Exception):
    def __init__(self, value):
        (val, detail) = value.split(":")
        self.value = val
        self.detail = detail

    def __str__(self):
        return repr(self.value, self.detail)

class AuthorizationFailed(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class MethodFailed(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
        
#######
# Convert complex SOAPpy objects to native python equivalents
#######

def simplify(object, level=0):
    """
    Convert the SOAPpy objects and thier contents to simple python types.

    This function recursively converts the passed 'container' object,
    and all public subobjects. (Private subobjects have names that
    start with '_'.)
    
    Conversions:
    - faultType    --> raise python exception
    - arrayType    --> array
    - compoundType --> dictionary
    """
    
    if level > 10:
        return object
    
    if isinstance( object, faultType ):
        if object.faultstring == "Required Header Misunderstood":
            raise RequiredHeaderMismatch(object.detail)
        elif object.faultstring == "Method Not Found":
            raise MethodNotFound(object.detail)
        elif object.faultstring == "Authorization Failed":
            raise AuthorizationFailed(object.detail)
        elif object.faultstring == "Method Failed":
            raise MethodFailed(object.detail)
        else:
            se = SOAPException(object.faultcode, object.faultstring,
                               object.detail)
            raise se
    elif isinstance( object, arrayType ):
        data = object._aslist()
        for k in range(len(data)):
            data[k] = simplify(data[k], level=level+1)
        return data
    elif isinstance( object, compoundType ) or isinstance(object, structType):
        data = object._asdict()
        for k in data.keys():
            if isPublic(k):
                data[k] = simplify(data[k], level=level+1)
        return data
    elif type(object)==DictType:
        for k in object.keys():
            if isPublic(k):
                object[k] = simplify(object[k])
        return object
    elif type(object)==list:
        for k in range(len(object)):
            object[k] = simplify(object[k])
        return object
    else:
        return object


def simplify_contents(object, level=0):
    """
    Convert the contents of SOAPpy objects to simple python types.

    This function recursively converts the sub-objects contained in a
    'container' object to simple python types.
    
    Conversions:
    - faultType    --> raise python exception
    - arrayType    --> array
    - compoundType --> dictionary
    """
    
    if level>10: return object

    if isinstance( object, faultType ):
        for k in object._keys():
            if isPublic(k):
                setattr(object, k, simplify(object[k], level=level+1))
        raise object
    elif isinstance( object, arrayType ): 
        data = object._aslist()
        for k in range(len(data)):
            object[k] = simplify(data[k], level=level+1)
    elif isinstance(object, structType):
        data = object._asdict()
        for k in data.keys():
            if isPublic(k):
                setattr(object, k, simplify(data[k], level=level+1))
    elif isinstance( object, compoundType ) :
        data = object._asdict()
        for k in data.keys():
            if isPublic(k):
                object[k] = simplify(data[k], level=level+1)
    elif type(object)==DictType:
        for k in object.keys():
            if isPublic(k):
                object[k] = simplify(object[k])
    elif type(object)==list:
        for k in range(len(object)):
            object[k] = simplify(object[k])
    
    return object


