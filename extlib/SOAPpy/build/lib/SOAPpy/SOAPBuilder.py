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

ident = '$Id: SOAPBuilder.py,v 1.27 2005/02/21 20:24:13 warnes Exp $'
from version import __version__

import cgi
import copy
from wstools.XMLname import toXMLname, fromXMLname
import fpconst

# SOAPpy modules
from Config import Config
from NS     import NS
from Types  import *

# Test whether this Python version has Types.BooleanType
# If it doesn't have it, then False and True are serialized as integers
try:
    BooleanType
    pythonHasBooleanType = 1
except NameError:
    pythonHasBooleanType = 0

################################################################################
# SOAP Builder
################################################################################
class SOAPBuilder:
    _xml_top = '<?xml version="1.0"?>\n'
    _xml_enc_top = '<?xml version="1.0" encoding="%s"?>\n'
    _env_top = ( '%(ENV_T)s:Envelope\n' + \
                 '  %(ENV_T)s:encodingStyle="%(ENC)s"\n' ) % \
                 NS.__dict__
    _env_bot = '</%(ENV_T)s:Envelope>\n' % NS.__dict__

    # Namespaces potentially defined in the Envelope tag.

    _env_ns = {NS.ENC: NS.ENC_T, NS.ENV: NS.ENV_T,
        NS.XSD: NS.XSD_T, NS.XSD2: NS.XSD2_T, NS.XSD3: NS.XSD3_T,
        NS.XSI: NS.XSI_T, NS.XSI2: NS.XSI2_T, NS.XSI3: NS.XSI3_T}

    def __init__(self, args = (), kw = {}, method = None, namespace = None,
        header = None, methodattrs = None, envelope = 1, encoding = 'UTF-8',
        use_refs = 0, config = Config, noroot = 0):

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
        self.out        = []
        self.tcounter   = 0
        self.ncounter   = 1
        self.icounter   = 1
        self.envns      = {}
        self.ids        = {}
        self.depth      = 0
        self.multirefs  = []
        self.multis     = 0
        self.body       = not isinstance(args, bodyType)
        self.noroot     = noroot

    def build(self):
        if Config.debug: print "In build."
        ns_map = {}

        # Cache whether typing is on or not
        typed = self.config.typed

        if self.header:
            # Create a header.
            self.dump(self.header, "Header", typed = typed)
            #self.header = None # Wipe it out so no one is using it.

        if self.body:
            # Call genns to record that we've used SOAP-ENV.
            self.depth += 1
            body_ns = self.genns(ns_map, NS.ENV)[0]
            self.out.append("<%sBody>\n" % body_ns)

        if self.method:
            # Save the NS map so that it can be restored when we
            # fall out of the scope of the method definition
            save_ns_map = ns_map.copy()
            self.depth += 1
            a = ''
            if self.methodattrs:
                for (k, v) in self.methodattrs.items():
                    a += ' %s="%s"' % (k, v)

            if self.namespace:  # Use the namespace info handed to us
                methodns, n = self.genns(ns_map, self.namespace)
            else:
                methodns, n = '', ''

            self.out.append('<%s%s%s%s%s>\n' % (
                methodns, self.method, n, a, self.genroot(ns_map)))

        try:
            if type(self.args) != TupleType:
                args = (self.args,)
            else:
                args = self.args

            for i in args:
                self.dump(i, typed = typed, ns_map = ns_map)

            if hasattr(self.config, "argsOrdering") and self.config.argsOrdering.has_key(self.method):
                for k in self.config.argsOrdering.get(self.method):
                    self.dump(self.kw.get(k), k, typed = typed, ns_map = ns_map)                
            else:
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
            self.out.append("</%s%s>\n" % (methodns, self.method))
            # End of the method definition; drop any local namespaces
            ns_map = save_ns_map
            self.depth -= 1

        if self.body:
            # dump may add to self.multirefs, but the for loop will keep
            # going until it has used all of self.multirefs, even those
            # entries added while in the loop.

            self.multis = 1

            for obj, tag in self.multirefs:
                self.dump(obj, tag, typed = typed, ns_map = ns_map)

            self.out.append("</%sBody>\n" % body_ns)
            self.depth -= 1

        if self.envelope:
            e = map (lambda ns: '  xmlns:%s="%s"\n' % (ns[1], ns[0]),
                self.envns.items())

            self.out = ['<', self._env_top] + e + ['>\n'] + \
                       self.out + \
                       [self._env_bot]

        if self.encoding != None:
            self.out.insert(0, self._xml_enc_top % self.encoding)
            return ''.join(self.out).encode(self.encoding)

        self.out.insert(0, self._xml_top)
        return ''.join(self.out)

    def gentag(self):
        if Config.debug: print "In gentag."
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
        if self.noroot:
            return ''

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

        self.out.append('<%s href="#i%d"%s/>\n' %
                        (tag, n, self.genroot(ns_map)))
        return None

    # dumpers

    def dump(self, obj, tag = None, typed = 1, ns_map = {}):
        if Config.debug: print "In dump.", "obj=", obj
        ns_map = ns_map.copy()
        self.depth += 1

        if type(tag) not in (NoneType, StringType, UnicodeType):
            raise KeyError, "tag must be a string or None"

        try:
            meth = getattr(self, "dump_" + type(obj).__name__)
        except AttributeError:
            if type(obj) == LongType:
                obj_type = "integer"
            elif pythonHasBooleanType and type(obj) == BooleanType:
                obj_type = "boolean"
            else:
                obj_type = type(obj).__name__

            self.out.append(self.dumper(None, obj_type, obj, tag, typed,
                                        ns_map, self.genroot(ns_map)))
        else:
            meth(obj, tag, typed, ns_map)


        self.depth -= 1

    # generic dumper
    def dumper(self, nsURI, obj_type, obj, tag, typed = 1, ns_map = {},
               rootattr = '', id = '',
               xml = '<%(tag)s%(type)s%(id)s%(attrs)s%(root)s>%(data)s</%(tag)s>\n'):
        if Config.debug: print "In dumper."

        if nsURI == None:
            nsURI = self.config.typesNamespaceURI

        tag = tag or self.gentag()

        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        a = n = t = ''
        if typed and obj_type:
            ns, n = self.genns(ns_map, nsURI)
            ins = self.genns(ns_map, self.config.schemaNamespaceURI)[0]
            t = ' %stype="%s%s"%s' % (ins, ns, obj_type, n)

        try: a = obj._marshalAttrs(ns_map, self)
        except: pass

        try: data = obj._marshalData()
        except:
            if (obj_type != "string"): # strings are already encoded
                data = cgi.escape(str(obj))
            else:
                data = obj


        return xml % {"tag": tag, "type": t, "data": data, "root": rootattr,
            "id": id, "attrs": a}

    def dump_float(self, obj, tag, typed = 1, ns_map = {}):
        if Config.debug: print "In dump_float."
        tag = tag or self.gentag()

        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        if Config.strict_range:
            doubleType(obj)

        if fpconst.isPosInf(obj):
            obj = "INF"
        elif fpconst.isNegInf(obj):
            obj = "-INF"
        elif fpconst.isNaN(obj):
            obj = "NaN"
        else:
            obj = repr(obj)

	# Note: python 'float' is actually a SOAP 'double'.
        self.out.append(self.dumper(None, "double", obj, tag, typed, ns_map,
                                    self.genroot(ns_map)))

    def dump_string(self, obj, tag, typed = 0, ns_map = {}):
        if Config.debug: print "In dump_string."
        tag = tag or self.gentag()
        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        try: data = obj._marshalData()
        except: data = obj

        self.out.append(self.dumper(None, "string", cgi.escape(data), tag,
                                    typed, ns_map, self.genroot(ns_map), id))

    dump_str = dump_string # For Python 2.2+
    dump_unicode = dump_string

    def dump_None(self, obj, tag, typed = 0, ns_map = {}):
        if Config.debug: print "In dump_None."
        tag = tag or self.gentag()
        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding
        ns = self.genns(ns_map, self.config.schemaNamespaceURI)[0]

        self.out.append('<%s %snull="1"%s/>\n' %
                        (tag, ns, self.genroot(ns_map)))

    dump_NoneType = dump_None # For Python 2.2+

    def dump_list(self, obj, tag, typed = 1, ns_map = {}):
        if Config.debug: print "In dump_list.",  "obj=", obj
        tag = tag or self.gentag()
        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        if type(obj) == InstanceType:
            data = obj.data
        else:
            data = obj

        if typed:
            id = self.checkref(obj, tag, ns_map)
            if id == None:
                return

        try:
            sample = data[0]
            empty = 0
        except:
            # preserve type if present
            if getattr(obj,"_typed",None) and getattr(obj,"_type",None):
		if getattr(obj, "_complexType", None):
                    sample = typedArrayType(typed=obj._type,
                                            complexType = obj._complexType)
                    sample._typename = obj._type
                    if not getattr(obj,"_ns",None): obj._ns = NS.URN
		else:
                    sample = typedArrayType(typed=obj._type)
            else:
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
                   type(sample) == DictType or \
                   (isinstance(sample, anyType) and \
                    (getattr(sample, "_complexType", None) and \
                     sample._complexType)): # force to urn struct
                try:
                    tns = obj._ns or NS.URN
                except:
                    tns = NS.URN

                ns, ndecl = self.genns(ns_map, tns)

                try:
                    typename = sample._typename
                except:
                    typename = "SOAPStruct"

                t = ns + typename
                                
            elif isinstance(sample, anyType):
                ns = sample._validNamespaceURI(self.config.typesNamespaceURI,
                                               self.config.strictNamespaces)
                if ns:
                    ns, ndecl = self.genns(ns_map, ns)
                    t = ns + str(sample._type)
                else:
                    t = 'ur-type'
            else:
		typename = type(sample).__name__

                # For Python 2.2+
                if type(sample) == StringType: typename = 'string'

                # HACK: unicode is a SOAP string
                if type(sample) == UnicodeType: typename = 'string'
                
		# HACK: python 'float' is actually a SOAP 'double'.
		if typename=="float": typename="double"  
                t = self.genns(ns_map, self.config.typesNamespaceURI)[0] + \
		    typename

        else:
            t = self.genns(ns_map, self.config.typesNamespaceURI)[0] + \
                "ur-type"

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        ens, edecl = self.genns(ns_map, NS.ENC)
        ins, idecl = self.genns(ns_map, self.config.schemaNamespaceURI)

        if typed:
            self.out.append(
                '<%s %sarrayType="%s[%d]" %stype="%sArray"%s%s%s%s%s%s>\n' %
                (tag, ens, t, len(data), ins, ens, ndecl, edecl, idecl,
                 self.genroot(ns_map), id, a))

        if typed:
            try: elemsname = obj._elemsname
            except: elemsname = "item"
        else:
            elemsname = tag
            
        for i in data:
            self.dump(i, elemsname, not same_type, ns_map)

        if typed: self.out.append('</%s>\n' % tag)

    dump_tuple = dump_list

    def dump_dictionary(self, obj, tag, typed = 1, ns_map = {}):
        if Config.debug: print "In dump_dictionary."
        tag = tag or self.gentag()
        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        id = self.checkref(obj, tag, ns_map)
        if id == None:
            return

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        self.out.append('<%s%s%s%s>\n' % 
                        (tag, id, a, self.genroot(ns_map)))

        for (k, v) in obj.items():
            if k[0] != "_":
                self.dump(v, k, 1, ns_map)

        self.out.append('</%s>\n' % tag)

    dump_dict = dump_dictionary # For Python 2.2+

    def dump_instance(self, obj, tag, typed = 1, ns_map = {}):
        if Config.debug: print "In dump_instance.", "obj=", obj, "tag=", tag
        if not tag:
            # If it has a name use it.
            if isinstance(obj, anyType) and obj._name:
                tag = obj._name
            else:
                tag = self.gentag()
        tag = toXMLname(tag) # convert from SOAP 1.2 XML name encoding

        if isinstance(obj, arrayType):      # Array
            self.dump_list(obj, tag, typed, ns_map)
            return

        if isinstance(obj, faultType):    # Fault
            cns, cdecl = self.genns(ns_map, NS.ENC)
            vns, vdecl = self.genns(ns_map, NS.ENV)
            self.out.append('''<%sFault %sroot="1"%s%s>
<faultcode>%s</faultcode>
<faultstring>%s</faultstring>
''' % (vns, cns, vdecl, cdecl, obj.faultcode, obj.faultstring))
            if hasattr(obj, "detail"):
                self.dump(obj.detail, "detail", typed, ns_map)
            self.out.append("</%sFault>\n" % vns)
            return

        r = self.genroot(ns_map)

        try: a = obj._marshalAttrs(ns_map, self)
        except: a = ''

        if isinstance(obj, voidType):     # void
            self.out.append("<%s%s%s></%s>\n" % (tag, a, r, tag))
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
            self.out.append("<%s%s%s%s%s>\n" % (tag, ndecl, id, a, r))

            keylist = obj.__dict__.keys()

            # first write out items with order information
            if hasattr(obj, '_keyord'):
                for i in range(len(obj._keyord)):
                    self.dump(obj._aslist(i), obj._keyord[i], 1, ns_map)
                    keylist.remove(obj._keyord[i])

            # now write out the rest
            for k in keylist:
                if (k[0] != "_"):
                    self.dump(getattr(obj,k), k, 1, ns_map)

            if isinstance(obj, bodyType):
                self.multis = 1

                for v, k in self.multirefs:
                    self.dump(v, k, typed = typed, ns_map = ns_map)

            self.out.append('</%s>\n' % tag)

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

            self.out.append('<%s%s%s%s%s>%s</%s>\n' %
                            (tag, t, id, a, r, obj._marshalData(), tag))

        else:                           # Some Class
            self.out.append('<%s%s%s>\n' % (tag, id, r))

            for (k, v) in obj.__dict__.items():
                if k[0] != "_":
                    self.dump(v, k, 1, ns_map)

            self.out.append('</%s>\n' % tag)


################################################################################
# SOAPBuilder's more public interface
################################################################################

def buildSOAP(args=(), kw={}, method=None, namespace=None,
              header=None, methodattrs=None, envelope=1, encoding='UTF-8',
              config=Config, noroot = 0):
    t = SOAPBuilder(args=args, kw=kw, method=method, namespace=namespace,
                    header=header, methodattrs=methodattrs,envelope=envelope,
                    encoding=encoding, config=config,noroot=noroot)
    return t.build()
