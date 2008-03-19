#!/usr/bin/python
################################################################################
#
# SOAP.py 0.9.7 - Cayce Ullman    (cayce@actzero.com)
#                 Brian Matthews  (blm@actzero.com)
#
# INCLUDED:
# - General SOAP Parser based on sax.xml (requires Python 2.0)
# - General SOAP Builder
# - SOAP Proxy for RPC client code
# - SOAP Server framework for RPC server code
#
# FEATURES:
# - Handles all of the types in the BDG
# - Handles faults
# - Allows namespace specification
# - Allows SOAPAction specification
# - Homogeneous typed arrays
# - Supports multiple schemas
# - Header support (mustUnderstand and actor)
# - XML attribute support
# - Multi-referencing support (Parser/Builder)
# - Understands SOAP-ENC:root attribute
# - Good interop, passes all client tests for Frontier, SOAP::LITE, SOAPRMI
# - Encodings
# - SSL clients (with OpenSSL configured in to Python)
# - SSL servers (with OpenSSL configured in to Python and M2Crypto installed)
#
# TODO:
# - Timeout on method calls - MCU
# - Arrays (sparse, multidimensional and partial) - BLM
# - Clean up data types - BLM
# - Type coercion system (Builder) - MCU
# - Early WSDL Support - MCU
# - Attachments - BLM
# - setup.py - MCU
# - mod_python example - MCU
# - medusa example - MCU
# - Documentation - JAG
# - Look at performance
#
################################################################################
#
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
#
# Additional changes:
# 0.9.7.3 - 4/18/2002 - Mark Pilgrim (f8dy@diveintomark.org)
#   added dump_dict as alias for dump_dictionary for Python 2.2 compatibility
# 0.9.7.2 - 4/12/2002 - Mark Pilgrim (f8dy@diveintomark.org)
#   fixed logic to unmarshal the value of "null" attributes ("true" or "1"
#   means true, others false)
# 0.9.7.1 - 4/11/2002 - Mark Pilgrim (f8dy@diveintomark.org)
#   added "dump_str" as alias for "dump_string" for Python 2.2 compatibility
#   Between 2.1 and 2.2, type("").__name__ changed from "string" to "str"
################################################################################

import xml.sax
import UserList
import base64
import cgi
import urllib
import exceptions
import copy
import re
import socket
import string
import sys
import time
import SocketServer
from types import *

try: from M2Crypto import SSL
except: pass

ident = '$Id: SOAP.py,v 1.1.1.1 2004/01/16 16:15:18 bluecoat93 Exp $'

__version__ = "0.9.7.3"

# Platform hackery

# Check float support
try:
    float("NaN")
    float("INF")
    float("-INF")
    good_float = 1
except:
    good_float = 0

################################################################################
# Exceptions
################################################################################
class Error(exceptions.Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return "<Error : %s>" % self.msg
    __repr__ = __str__

class RecursionError(Error):
    pass

class UnknownTypeError(Error):
    pass

class HTTPError(Error):
    # indicates an HTTP protocol error
    def __init__(self, code, msg):
        self.code = code
        self.msg  = msg
    def __str__(self):
        return "<HTTPError %s %s>" % (self.code, self.msg)
    __repr__ = __str__

##############################################################################
# Namespace Class
################################################################################
def invertDict(dict):
    d = {}

    for k, v in dict.items():
        d[v] = k

    return d

class NS:
    XML  = "http://www.w3.org/XML/1998/namespace"

    ENV  = "http://schemas.xmlsoap.org/soap/envelope/"
    ENC  = "http://schemas.xmlsoap.org/soap/encoding/"

    XSD  = "http://www.w3.org/1999/XMLSchema"
    XSD2 = "http://www.w3.org/2000/10/XMLSchema"
    XSD3 = "http://www.w3.org/2001/XMLSchema"

    XSD_L = [XSD, XSD2, XSD3]
    EXSD_L= [ENC, XSD, XSD2, XSD3]

    XSI   = "http://www.w3.org/1999/XMLSchema-instance"
    XSI2  = "http://www.w3.org/2000/10/XMLSchema-instance"
    XSI3  = "http://www.w3.org/2001/XMLSchema-instance"
    XSI_L = [XSI, XSI2, XSI3]

    URN   = "http://soapinterop.org/xsd"

    # For generated messages
    XML_T = "xml"
    ENV_T = "SOAP-ENV"
    ENC_T = "SOAP-ENC"
    XSD_T = "xsd"
    XSD2_T= "xsd2"
    XSD3_T= "xsd3"
    XSI_T = "xsi"
    XSI2_T= "xsi2"
    XSI3_T= "xsi3"
    URN_T = "urn"

    NSMAP       = {ENV_T: ENV, ENC_T: ENC, XSD_T: XSD, XSD2_T: XSD2,
                    XSD3_T: XSD3, XSI_T: XSI, XSI2_T: XSI2, XSI3_T: XSI3,
                    URN_T: URN}
    NSMAP_R     = invertDict(NSMAP)

    STMAP       = {'1999': (XSD_T, XSI_T), '2000': (XSD2_T, XSI2_T),
                    '2001': (XSD3_T, XSI3_T)}
    STMAP_R     = invertDict(STMAP)

    def __init__(self):
        raise Error, "Don't instantiate this"

################################################################################
# Configuration class
################################################################################

class SOAPConfig:
    __readonly = ('SSLserver', 'SSLclient')

    def __init__(self, config = None, **kw):
        d = self.__dict__

        if config:
            if not isinstance(config, SOAPConfig):
                raise AttributeError, \
                    "initializer must be SOAPConfig instance"

            s = config.__dict__

            for k, v in s.items():
                if k[0] != '_':
                    d[k] = v
        else:
            # Setting debug also sets returnFaultInfo, dumpFaultInfo,
            # dumpHeadersIn, dumpHeadersOut, dumpSOAPIn, and dumpSOAPOut
            self.debug = 0
            # Setting namespaceStyle sets typesNamespace, typesNamespaceURI,
            # schemaNamespace, and schemaNamespaceURI
            self.namespaceStyle = '1999'
            self.strictNamespaces = 0
            self.typed = 1
            self.buildWithNamespacePrefix = 1
            self.returnAllAttrs = 0

            try: SSL; d['SSLserver'] = 1
            except: d['SSLserver'] = 0

            try: socket.ssl; d['SSLclient'] = 1
            except: d['SSLclient'] = 0

        for k, v in kw.items():
            if k[0] != '_':
                setattr(self, k, v)

    def __setattr__(self, name, value):
        if name in self.__readonly:
            raise AttributeError, "readonly configuration setting"

        d = self.__dict__

        if name in ('typesNamespace', 'typesNamespaceURI',
            'schemaNamespace', 'schemaNamespaceURI'):

            if name[-3:] == 'URI':
                base, uri = name[:-3], 1
            else:
                base, uri = name, 0

            if type(value) == StringType:
                if NS.NSMAP.has_key(value):
                    n = (value, NS.NSMAP[value])
                elif NS.NSMAP_R.has_key(value):
                    n = (NS.NSMAP_R[value], value)
                else:
                    raise AttributeError, "unknown namespace"
            elif type(value) in (ListType, TupleType):
                if uri:
                    n = (value[1], value[0])
                else:
                    n = (value[0], value[1])
            else:
                raise AttributeError, "unknown namespace type"

            d[base], d[base + 'URI'] = n

            try:
                d['namespaceStyle'] = \
                    NS.STMAP_R[(d['typesNamespace'], d['schemaNamespace'])]
            except:
                d['namespaceStyle'] = ''

        elif name == 'namespaceStyle':
            value = str(value)

            if not NS.STMAP.has_key(value):
                raise AttributeError, "unknown namespace style"

            d[name] = value
            n = d['typesNamespace'] = NS.STMAP[value][0]
            d['typesNamespaceURI'] = NS.NSMAP[n]
            n = d['schemaNamespace'] = NS.STMAP[value][1]
            d['schemaNamespaceURI'] = NS.NSMAP[n]

        elif name == 'debug':
            d[name]                     = \
                d['returnFaultInfo']    = \
                d['dumpFaultInfo']      = \
                d['dumpHeadersIn']      = \
                d['dumpHeadersOut']     = \
                d['dumpSOAPIn']         = \
                d['dumpSOAPOut']        = value

        else:
            d[name] = value

Config = SOAPConfig()

################################################################################
# Types and Wrappers
################################################################################

class anyType:
    _validURIs = (NS.XSD, NS.XSD2, NS.XSD3, NS.ENC)

    def __init__(self, data = None, name = None, typed = 1, attrs = None):
        if self.__class__ == anyType:
            raise Error, "anyType can't be instantiated directly"

        if type(name) in (ListType, TupleType):
            self._ns, self._name = name
        else:
            self._ns, self._name = self._validURIs[0], name
        self._typed = typed
        self._attrs = {}

        self._cache = None
        self._type = self._typeName()

        self._data = self._checkValueSpace(data)

        if attrs != None:
            self._setAttrs(attrs)

    def __str__(self):
        if self._name:
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

        self._attrs[attr] = str(value)

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
        if not self._typed:
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
            raise AttributeError, "invalid %s type" % self._type

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
            raise ValueError, "invalid %s value" % self._type

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
            raise ValueError, "invalid %s value" % self._type

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

            if e[0] < 0:
                neg = '-'
                e[0] = abs(e[0])

            if not e[0]:
                e[0] = '--'
            elif e[0] < 100:
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
        self._aslist    = []
        self._asdict    = {}
        self._keyord    = []

        if type(data) == DictType:
            self.__dict__.update(data)

    def __getitem__(self, item):
        if type(item) == IntType:
            return self._aslist[item]
        return getattr(self, item)

    def __len__(self):
        return len(self._aslist)

    def __nonzero__(self):
        return 1

    def _keys(self):
        return filter(lambda x: x[0] != '_', self.__dict__.keys())

    def _addItem(self, name, value, attrs = None):
        d = self._asdict

        if d.has_key(name):
            if type(d[name]) != ListType:
                d[name] = [d[name]]
            d[name].append(value)
        else:
            d[name] = value

        self._keyord.append(name)
        self._aslist.append(value)
        self.__dict__[name] = d[name]

    def _placeItem(self, name, value, pos, subpos = 0, attrs = None):
        d = self._asdict

        if subpos == 0 and type(d[name]) != ListType:
            d[name] = value
        else:
            d[name][subpos] = value

        self._keyord[pos] = name
        self._aslist[pos] = value
        self.__dict__[name] = d[name]

    def _getItemAsList(self, name, default = []):
        try:
            d = self.__dict__[name]
        except:
            return default

        if type(d) == ListType:
            return d
        return [d]

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
                self._full = 1

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
        offset = 0, rank = None, asize = 0, elemsname = None):

        arrayType.__init__(self, data, name, attrs, offset, rank, asize,
            elemsname)

        self._type = typed

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
        return "<Fault %s: %s>" % (self.faultcode, self.faultstring)

    __str__ = __repr__

################################################################################
class RefHolder:
    def __init__(self, name, frame):
        self.name = name
        self.parent = frame
        self.pos = len(frame)
        self.subpos = frame.namecounts.get(name, 0)

    def __repr__(self):
        return "<%s %s at %d>" % (self.__class__, self.name, id(self))

################################################################################
# Utility infielders
################################################################################
def collapseWhiteSpace(s):
    return re.sub('\s+', ' ', s).strip()

def decodeHexString(data):
    conv = {'0': 0x0, '1': 0x1, '2': 0x2, '3': 0x3, '4': 0x4,
        '5': 0x5, '6': 0x6, '7': 0x7, '8': 0x8, '9': 0x9, 'a': 0xa,
        'b': 0xb, 'c': 0xc, 'd': 0xd, 'e': 0xe, 'f': 0xf, 'A': 0xa,
        'B': 0xb, 'C': 0xc, 'D': 0xd, 'E': 0xe, 'F': 0xf,}
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

class UnderflowError(exceptions.ArithmeticError):
    pass

def debugHeader(title):
    s = '*** ' + title + ' '
    print s + ('*' * (72 - len(s)))

def debugFooter(title):
    print '*' * 72
    sys.stdout.flush()

################################################################################
# SOAP Parser
################################################################################
class SOAPParser(xml.sax.handler.ContentHandler):
    class Frame:
        def __init__(self, name, kind = None, attrs = {}, rules = {}):
            self.name = name
            self.kind = kind
            self.attrs = attrs
            self.rules = rules

            self.contents = []
            self.names = []
            self.namecounts = {}
            self.subattrs = []

        def append(self, name, data, attrs):
            self.names.append(name)
            self.contents.append(data)
            self.subattrs.append(attrs)

            if self.namecounts.has_key(name):
                self.namecounts[name] += 1
            else:
                self.namecounts[name] = 1

        def _placeItem(self, name, value, pos, subpos = 0, attrs = None):
            self.contents[pos] = value

            if attrs:
                self.attrs.update(attrs)

        def __len__(self):
            return len(self.contents)

        def __repr__(self):
            return "<%s %s at %d>" % (self.__class__, self.name, id(self))

    def __init__(self, rules = None):
        xml.sax.handler.ContentHandler.__init__(self)
        self.body       = None
        self.header     = None
        self.attrs      = {}
        self._data      = None
        self._next      = "E" # Keeping state for message validity
        self._stack     = [self.Frame('SOAP')]

        # Make two dictionaries to store the prefix <-> URI mappings, and
        # initialize them with the default
        self._prem      = {NS.XML_T: NS.XML}
        self._prem_r    = {NS.XML: NS.XML_T}
        self._ids       = {}
        self._refs      = {}
        self._rules    = rules

    def startElementNS(self, name, qname, attrs):
        # Workaround two sax bugs
        if name[0] == None and name[1][0] == ' ':
            name = (None, name[1][1:])
        else:
            name = tuple(name)

        # First some checking of the layout of the message

        if self._next == "E":
            if name[1] != 'Envelope':
                raise Error, "expected `SOAP-ENV:Envelope', got `%s:%s'" % \
                    (self._prem_r[name[0]], name[1])
            if name[0] != NS.ENV:
                raise faultType, ("%s:VersionMismatch" % NS.ENV_T,
                    "Don't understand version `%s' Envelope" % name[0])
            else:
                self._next = "HorB"
        elif self._next == "HorB":
            if name[0] == NS.ENV and name[1] in ("Header", "Body"):
                self._next = None
            else:
                raise Error, \
                    "expected `SOAP-ENV:Header' or `SOAP-ENV:Body', " \
                    "got `%s'" % self._prem_r[name[0]] + ':' + name[1]
        elif self._next == "B":
            if name == (NS.ENV, "Body"):
                self._next = None
            else:
                raise Error, "expected `SOAP-ENV:Body', got `%s'" % \
                    self._prem_r[name[0]] + ':' + name[1]
        elif self._next == "":
            raise Error, "expected nothing, got `%s'" % \
                self._prem_r[name[0]] + ':' + name[1]

        if len(self._stack) == 2:
            rules = self._rules
        else:
            try:
                rules = self._stack[-1].rules[name[1]]
            except:
                rules = None

        if type(rules) not in (NoneType, DictType):
            kind = rules
        else:
            kind = attrs.get((NS.ENC, 'arrayType'))

            if kind != None:
                del attrs._attrs[(NS.ENC, 'arrayType')]

                i = kind.find(':')
                if i >= 0:
                    kind = (self._prem[kind[:i]], kind[i + 1:])
                else:
                    kind = None

        self.pushFrame(self.Frame(name[1], kind, attrs._attrs, rules))

        self._data = '' # Start accumulating

    def pushFrame(self, frame):
        self._stack.append(frame)

    def popFrame(self):
        return self._stack.pop()

    def endElementNS(self, name, qname):
        # Workaround two sax bugs
        if name[0] == None and name[1][0] == ' ':
            ns, name = None, name[1][1:]
        else:
            ns, name = tuple(name)

        if self._next == "E":
            raise Error, "didn't get SOAP-ENV:Envelope"
        if self._next in ("HorB", "B"):
            raise Error, "didn't get SOAP-ENV:Body"

        cur = self.popFrame()
        attrs = cur.attrs

        idval = None

        if attrs.has_key((None, 'id')):
            idval = attrs[(None, 'id')]

            if self._ids.has_key(idval):
                raise Error, "duplicate id `%s'" % idval

            del attrs[(None, 'id')]

        root = 1

        if len(self._stack) == 3:
            if attrs.has_key((NS.ENC, 'root')):
                root = int(attrs[(NS.ENC, 'root')])

                # Do some preliminary checks. First, if root="0" is present,
                # the element must have an id. Next, if root="n" is present,
                # n something other than 0 or 1, raise an exception.

                if root == 0:
                    if idval == None:
                        raise Error, "non-root element must have an id"
                elif root != 1:
                    raise Error, "SOAP-ENC:root must be `0' or `1'"

                del attrs[(NS.ENC, 'root')]

        while 1:
            href = attrs.get((None, 'href'))
            if href:
                if href[0] != '#':
                    raise Error, "only do local hrefs right now"
                if self._data != None and self._data.strip() != '':
                    raise Error, "hrefs can't have data"

                href = href[1:]

                if self._ids.has_key(href):
                    data = self._ids[href]
                else:
                    data = RefHolder(name, self._stack[-1])

                    if self._refs.has_key(href):
                        self._refs[href].append(data)
                    else:
                        self._refs[href] = [data]

                del attrs[(None, 'href')]

                break

            kind = None

            if attrs:
                for i in NS.XSI_L:
                    if attrs.has_key((i, 'type')):
                        kind = attrs[(i, 'type')]
                        del attrs[(i, 'type')]

                if kind != None:
                    i = kind.find(':')
                    if i >= 0:
                        kind = (self._prem[kind[:i]], kind[i + 1:])
                    else:
# XXX What to do here? (None, kind) is just going to fail in convertType
                        kind = (None, kind)

            null = 0

            if attrs:
                for i in (NS.XSI, NS.XSI2):
                    if attrs.has_key((i, 'null')):
                        null = attrs[(i, 'null')]
                        del attrs[(i, 'null')]

                if attrs.has_key((NS.XSI3, 'nil')):
                    null = attrs[(NS.XSI3, 'nil')]
                    del attrs[(NS.XSI3, 'nil')]

                #MAP 4/12/2002 - must also support "true"
                #null = int(null)
                null = (str(null).lower() in ['true', '1'])

                if null:
                    if len(cur) or \
                        (self._data != None and self._data.strip() != ''):
                        raise Error, "nils can't have data"

                    data = None

                    break

            if len(self._stack) == 2:
                if (ns, name) == (NS.ENV, "Header"):
                    self.header = data = headerType(attrs = attrs)
                    self._next = "B"
                    break
                elif (ns, name) == (NS.ENV, "Body"):
                    self.body = data = bodyType(attrs = attrs)
                    self._next = ""
                    break
            elif len(self._stack) == 3 and self._next == None:
                if (ns, name) == (NS.ENV, "Fault"):
                    data = faultType()
                    self._next = ""
                    break

            if cur.rules != None:
                rule = cur.rules

                if type(rule) in (StringType, UnicodeType):
# XXX Need a namespace here
                    rule = (None, rule)
                elif type(rule) == ListType:
                    rule = tuple(rule)

# XXX What if rule != kind?
                if callable(rule):
                    data = rule(self._data)
                elif type(rule) == DictType:
                    data = structType(name = (ns, name), attrs = attrs)
                else:
                    data = self.convertType(self._data, rule, attrs)

                break

            if (kind == None and cur.kind != None) or \
                (kind == (NS.ENC, 'Array')):
                kind = cur.kind

                if kind == None:
                    kind = 'ur-type[%d]' % len(cur)
                else:
                    kind = kind[1]

                if len(cur.namecounts) == 1:
                    elemsname = cur.names[0]
                else:
                    elemsname = None

                data = self.startArray((ns, name), kind, attrs, elemsname)

                break

            if len(self._stack) == 3 and kind == None and \
                len(cur) == 0 and \
                (self._data == None or self._data.strip() == ''):
                data = structType(name = (ns, name), attrs = attrs)
                break

            if len(cur) == 0 and ns != NS.URN:
                # Nothing's been added to the current frame so it must be a
                # simple type.

                if kind == None:
                    # If the current item's container is an array, it will
                    # have a kind. If so, get the bit before the first [,
                    # which is the type of the array, therefore the type of
                    # the current item.

                    kind = self._stack[-1].kind

                    if kind != None:
                        i = kind[1].find('[')
                        if i >= 0:
                            kind = (kind[0], kind[1][:i])
                    elif ns != None:
                        kind = (ns, name)

                if kind != None:
                    try:
                        data = self.convertType(self._data, kind, attrs)
                    except UnknownTypeError:
                        data = None
                else:
                    data = None

                if data == None:
                    data = self._data or ''

                    if len(attrs) == 0:
                        try: data = str(data)
                        except: pass

                break

            data = structType(name = (ns, name), attrs = attrs)

            break

        if isinstance(data, compoundType):
            for i in range(len(cur)):
                v = cur.contents[i]
                data._addItem(cur.names[i], v, cur.subattrs[i])

                if isinstance(v, RefHolder):
                    v.parent = data

        if root:
            self._stack[-1].append(name, data, attrs)

        if idval != None:
            self._ids[idval] = data

            if self._refs.has_key(idval):
                for i in self._refs[idval]:
                    i.parent._placeItem(i.name, data, i.pos, i.subpos, attrs)

                del self._refs[idval]

        self.attrs[id(data)] = attrs

        if isinstance(data, anyType):
            data._setAttrs(attrs)

        self._data = None       # Stop accumulating

    def endDocument(self):
        if len(self._refs) == 1:
            raise Error, \
                "unresolved reference " + self._refs.keys()[0]
        elif len(self._refs) > 1:
            raise Error, \
                "unresolved references " + ', '.join(self._refs.keys())

    def startPrefixMapping(self, prefix, uri):
        self._prem[prefix] = uri
        self._prem_r[uri] = prefix

    def endPrefixMapping(self, prefix):
        try:
            del self._prem_r[self._prem[prefix]]
            del self._prem[prefix]
        except:
            pass

    def characters(self, c):
        if self._data != None:
            self._data += c

    arrayre = '^(?:(?P<ns>[^:]*):)?' \
        '(?P<type>[^[]+)' \
        '(?:\[(?P<rank>,*)\])?' \
        '(?:\[(?P<asize>\d+(?:,\d+)*)?\])$'

    def startArray(self, name, kind, attrs, elemsname):
        if type(self.arrayre) == StringType:
            self.arrayre = re.compile (self.arrayre)

        offset = attrs.get((NS.ENC, "offset"))

        if offset != None:
            del attrs[(NS.ENC, "offset")]

            try:
                if offset[0] == '[' and offset[-1] == ']':
                    offset = int(offset[1:-1])
                    if offset < 0:
                        raise Exception
                else:
                    raise Exception
            except:
                raise AttributeError, "invalid Array offset"
        else:
            offset = 0

        try:
            m = self.arrayre.search(kind)

            if m == None:
                raise Exception

            t = m.group('type')

            if t == 'ur-type':
                return arrayType(None, name, attrs, offset, m.group('rank'),
                    m.group('asize'), elemsname)
            elif m.group('ns') != None:
                return typedArrayType(None, name,
                    (self._prem[m.group('ns')], t), attrs, offset,
                    m.group('rank'), m.group('asize'), elemsname)
            else:
                return typedArrayType(None, name, (None, t), attrs, offset,
                    m.group('rank'), m.group('asize'), elemsname)
        except:
            raise AttributeError, "invalid Array type `%s'" % kind

    # Conversion

    class DATETIMECONSTS:
        SIGNre = '(?P<sign>-?)'
        CENTURYre = '(?P<century>\d{2,})'
        YEARre = '(?P<year>\d{2})'
        MONTHre = '(?P<month>\d{2})'
        DAYre = '(?P<day>\d{2})'
        HOURre = '(?P<hour>\d{2})'
        MINUTEre = '(?P<minute>\d{2})'
        SECONDre = '(?P<second>\d{2}(?:\.\d*)?)'
        TIMEZONEre = '(?P<zulu>Z)|(?P<tzsign>[-+])(?P<tzhour>\d{2}):' \
            '(?P<tzminute>\d{2})'
        BOSre = '^\s*'
        EOSre = '\s*$'

        __allres = {'sign': SIGNre, 'century': CENTURYre, 'year': YEARre,
            'month': MONTHre, 'day': DAYre, 'hour': HOURre,
            'minute': MINUTEre, 'second': SECONDre, 'timezone': TIMEZONEre,
            'b': BOSre, 'e': EOSre}

        dateTime = '%(b)s%(sign)s%(century)s%(year)s-%(month)s-%(day)sT' \
            '%(hour)s:%(minute)s:%(second)s(%(timezone)s)?%(e)s' % __allres
        timeInstant = dateTime
        timePeriod = dateTime
        time = '%(b)s%(hour)s:%(minute)s:%(second)s(%(timezone)s)?%(e)s' % \
            __allres
        date = '%(b)s%(sign)s%(century)s%(year)s-%(month)s-%(day)s' \
            '(%(timezone)s)?%(e)s' % __allres
        century = '%(b)s%(sign)s%(century)s(%(timezone)s)?%(e)s' % __allres
        gYearMonth = '%(b)s%(sign)s%(century)s%(year)s-%(month)s' \
            '(%(timezone)s)?%(e)s' % __allres
        gYear = '%(b)s%(sign)s%(century)s%(year)s(%(timezone)s)?%(e)s' % \
            __allres
        year = gYear
        gMonthDay = '%(b)s--%(month)s-%(day)s(%(timezone)s)?%(e)s' % __allres
        recurringDate = gMonthDay
        gDay = '%(b)s---%(day)s(%(timezone)s)?%(e)s' % __allres
        recurringDay = gDay
        gMonth = '%(b)s--%(month)s--(%(timezone)s)?%(e)s' % __allres
        month = gMonth

        recurringInstant = '%(b)s%(sign)s(%(century)s|-)(%(year)s|-)-' \
            '(%(month)s|-)-(%(day)s|-)T' \
            '(%(hour)s|-):(%(minute)s|-):(%(second)s|-)' \
            '(%(timezone)s)?%(e)s' % __allres

        duration = '%(b)s%(sign)sP' \
            '((?P<year>\d+)Y)?' \
            '((?P<month>\d+)M)?' \
            '((?P<day>\d+)D)?' \
            '((?P<sep>T)' \
            '((?P<hour>\d+)H)?' \
            '((?P<minute>\d+)M)?' \
            '((?P<second>\d*(?:\.\d*)?)S)?)?%(e)s' % \
            __allres

        timeDuration = duration

        # The extra 31 on the front is:
        # - so the tuple is 1-based
        # - so months[month-1] is December's days if month is 1

        months = (31, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    def convertDateTime(self, value, kind):
        def getZoneOffset(d):
            zoffs = 0

            try:
                if d['zulu'] == None:
                    zoffs = 60 * int(d['tzhour']) + int(d['tzminute'])
                    if d['tzsign'] != '-':
                        zoffs = -zoffs
            except TypeError:
                pass

            return zoffs

        def applyZoneOffset(months, zoffs, date, minfield, posday = 1):
            if zoffs == 0 and (minfield > 4 or 0 <= date[5] < 60):
                return date

            if minfield > 5: date[5] = 0
            if minfield > 4: date[4] = 0

            if date[5] < 0:
                date[4] += int(date[5]) / 60
                date[5] %= 60

            date[4] += zoffs

            if minfield > 3 or 0 <= date[4] < 60: return date

            date[3] += date[4] / 60
            date[4] %= 60

            if minfield > 2 or 0 <= date[3] < 24: return date

            date[2] += date[3] / 24
            date[3] %= 24

            if minfield > 1:
                if posday and date[2] <= 0:
                    date[2] += 31       # zoffs is at most 99:59, so the
                                        # day will never be less than -3
                return date

            while 1:
                # The date[1] == 3 (instead of == 2) is because we're
                # going back a month, so we need to know if the previous
                # month is February, so we test if this month is March.

                leap = minfield == 0 and date[1] == 3 and \
                    date[0] % 4 == 0 and \
                    (date[0] % 100 != 0 or date[0] % 400 == 0)

                if 0 < date[2] <= months[date[1]] + leap: break

                date[2] += months[date[1] - 1] + leap

                date[1] -= 1

                if date[1] > 0: break

                date[1] = 12

                if minfield > 0: break

                date[0] -= 1

            return date

        try:
            exp = getattr(self.DATETIMECONSTS, kind)
        except AttributeError:
            return None

        if type(exp) == StringType:
            exp = re.compile(exp)
            setattr (self.DATETIMECONSTS, kind, exp)

        m = exp.search(value)

        try:
            if m == None:
                raise Exception

            d = m.groupdict()
            f = ('century', 'year', 'month', 'day',
                'hour', 'minute', 'second')
            fn = len(f)         # Index of first non-None value
            r = []

            if kind in ('duration', 'timeDuration'):
                if d['sep'] != None and d['hour'] == None and \
                    d['minute'] == None and d['second'] == None:
                    raise Exception

                f = f[1:]

                for i in range(len(f)):
                    s = d[f[i]]

                    if s != None:
                        if f[i] == 'second':
                            s = float(s)
                        else:
                            try: s = int(s)
                            except ValueError: s = long(s)

                        if i < fn: fn = i

                    r.append(s)

                if fn > len(r):         # Any non-Nones?
                    raise Exception

                if d['sign'] == '-':
                    r[fn] = -r[fn]

                return tuple(r)

            if kind == 'recurringInstant':
                for i in range(len(f)):
                    s = d[f[i]]

                    if s == None or s == '-':
                        if i > fn:
                            raise Exception
                        s = None
                    else:
                        if i < fn:
                            fn = i

                        if f[i] == 'second':
                            s = float(s)
                        else:
                            try:
                                s = int(s)
                            except ValueError:
                                s = long(s)

                    r.append(s)

                s = r.pop(0)

                if fn == 0:
                    r[0] += s * 100
                else:
                    fn -= 1

                if fn < len(r) and d['sign'] == '-':
                    r[fn] = -r[fn]

                cleanDate(r, fn)

                return tuple(applyZoneOffset(self.DATETIMECONSTS.months,
                    getZoneOffset(d), r, fn, 0))

            r = [0, 0, 1, 1, 0, 0, 0]

            for i in range(len(f)):
                field = f[i]

                s = d.get(field)

                if s != None:
                    if field == 'second':
                        s = float(s)
                    else:
                        try:
                            s = int(s)
                        except ValueError:
                            s = long(s)

                    if i < fn:
                        fn = i

                    r[i] = s

            if fn > len(r):     # Any non-Nones?
                raise Exception

            s = r.pop(0)

            if fn == 0:
                r[0] += s * 100
            else:
                fn -= 1

            if d.get('sign') == '-':
                r[fn] = -r[fn]

            cleanDate(r, fn)

            zoffs = getZoneOffset(d)

            if zoffs:
                r = applyZoneOffset(self.DATETIMECONSTS.months, zoffs, r, fn)

            if kind == 'century':
                return r[0] / 100

            s = []

            for i in range(1, len(f)):
                if d.has_key(f[i]):
                    s.append(r[i - 1])

            if len(s) == 1:
                return s[0]
            return tuple(s)
        except Exception, e:
            raise Error, "invalid %s value `%s' - %s" % (kind, value, e)

    intlimits = \
    {
        'nonPositiveInteger':   (0, None, 0),
        'non-positive-integer': (0, None, 0),
        'negativeInteger':      (0, None, -1),
        'negative-integer':     (0, None, -1),
        'long':                 (1, -9223372036854775808L,
                                    9223372036854775807L),
        'int':                  (0, -2147483648L, 2147483647),
        'short':                (0, -32768, 32767),
        'byte':                 (0, -128, 127),
        'nonNegativeInteger':   (0, 0, None),
        'non-negative-integer': (0, 0, None),
        'positiveInteger':      (0, 1, None),
        'positive-integer':     (0, 1, None),
        'unsignedLong':         (1, 0, 18446744073709551615L),
        'unsignedInt':          (0, 0, 4294967295L),
        'unsignedShort':        (0, 0, 65535),
        'unsignedByte':         (0, 0, 255),
    }
    floatlimits = \
    {
        'float':        (7.0064923216240861E-46, -3.4028234663852886E+38,
                         3.4028234663852886E+38),
        'double':       (2.4703282292062327E-324, -1.7976931348623158E+308,
                         1.7976931348623157E+308),
    }
    zerofloatre = '[1-9]'

    def convertType(self, d, t, attrs):
        dnn = d or ''

        if t[0] in NS.EXSD_L:
            if t[1] == "integer":
                try:
                    d = int(d)
                    if len(attrs):
                        d = long(d)
                except:
                    d = long(d)
                return d
            if self.intlimits.has_key (t[1]):
                l = self.intlimits[t[1]]
                try: d = int(d)
                except: d = long(d)

                if l[1] != None and d < l[1]:
                    raise UnderflowError, "%s too small" % d
                if l[2] != None and d > l[2]:
                    raise OverflowError, "%s too large" % d

                if l[0] or len(attrs):
                    return long(d)
                return d
            if t[1] == "string":
                if len(attrs):
                    return unicode(dnn)
                try:
                    return str(dnn)
                except:
                    return dnn
            if t[1] == "boolean":
                d = d.strip().lower()
                if d in ('0', 'false'):
                    return 0
                if d in ('1', 'true'):
                    return 1
                raise AttributeError, "invalid boolean value"
            if self.floatlimits.has_key (t[1]):
                l = self.floatlimits[t[1]]
                s = d.strip().lower()
                try:
                    d = float(s)
                except:
                    # Some platforms don't implement the float stuff. This
                    # is close, but NaN won't be > "INF" as required by the
                    # standard.

                    if s in ("nan", "inf"):
                        return 1e300**2
                    if s == "-inf":
                        return -1e300**2

                    raise

                if str (d) == 'nan':
                    if s != 'nan':
                        raise ValueError, "invalid %s" % t[1]
                elif str (d) == '-inf':
                    if s != '-inf':
                        raise UnderflowError, "%s too small" % t[1]
                elif str (d) == 'inf':
                    if s != 'inf':
                        raise OverflowError, "%s too large" % t[1]
                elif d < 0:
                    if d < l[1]:
                        raise UnderflowError, "%s too small" % t[1]
                elif d > 0:
                    if d < l[0] or d > l[2]:
                        raise OverflowError, "%s too large" % t[1]
                elif d == 0:
                    if type(self.zerofloatre) == StringType:
                        self.zerofloatre = re.compile(self.zerofloatre)

                    if self.zerofloatre.search(s):
                        raise UnderflowError, "invalid %s" % t[1]

                return d
            if t[1] in ("dateTime", "date", "timeInstant", "time"):
                return self.convertDateTime(d, t[1])
            if t[1] == "decimal":
                return float(d)
            if t[1] in ("language", "QName", "NOTATION", "NMTOKEN", "Name",
                "NCName", "ID", "IDREF", "ENTITY"):
                return collapseWhiteSpace(d)
            if t[1] in ("IDREFS", "ENTITIES", "NMTOKENS"):
                d = collapseWhiteSpace(d)
                return d.split()
        if t[0] in NS.XSD_L:
            if t[1] in ("base64", "base64Binary"):
                return base64.decodestring(d)
            if t[1] == "hexBinary":
                return decodeHexString(d)
            if t[1] == "anyURI":
                return urllib.unquote(collapseWhiteSpace(d))
            if t[1] in ("normalizedString", "token"):
                return collapseWhiteSpace(d)
        if t[0] == NS.ENC:
            if t[1] == "base64":
                return base64.decodestring(d)
        if t[0] == NS.XSD:
            if t[1] == "binary":
                try:
                    e = attrs[(None, 'encoding')]

                    if e == 'hex':
                        return decodeHexString(d)
                    elif e == 'base64':
                        return base64.decodestring(d)
                except:
                    pass

                raise Error, "unknown or missing binary encoding"
            if t[1] == "uri":
                return urllib.unquote(collapseWhiteSpace(d))
            if t[1] == "recurringInstant":
                return self.convertDateTime(d, t[1])
        if t[0] in (NS.XSD2, NS.ENC):
            if t[1] == "uriReference":
                return urllib.unquote(collapseWhiteSpace(d))
            if t[1] == "timePeriod":
                return self.convertDateTime(d, t[1])
            if t[1] in ("century", "year"):
                return self.convertDateTime(d, t[1])
        if t[0] in (NS.XSD, NS.XSD2, NS.ENC):
            if t[1] == "timeDuration":
                return self.convertDateTime(d, t[1])
        if t[0] == NS.XSD3:
            if t[1] == "anyURI":
                return urllib.unquote(collapseWhiteSpace(d))
            if t[1] in ("gYearMonth", "gMonthDay"):
                return self.convertDateTime(d, t[1])
            if t[1] == "gYear":
                return self.convertDateTime(d, t[1])
            if t[1] == "gMonth":
                return self.convertDateTime(d, t[1])
            if t[1] == "gDay":
                return self.convertDateTime(d, t[1])
            if t[1] == "duration":
                return self.convertDateTime(d, t[1])
        if t[0] in (NS.XSD2, NS.XSD3):
            if t[1] == "token":
                return collapseWhiteSpace(d)
            if t[1] == "recurringDate":
                return self.convertDateTime(d, t[1])
            if t[1] == "month":
                return self.convertDateTime(d, t[1])
            if t[1] == "recurringDay":
                return self.convertDateTime(d, t[1])
        if t[0] == NS.XSD2:
            if t[1] == "CDATA":
                return collapseWhiteSpace(d)

        raise UnknownTypeError, "unknown type `%s'" % (t[0] + ':' + t[1])

################################################################################
# call to SOAPParser that keeps all of the info
################################################################################
def _parseSOAP(xml_str, rules = None):
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    parser = xml.sax.make_parser()
    t = SOAPParser(rules = rules)
    parser.setContentHandler(t)
    e = xml.sax.handler.ErrorHandler()
    parser.setErrorHandler(e)

    inpsrc = xml.sax.xmlreader.InputSource()
    inpsrc.setByteStream(StringIO(xml_str))

    # turn on namespace mangeling
    parser.setFeature(xml.sax.handler.feature_namespaces,1)

    parser.parse(inpsrc)

    return t

################################################################################
# SOAPParser's more public interface
################################################################################
def parseSOAP(xml_str, attrs = 0):
    t = _parseSOAP(xml_str)

    if attrs:
        return t.body, t.attrs
    return t.body


def parseSOAPRPC(xml_str, header = 0, body = 0, attrs = 0, rules = None):
    t = _parseSOAP(xml_str, rules = rules)
    p = t.body._aslist[0]

    # Empty string, for RPC this translates into a void
    if type(p) in (type(''), type(u'')) and p in ('', u''):
        name = "Response"
        for k in t.body.__dict__.keys():
            if k[0] != "_":
                name = k
        p = structType(name)

    if header or body or attrs:
        ret = (p,)
        if header : ret += (t.header,)
        if body: ret += (t.body,)
        if attrs: ret += (t.attrs,)
        return ret
    else:
        return p


################################################################################
# SOAP Builder
################################################################################
class SOAPBuilder:
    _xml_top = '<?xml version="1.0"?>\n'
    _xml_enc_top = '<?xml version="1.0" encoding="%s"?>\n'
    _env_top = '%(ENV_T)s:Envelope %(ENV_T)s:encodingStyle="%(ENC)s"' % \
        NS.__dict__
    _env_bot = '</%(ENV_T)s:Envelope>\n' % NS.__dict__

    # Namespaces potentially defined in the Envelope tag.

    _env_ns = {NS.ENC: NS.ENC_T, NS.ENV: NS.ENV_T,
        NS.XSD: NS.XSD_T, NS.XSD2: NS.XSD2_T, NS.XSD3: NS.XSD3_T,
        NS.XSI: NS.XSI_T, NS.XSI2: NS.XSI2_T, NS.XSI3: NS.XSI3_T}

    def __init__(self, args = (), kw = {}, method = None, namespace = None,
        header = None, methodattrs = None, envelope = 1, encoding = 'UTF-8',
        use_refs = 0, config = Config):

        # Test the encoding, raising an exception if it's not known
        if encoding != None:
            ''.encode(encoding)

        self.args       = args
        self.kw         = kw
        self.envelope   = envelope
        self.encoding   = encoding
        self.method     = method
        self.namespace  = namespace
        self.header     = header
        self.methodattrs= methodattrs
        self.use_refs   = use_refs
        self.config     = config
        self.out        = ''
        self.tcounter   = 0
        self.ncounter   = 1
        self.icounter   = 1
        self.envns      = {}
        self.ids        = {}
        self.depth      = 0
        self.multirefs  = []
        self.multis     = 0
        self.body       = not isinstance(args, bodyType)

    def build(self):
        ns_map = {}

        # Cache whether typing is on or not
        typed = self.config.typed

        if self.header:
            # Create a header.
            self.dump(self.header, "Header", typed = typed)
            self.header = None # Wipe it out so no one is using it.
        if self.body:
            # Call genns to record that we've used SOAP-ENV.
            self.depth += 1
            body_ns = self.genns(ns_map, NS.ENV)[0]
            self.out += "<%sBody>\n" % body_ns

        if self.method:
            self.depth += 1
            a = ''
            if self.methodattrs:
                for (k, v) in self.methodattrs.items():
                    a += ' %s="%s"' % (k, v)

            if self.namespace:  # Use the namespace info handed to us
                methodns, n = self.genns(ns_map, self.namespace)
            else:
                methodns, n = '', ''

            self.out += '<%s%s%s%s%s>\n' % \
                (methodns, self.method, n, a, self.genroot(ns_map))

        try:
            if type(self.args) != TupleType:
                args = (self.args,)
            else:
                args = self.args

            for i in args:
                self.dump(i, typed = typed, ns_map = ns_map)

            for (k, v) in self.kw.items():
                self.dump(v, k, typed = typed, ns_map = ns_map)
        except RecursionError:
            if self.use_refs == 0:
                # restart
                b = SOAPBuilder(args = self.args, kw = self.kw,
                    method = self.method, namespace = self.namespace,
                    header = self.header, methodattrs = self.methodattrs,
                    envelope = self.envelope, encoding = self.encoding,
                    use_refs = 1, config = self.config)
                return b.build()
            raise

        if self.method:
            self.out += "</%s%s>\n" % (methodns, self.method)
            self.depth -= 1

        if self.body:
            # dump may add to self.multirefs, but the for loop will keep
            # going until it has used all of self.multirefs, even those
            # entries added while in the loop.

            self.multis = 1

            for obj, tag in self.multirefs:
                self.dump(obj, tag, typed = typed, ns_map = ns_map)

            self.out += "</%sBody>\n" % body_ns
            self.depth -= 1

        if self.envelope:
            e = map (lambda ns: 'xmlns:%s="%s"' % (ns[1], ns[0]),
                self.envns.items())

            self.out = '<' + self._env_top + ' '.join([''] + e) + '>\n' + \
                self.out + \
                self._env_bot

        if self.encoding != None:
            self.out = self._xml_enc_top % self.encoding + self.out

            return self.out.encode(self.encoding)

        return self._xml_top + self.out

    def gentag(self):
        self.tcounter += 1
        return "v%d" % self.tcounter

    def genns(self, ns_map, nsURI):
        if nsURI == None:
            return ('', '')

        if type(nsURI) == TupleType: # already a tuple
            if len(nsURI) == 2:
                ns, nsURI = nsURI
            else:
                ns, nsURI = None, nsURI[0]
        else:
            ns = None

        if ns_map.has_key(nsURI):
            return (ns_map[nsURI] + ':', '')

        if self._env_ns.has_key(nsURI):
            ns = self.envns[nsURI] = ns_map[nsURI] = self._env_ns[nsURI]
            return (ns + ':', '')

        if not ns:
            ns = "ns%d" % self.ncounter
            self.ncounter += 1
        ns_map[nsURI] = ns
        if self.config.buildWithNamespacePrefix:
            return (ns + ':', ' xmlns:%s="%s"' % (ns, nsURI))
        else:
            return ('', ' xmlns="%s"' % (nsURI))

    def genroot(self, ns_map):
        if self.depth != 2:
            return ''

        ns, n = self.genns(ns_map, NS.ENC)
        return ' %sroot="%d"%s' % (ns, not self.multis, n)

    # checkref checks an element to see if it needs to be encoded as a
    # multi-reference element or not. If it returns None, the element has
    # been handled and the caller can continue with subsequent elements.
    # If it returns a string, the string should be included in the opening
    # tag of the marshaled element.

    def checkref(self, obj, tag, ns_map):
        if self.depth < 2:
            return ''

        if not self.ids.has_key(id(obj)):
            n = self.ids[id(obj)] = self.icounter
            self.icounter = n + 1

            if self.use_refs == 0:
                return ''

            if self.depth == 2:
                return ' id="i%d"' % n

            self.multirefs.append((obj, tag))
        else:
            if self.use_refs == 0:
                raise RecursionError, "Cannot serialize recursive object"

            n = self.ids[id(obj)]

            if self.multis and self.depth == 2:
                return ' id="i%d"' % n

        self.out += '<%s href="#i%d"%s/>\n' % (tag, n, self.genroot(ns_map))
        return None

    # dumpers

    def dump(self, obj, tag = None, typed = 1, ns_map = {}):
        ns_map = ns_map.copy()
        self.depth += 1

        if type(tag) not in (NoneType, StringType, UnicodeType):
            raise KeyError, "tag must be a string or None"

        try:
            meth = getattr(self, "dump_" + type(obj).__name__)
            meth(obj, tag, typed, ns_map)
        except AttributeError:
            if type(obj) == LongType:
                obj_type = "integer"
            else:
                obj_type = type(obj).__name__

            self.out += self.dumper(None, obj_type, obj, tag, typed,
                ns_map, self.genroot(ns_map))

        self.depth -= 1

    # generic dumper
    def dumper(self, nsURI, obj_type, obj, tag, typed = 1, ns_map = {},
        rootattr = '', id = '',
        xml = '<%(tag)s%(type)s%(id)s%(attrs)s%(root)s>%(data)s</%(tag)s>\n'):

        if nsURI == None:
            nsURI = self.config.typesNamespaceURI

        tag = tag or self.gentag()

        a = n = t = ''
        if typed and obj_type:
            ns, n = self.genns(ns_map, nsURI)
            ins = self.genns(ns_map, self.config.schemaNamespaceURI)[0]
            t = ' %stype="%s%s"%s' % (ins, ns, obj_type, n)

        try: a = obj._marshalAttrs(ns_map, self)
        except: pass

        try: data = obj._marshalData()
        except: data = obj

        return xml % {"tag": tag, "type": t, "data": data, "root": rootattr,
            "id": id, "attrs": a}

    def dump_float(self, obj, tag, typed = 1, ns_map = {}):
        # Terrible windows hack
        if not good_float:
            if obj == float(1e300**2):
                obj = "INF"
            elif obj == float(-1e300**2):
                obj = "-INF"

        obj = str(obj)
        if obj in ('inf', '-inf'):
            obj = str(obj).upper()
        elif obj == 'nan':
            obj = 'NaN'
        self.out += self.dumper(None, "float", obj, tag, typed, ns_map,
            self.genroot(ns_map))

    def dump_string(self, obj, tag, typed = 0, ns_map = {}):
        tag = tag or self.gentag()

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        try: data = obj._marshalData()
        except: data = obj

        self.out += self.dumper(None, "string", cgi.escape(data), tag,
            typed, ns_map, self.genroot(ns_map), id)

    dump_unicode = dump_string
    dump_str = dump_string # 4/12/2002 - MAP - for Python 2.2

    def dump_None(self, obj, tag, typed = 0, ns_map = {}):
        tag = tag or self.gentag()
        ns = self.genns(ns_map, self.config.schemaNamespaceURI)[0]

        self.out += '<%s %snull="1"%s/>\n' % (tag, ns, self.genroot(ns_map))

    def dump_list(self, obj, tag, typed = 1, ns_map = {}):
        if type(obj) == InstanceType:
            data = obj.data
        else:
            data = obj

        tag = tag or self.gentag()

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        try:
            sample = data[0]
            empty = 0
        except:
            sample = structType()
            empty = 1

        # First scan list to see if all are the same type
        same_type = 1

        if not empty:
            for i in data[1:]:
                if type(sample) != type(i) or \
                    (type(sample) == InstanceType and \
                        sample.__class__ != i.__class__):
                    same_type = 0
                    break

        ndecl = ''
        if same_type:
            if (isinstance(sample, structType)) or \
                type(sample) == DictType: # force to urn struct

                try:
                    tns = obj._ns or NS.URN
                except:
                    tns = NS.URN

                ns, ndecl = self.genns(ns_map, tns)

                try:
                    typename = last._typename
                except:
                    typename = "SOAPStruct"

                t = ns + typename

            elif isinstance(sample, anyType):
                ns = sample._validNamespaceURI(self.config.typesNamespaceURI,
                    self.config.strictNamespaces)
                if ns:
                    ns, ndecl = self.genns(ns_map, ns)
                    t = ns + sample._type
                else:
                    t = 'ur-type'
            else:
                t = self.genns(ns_map, self.config.typesNamespaceURI)[0] + \
                    type(sample).__name__
        else:
            t = self.genns(ns_map, self.config.typesNamespaceURI)[0] + \
                "ur-type"

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        ens, edecl = self.genns(ns_map, NS.ENC)
        ins, idecl = self.genns(ns_map, self.config.schemaNamespaceURI)

        self.out += \
            '<%s %sarrayType="%s[%d]" %stype="%sArray"%s%s%s%s%s%s>\n' %\
            (tag, ens, t, len(data), ins, ens, ndecl, edecl, idecl,
                self.genroot(ns_map), id, a)

        typed = not same_type

        try: elemsname = obj._elemsname
        except: elemsname = "item"

        for i in data:
            self.dump(i, elemsname, typed, ns_map)

        self.out += '</%s>\n' % tag

    dump_tuple = dump_list

    def dump_dictionary(self, obj, tag, typed = 1, ns_map = {}):
        tag = tag or self.gentag()

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        self.out += '<%s%s%s%s>\n' % \
            (tag, id, a, self.genroot(ns_map))

        for (k, v) in obj.items():
            if k[0] != "_":
                self.dump(v, k, 1, ns_map)

        self.out += '</%s>\n' % tag
    dump_dict = dump_dictionary # 4/18/2002 - MAP - for Python 2.2
    
    def dump_instance(self, obj, tag, typed = 1, ns_map = {}):
        if not tag:
            # If it has a name use it.
            if isinstance(obj, anyType) and obj._name:
                tag = obj._name
            else:
                tag = self.gentag()

        if isinstance(obj, arrayType):      # Array
            self.dump_list(obj, tag, typed, ns_map)
            return

        if isinstance(obj, faultType):    # Fault
            cns, cdecl = self.genns(ns_map, NS.ENC)
            vns, vdecl = self.genns(ns_map, NS.ENV)
            self.out += '''<%sFault %sroot="1"%s%s>
<faultcode>%s</faultcode>
<faultstring>%s</faultstring>
''' % (vns, cns, vdecl, cdecl, obj.faultcode, obj.faultstring)
            if hasattr(obj, "detail"):
                self.dump(obj.detail, "detail", typed, ns_map)
            self.out += "</%sFault>\n" % vns
            return

        r = self.genroot(ns_map)

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        if isinstance(obj, voidType):     # void
            self.out += "<%s%s%s></%s>\n" % (tag, a, r, tag)
            return

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        if isinstance(obj, structType):
            # Check for namespace
            ndecl = ''
            ns = obj._validNamespaceURI(self.config.typesNamespaceURI,
                self.config.strictNamespaces)
            if ns:
                ns, ndecl = self.genns(ns_map, ns)
                tag = ns + tag
            self.out += "<%s%s%s%s%s>\n" % (tag, ndecl, id, a, r)

            # If we have order use it.
            order = 1

            for i in obj._keys():
                if i not in obj._keyord:
                    order = 0
                    break
            if order:
                for i in range(len(obj._keyord)):
                    self.dump(obj._aslist[i], obj._keyord[i], 1, ns_map)
            else:
                # don't have pristine order information, just build it.
                for (k, v) in obj.__dict__.items():
                    if k[0] != "_":
                        self.dump(v, k, 1, ns_map)

            if isinstance(obj, bodyType):
                self.multis = 1

                for v, k in self.multirefs:
                    self.dump(v, k, typed = typed, ns_map = ns_map)

            self.out += '</%s>\n' % tag

        elif isinstance(obj, anyType):
            t = ''

            if typed:
                ns = obj._validNamespaceURI(self.config.typesNamespaceURI,
                    self.config.strictNamespaces)
                if ns:
                    ons, ondecl = self.genns(ns_map, ns)
                    ins, indecl = self.genns(ns_map,
                        self.config.schemaNamespaceURI)
                    t = ' %stype="%s%s"%s%s' % \
                        (ins, ons, obj._type, ondecl, indecl)

            self.out += '<%s%s%s%s%s>%s</%s>\n' % \
                (tag, t, id, a, r, obj._marshalData(), tag)

        else:                           # Some Class
            self.out += '<%s%s%s>\n' % (tag, id, r)

            for (k, v) in obj.__dict__.items():
                if k[0] != "_":
                    self.dump(v, k, 1, ns_map)

            self.out += '</%s>\n' % tag


################################################################################
# SOAPBuilder's more public interface
################################################################################
def buildSOAP(args=(), kw={}, method=None, namespace=None, header=None,
              methodattrs=None,envelope=1,encoding='UTF-8',config=Config):
    t = SOAPBuilder(args=args,kw=kw, method=method, namespace=namespace,
        header=header, methodattrs=methodattrs,envelope=envelope,
        encoding=encoding, config=config)
    return t.build()

################################################################################
# RPC
################################################################################

def SOAPUserAgent():
    return "SOAP.py " + __version__ + " (actzero.com)"

################################################################################
# Client
################################################################################
class SOAPAddress:
    def __init__(self, url, config = Config):
        proto, uri = urllib.splittype(url)

        # apply some defaults
        if uri[0:2] != '//':
            if proto != None:
                uri = proto + ':' + uri

            uri = '//' + uri
            proto = 'http'

        host, path = urllib.splithost(uri)

        try:
            int(host)
            host = 'localhost:' + host
        except:
            pass

        if not path:
            path = '/'

        if proto not in ('http', 'https'):
            raise IOError, "unsupported SOAP protocol"
        if proto == 'https' and not config.SSLclient:
            raise AttributeError, \
                "SSL client not supported by this Python installation"

        self.proto = proto
        self.host = host
        self.path = path

    def __str__(self):
        return "%(proto)s://%(host)s%(path)s" % self.__dict__

    __repr__ = __str__


class HTTPTransport:
    # Need a Timeout someday?
    def call(self, addr, data, soapaction = '', encoding = None,
        http_proxy = None, config = Config):

        import httplib

        if not isinstance(addr, SOAPAddress):
            addr = SOAPAddress(addr, config)

        # Build a request
        if http_proxy:
            real_addr = http_proxy
            real_path = addr.proto + "://" + addr.host + addr.path
        else:
            real_addr = addr.host
            real_path = addr.path
            
        if addr.proto == 'https':
            r = httplib.HTTPS(real_addr)
        else:
            r = httplib.HTTP(real_addr)

        r.putrequest("POST", real_path)

        r.putheader("Host", addr.host)
        r.putheader("User-agent", SOAPUserAgent())
        t = 'text/xml';
        if encoding != None:
            t += '; charset="%s"' % encoding
        r.putheader("Content-type", t)
        r.putheader("Content-length", str(len(data)))
        r.putheader("SOAPAction", '"%s"' % soapaction)

        if config.dumpHeadersOut:
            s = 'Outgoing HTTP headers'
            debugHeader(s)
            print "POST %s %s" % (real_path, r._http_vsn_str)
            print "Host:", addr.host
            print "User-agent: SOAP.py " + __version__ + " (actzero.com)"
            print "Content-type:", t
            print "Content-length:", len(data)
            print 'SOAPAction: "%s"' % soapaction
            debugFooter(s)

        r.endheaders()

        if config.dumpSOAPOut:
            s = 'Outgoing SOAP'
            debugHeader(s)
            print data,
            if data[-1] != '\n':
                print
            debugFooter(s)

        # send the payload
        r.send(data)

        # read response line
        code, msg, headers = r.getreply()

        if config.dumpHeadersIn:
            s = 'Incoming HTTP headers'
            debugHeader(s)
            if headers.headers:
                print "HTTP/1.? %d %s" % (code, msg)
                print "\n".join(map (lambda x: x.strip(), headers.headers))
            else:
                print "HTTP/0.9 %d %s" % (code, msg)
            debugFooter(s)

        if config.dumpSOAPIn:
            data = r.getfile().read()

            s = 'Incoming SOAP'
            debugHeader(s)
            print data,
            if data[-1] != '\n':
                print
            debugFooter(s)

        if code not in (200, 500):
            raise HTTPError(code, msg)

        if not config.dumpSOAPIn:
            data = r.getfile().read()

        # return response payload
        return data

################################################################################
# SOAP Proxy
################################################################################
class SOAPProxy:
    def __init__(self, proxy, namespace = None, soapaction = '',
                 header = None, methodattrs = None, transport = HTTPTransport,
                 encoding = 'UTF-8', throw_faults = 1, unwrap_results = 1,
                 http_proxy=None, config = Config):

        # Test the encoding, raising an exception if it's not known
        if encoding != None:
            ''.encode(encoding)

        self.proxy          = SOAPAddress(proxy, config)
        self.namespace      = namespace
        self.soapaction     = soapaction
        self.header         = header
        self.methodattrs    = methodattrs
        self.transport      = transport()
        self.encoding       = encoding
        self.throw_faults   = throw_faults
        self.unwrap_results = unwrap_results
        self.http_proxy     = http_proxy
        self.config         = config
        

    def __call(self, name, args, kw, ns = None, sa = None, hd = None,
        ma = None):

        ns = ns or self.namespace
        ma = ma or self.methodattrs

        if sa: # Get soapaction
            if type(sa) == TupleType: sa = sa[0]
        else:
            sa = self.soapaction

        if hd: # Get header
            if type(hd) == TupleType:
                hd = hd[0]
        else:
            hd = self.header

        hd = hd or self.header

        if ma: # Get methodattrs
            if type(ma) == TupleType: ma = ma[0]
        else:
            ma = self.methodattrs
        ma = ma or self.methodattrs

        m = buildSOAP(args = args, kw = kw, method = name, namespace = ns,
            header = hd, methodattrs = ma, encoding = self.encoding,
            config = self.config)
        #print m

        r = self.transport.call(self.proxy, m, sa, encoding = self.encoding,
                                http_proxy = self.http_proxy,
                                config = self.config)

        #print r
        p, attrs = parseSOAPRPC(r, attrs = 1)

        try:
            throw_struct = self.throw_faults and \
                isinstance (p, faultType)
        except:
            throw_struct = 0

        if throw_struct:
            raise p

        # Bubble a regular result up, if there is only element in the
        # struct, assume that is the result and return it.
        # Otherwise it will return the struct with all the elements
        # as attributes.
        if self.unwrap_results:
            try:
                count = 0
                for i in p.__dict__.keys():
                    if i[0] != "_":  # don't move the private stuff
                        count += 1
                        t = getattr(p, i)
                if count == 1: p = t # Only one piece of data, bubble it up
            except:
                pass

        if self.config.returnAllAttrs:
            return p, attrs
        return p

    def _callWithBody(self, body):
        return self.__call(None, body, {})

    def __getattr__(self, name):  # hook to catch method calls
        return self.__Method(self.__call, name, config = self.config)

    # To handle attribute wierdness
    class __Method:
        # Some magic to bind a SOAP method to an RPC server.
        # Supports "nested" methods (e.g. examples.getStateName) -- concept
        # borrowed from xmlrpc/soaplib -- www.pythonware.com
        # Altered (improved?) to let you inline namespaces on a per call
        # basis ala SOAP::LITE -- www.soaplite.com

        def __init__(self, call, name, ns = None, sa = None, hd = None,
            ma = None, config = Config):

            self.__call 	= call
            self.__name 	= name
            self.__ns   	= ns
            self.__sa   	= sa
            self.__hd   	= hd
            self.__ma           = ma
            self.__config       = config
            if self.__name[0] == "_":
                if self.__name in ["__repr__","__str__"]:
                    self.__call__ = self.__repr__
                else:
                    self.__call__ = self.__f_call
            else:
                self.__call__ = self.__r_call

        def __getattr__(self, name):
            if self.__name[0] == "_":
                # Don't nest method if it is a directive
                return self.__class__(self.__call, name, self.__ns,
                    self.__sa, self.__hd, self.__ma)

            return self.__class__(self.__call, "%s.%s" % (self.__name, name),
                self.__ns, self.__sa, self.__hd, self.__ma)

        def __f_call(self, *args, **kw):
            if self.__name == "_ns": self.__ns = args
            elif self.__name == "_sa": self.__sa = args
            elif self.__name == "_hd": self.__hd = args
            elif self.__name == "_ma": self.__ma = args
            return self

        def __r_call(self, *args, **kw):
            return self.__call(self.__name, args, kw, self.__ns, self.__sa,
                self.__hd, self.__ma)

        def __repr__(self):
            return "<%s at %d>" % (self.__class__, id(self))

################################################################################
# Server
################################################################################

# Method Signature class for adding extra info to registered funcs, right now
# used just to indicate it should be called with keywords, instead of ordered
# params.
class MethodSig:
    def __init__(self, func, keywords=0, context=0):
        self.func     = func
        self.keywords = keywords
        self.context  = context
        self.__name__ = func.__name__

    def __call__(self, *args, **kw):
        return apply(self.func,args,kw)

class SOAPContext:
    def __init__(self, header, body, attrs, xmldata, connection, httpheaders,
        soapaction):

        self.header     = header
        self.body       = body
        self.attrs      = attrs
        self.xmldata    = xmldata
        self.connection = connection
        self.httpheaders= httpheaders
        self.soapaction = soapaction

# A class to describe how header messages are handled
class HeaderHandler:
    # Initially fail out if there are any problems.
    def __init__(self, header, attrs):
        for i in header.__dict__.keys():
            if i[0] == "_":
                continue

            d = getattr(header, i)

            try:
                fault = int(attrs[id(d)][(NS.ENV, 'mustUnderstand')])
            except:
                fault = 0

            if fault:
                raise faultType, ("%s:MustUnderstand" % NS.ENV_T,
                    "Don't understand `%s' header element but "
                    "mustUnderstand attribute is set." % i)


################################################################################
# SOAP Server
################################################################################
class SOAPServer(SocketServer.TCPServer):
    import BaseHTTPServer

    class SOAPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def version_string(self):
            return '<a href="http://www.actzero.com/solution.html">' + \
                'SOAP.py ' + __version__ + '</a> (Python ' + \
                sys.version.split()[0] + ')'

        def date_time_string(self):
            self.__last_date_time_string = \
                SOAPServer.BaseHTTPServer.BaseHTTPRequestHandler.\
                date_time_string(self)

            return self.__last_date_time_string

        def do_POST(self):
            try:
                if self.server.config.dumpHeadersIn:
                    s = 'Incoming HTTP headers'
                    debugHeader(s)
                    print self.raw_requestline.strip()
                    print "\n".join(map (lambda x: x.strip(),
                        self.headers.headers))
                    debugFooter(s)

                data = self.rfile.read(int(self.headers["content-length"]))

                if self.server.config.dumpSOAPIn:
                    s = 'Incoming SOAP'
                    debugHeader(s)
                    print data,
                    if data[-1] != '\n':
                        print
                    debugFooter(s)

                (r, header, body, attrs) = \
                    parseSOAPRPC(data, header = 1, body = 1, attrs = 1)

                method = r._name
                args   = r._aslist
                kw     = r._asdict

                ns = r._ns
                resp = ""
                # For fault messages
                if ns:
                    nsmethod = "%s:%s" % (ns, method)
                else:
                    nsmethod = method

                try:
                    # First look for registered functions
                    if self.server.funcmap.has_key(ns) and \
                        self.server.funcmap[ns].has_key(method):
                        f = self.server.funcmap[ns][method]
                    else: # Now look at registered objects
                        # Check for nested attributes. This works even if
                        # there are none, because the split will return
                        # [method]
                        f = self.server.objmap[ns]
                        l = method.split(".")
                        for i in l:
                            f = getattr(f, i)
                except:
                    resp = buildSOAP(faultType("%s:Client" % NS.ENV_T,
                            "No method %s found" % nsmethod,
                            "%s %s" % tuple(sys.exc_info()[0:2])),
                        encoding = self.server.encoding,
                        config = self.server.config)
                    status = 500
                else:
                    try:
                        if header:
                            x = HeaderHandler(header, attrs)

                        # If it's wrapped, some special action may be needed

                        if isinstance(f, MethodSig):
                            c = None

                            if f.context:  # Build context object
                                c = SOAPContext(header, body, attrs, data,
                                    self.connection, self.headers,
                                    self.headers["soapaction"])

                            if f.keywords:
                                # This is lame, but have to de-unicode
                                # keywords

                                strkw = {}

                                for (k, v) in kw.items():
                                    strkw[str(k)] = v
                                if c:
                                    strkw["_SOAPContext"] = c
                                fr = apply(f, (), strkw)
                            elif c:
                                fr = apply(f, args, {'_SOAPContext':c})
                            else:
                                fr = apply(f, args, {})
                        else:
                            fr = apply(f, args, {})

                        if type(fr) == type(self) and \
                            isinstance(fr, voidType):
                            resp = buildSOAP(kw = {'%sResponse' % method: fr},
                                encoding = self.server.encoding,
                                config = self.server.config)
                        else:
                            resp = buildSOAP(kw =
                                {'%sResponse' % method: {'Result': fr}},
                                encoding = self.server.encoding,
                                config = self.server.config)
                    except Exception, e:
                        import traceback
                        info = sys.exc_info()

                        if self.server.config.dumpFaultInfo:
                            s = 'Method %s exception' % nsmethod
                            debugHeader(s)
                            traceback.print_exception(info[0], info[1],
                                info[2])
                            debugFooter(s)

                        if isinstance(e, faultType):
                            f = e
                        else:
                            f = faultType("%s:Server" % NS.ENV_T,
                               "Method %s failed." % nsmethod)

                        if self.server.config.returnFaultInfo:
                            f._setDetail("".join(traceback.format_exception(
                                    info[0], info[1], info[2])))
                        elif not hasattr(f, 'detail'):
                            f._setDetail("%s %s" % (info[0], info[1]))

                        resp = buildSOAP(f, encoding = self.server.encoding,
                           config = self.server.config)
                        status = 500
                    else:
                        status = 200
            except faultType, e:
                import traceback
                info = sys.exc_info()

                if self.server.config.dumpFaultInfo:
                    s = 'Received fault exception'
                    debugHeader(s)
                    traceback.print_exception(info[0], info[1],
                        info[2])
                    debugFooter(s)

                if self.server.config.returnFaultInfo:
                    e._setDetail("".join(traceback.format_exception(
                            info[0], info[1], info[2])))
                elif not hasattr(e, 'detail'):
                    e._setDetail("%s %s" % (info[0], info[1]))

                resp = buildSOAP(e, encoding = self.server.encoding,
                    config = self.server.config)
                status = 500
            except:
                # internal error, report as HTTP server error
                if self.server.config.dumpFaultInfo:
                    import traceback
                    s = 'Internal exception'
                    debugHeader(s)
                    traceback.print_exc ()
                    debugFooter(s)
                self.send_response(500)
                self.end_headers()

                if self.server.config.dumpHeadersOut and \
                    self.request_version != 'HTTP/0.9':
                    s = 'Outgoing HTTP headers'
                    debugHeader(s)
                    if self.responses.has_key(status):
                        s = ' ' + self.responses[status][0]
                    else:
                        s = ''
                    print "%s %d%s" % (self.protocol_version, 500, s)
                    print "Server:", self.version_string()
                    print "Date:", self.__last_date_time_string
                    debugFooter(s)
            else:
                # got a valid SOAP response
                self.send_response(status)

                t = 'text/xml';
                if self.server.encoding != None:
                    t += '; charset="%s"' % self.server.encoding
                self.send_header("Content-type", t)
                self.send_header("Content-length", str(len(resp)))
                self.end_headers()

                if self.server.config.dumpHeadersOut and \
                    self.request_version != 'HTTP/0.9':
                    s = 'Outgoing HTTP headers'
                    debugHeader(s)
                    if self.responses.has_key(status):
                        s = ' ' + self.responses[status][0]
                    else:
                        s = ''
                    print "%s %d%s" % (self.protocol_version, status, s)
                    print "Server:", self.version_string()
                    print "Date:", self.__last_date_time_string
                    print "Content-type:", t
                    print "Content-length:", len(resp)
                    debugFooter(s)

                if self.server.config.dumpSOAPOut:
                    s = 'Outgoing SOAP'
                    debugHeader(s)
                    print resp,
                    if resp[-1] != '\n':
                        print
                    debugFooter(s)

                self.wfile.write(resp)
                self.wfile.flush()

                # We should be able to shut down both a regular and an SSL
                # connection, but under Python 2.1, calling shutdown on an
                # SSL connections drops the output, so this work-around.
                # This should be investigated more someday.

                if self.server.config.SSLserver and \
                    isinstance(self.connection, SSL.Connection):
                    self.connection.set_shutdown(SSL.SSL_SENT_SHUTDOWN |
                        SSL.SSL_RECEIVED_SHUTDOWN)
                else:
                    self.connection.shutdown(1)

        def log_message(self, format, *args):
            if self.server.log:
                SOAPServer.BaseHTTPServer.BaseHTTPRequestHandler.\
                    log_message (self, format, *args)

    def __init__(self, addr = ('localhost', 8000),
        RequestHandler = SOAPRequestHandler, log = 1, encoding = 'UTF-8',
        config = Config, namespace = None, ssl_context = None):

        # Test the encoding, raising an exception if it's not known
        if encoding != None:
            ''.encode(encoding)

        if ssl_context != None and not config.SSLserver:
            raise AttributeError, \
                "SSL server not supported by this Python installation"

        self.namespace          = namespace
        self.objmap             = {}
        self.funcmap            = {}
        self.ssl_context        = ssl_context
        self.encoding           = encoding
        self.config             = config
        self.log                = log

        self.allow_reuse_address= 1

        SocketServer.TCPServer.__init__(self, addr, RequestHandler)

    def get_request(self):
        sock, addr = SocketServer.TCPServer.get_request(self)

        if self.ssl_context:
            sock = SSL.Connection(self.ssl_context, sock)
            sock._setup_ssl(addr)
            if sock.accept_ssl() != 1:
                raise socket.error, "Couldn't accept SSL connection"

        return sock, addr

    def registerObject(self, object, namespace = ''):
        if namespace == '': namespace = self.namespace
        self.objmap[namespace] = object

    def registerFunction(self, function, namespace = '', funcName = None):
        if not funcName : funcName = function.__name__
        if namespace == '': namespace = self.namespace
        if self.funcmap.has_key(namespace):
            self.funcmap[namespace][funcName] = function
        else:
            self.funcmap[namespace] = {funcName : function}

    def registerKWObject(self, object, namespace = ''):
        if namespace == '': namespace = self.namespace
        for i in dir(object.__class__):
            if i[0] != "_" and callable(getattr(object, i)):
                self.registerKWFunction(getattr(object,i), namespace)

    # convenience  - wraps your func for you.
    def registerKWFunction(self, function, namespace = '', funcName = None):
        self.registerFunction(MethodSig(function,keywords=1), namespace,
        funcName)
