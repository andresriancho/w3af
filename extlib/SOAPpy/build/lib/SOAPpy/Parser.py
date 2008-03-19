# SOAPpy modules
from Config    import Config
from Types     import *
from NS        import NS
from Utilities import *

import string
import fpconst
import xml.sax
from wstools.XMLname import fromXMLname

try: from M2Crypto import SSL
except: pass

ident = '$Id: Parser.py,v 1.16 2005/02/22 04:29:42 warnes Exp $'
from version import __version__


################################################################################
# SOAP Parser
################################################################################
class RefHolder:
    def __init__(self, name, frame):
        self.name = name
        self.parent = frame
        self.pos = len(frame)
        self.subpos = frame.namecounts.get(name, 0)

    def __repr__(self):
        return "<%s %s at %d>" % (self.__class__, self.name, id(self))

    def __str__(self):
        return "<%s %s at %d>" % (self.__class__, self.name, id(self))

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
                raise Error, "expected `SOAP-ENV:Envelope', gto `%s:%s'" % \
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

        self._data = [] # Start accumulating

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

        name = fromXMLname(name) # convert to SOAP 1.2 XML name encoding

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
                    raise Error, "Non-local hrefs are not yet suppported."
                if self._data != None and \
                   string.join(self._data, "").strip() != '':
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
                        #print "Kind with no NS:", kind
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


                ## Check for nil

                # check for nil='true'
                if type(null) in (StringType, UnicodeType):
                    if null.lower() == 'true':
                        null = 1

                # check for nil=1, but watch out for string values
                try:                
                    null = int(null)
                except ValueError, e:
                    if not e[0].startswith("invalid literal for int()"):
                        raise e
                    null = 0

                if null:
                    if len(cur) or \
                        (self._data != None and string.join(self._data, "").strip() != ''):
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
                    self._next = None # allow followons
                    break

            #print "\n"
            #print "data=", self._data
            #print "kind=", kind
            #print "cur.kind=", cur.kind
            #print "cur.rules=", cur.rules
            #print "\n"
                        

            if cur.rules != None:
                rule = cur.rules

                if type(rule) in (StringType, UnicodeType):
                    rule = (None, rule) # none flags special handling
                elif type(rule) == ListType:
                    rule = tuple(rule)

                #print "kind=",kind
                #print "rule=",rule


# XXX What if rule != kind?
                if callable(rule):
                    data = rule(string.join(self._data, ""))
                elif type(rule) == DictType:
                    data = structType(name = (ns, name), attrs = attrs)
                elif rule[1][:9] == 'arrayType':
                    data = self.convertType(cur.contents,
                                            rule, attrs)
                else:
                    data = self.convertType(string.join(self._data, ""),
                                            rule, attrs)

                break

            #print "No rules, using kind or cur.kind..."

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
                (self._data == None or string.join(self._data, "").strip() == ''):
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
                        data = self.convertType(string.join(self._data, ""),
                                                kind, attrs)
                    except UnknownTypeError:
                        data = None
                else:
                    data = None

                if data == None:
                    if self._data == None:
                        data = ''
                    else:
                        data = string.join(self._data, "")

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
            self._data.append(c)

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





    def convertType(self, d, t, attrs, config=Config):
        if t[0] is None and t[1] is not None:
            type = t[1].strip()
            if type[:9] == 'arrayType':
                index_eq = type.find('=')
                index_obr = type.find('[')
                index_cbr = type.find(']')
                elemtype = type[index_eq+1:index_obr]
                elemnum  = type[index_obr+1:index_cbr]
                if elemtype=="ur-type":
                    return(d)
                else:
                    newarr = map( lambda(di):
                                  self.convertToBasicTypes(d=di,
                                                       t = ( NS.XSD, elemtype),
                                                       attrs=attrs,
                                                       config=config),
                                  d)
                    return newarr
            else:
                t = (NS.XSD, t[1])

        return self.convertToBasicTypes(d, t, attrs, config)


    def convertToSOAPpyTypes(self, d, t, attrs, config=Config):
        pass


    def convertToBasicTypes(self, d, t, attrs, config=Config):
        dnn = d or ''

        #if Config.debug:
            #print "convertToBasicTypes:"
            #print "   requested_type=", t
            #print "   data=", d

        if t[0] in NS.EXSD_L:
            if t[1] == "integer":
                try:
                    d = int(d)
                    if len(attrs):
                        d = long(d)
                except:
                    d = long(d)
                return d
            if self.intlimits.has_key (t[1]): # integer types
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
            if t[1] in ('double','float'):
                l = self.floatlimits[t[1]]
                s = d.strip().lower()

                d = float(s)

                if config.strict_range:
                    if d < l[1]: raise UnderflowError
                    if d > l[2]: raise OverflowError
                else:
                    # some older SOAP impementations (notably SOAP4J,
                    # Apache SOAP) return "infinity" instead of "INF"
                    # so check the first 3 characters for a match.
                    if s == "nan":
                        return fpconst.NaN
                    elif s[0:3] in ("inf", "+inf"):
                        return fpconst.PosInf
                    elif s[0:3] == "-inf":
                        return fpconst.NegInf

                if fpconst.isNaN(d):
                    if s != 'nan':
                        raise ValueError, "invalid %s: %s" % (t[1], s)
                elif fpconst.isNegInf(d):
                    if s != '-inf':
                        raise UnderflowError, "%s too small: %s" % (t[1], s)
                elif fpconst.isPosInf(d):
                    if s != 'inf':
                        raise OverflowError, "%s too large: %s" % (t[1], s)
                elif d < 0 and d < l[1]:
                        raise UnderflowError, "%s too small: %s" % (t[1], s)
                elif d > 0 and ( d < l[0] or d > l[2] ):
                        raise OverflowError, "%s too large: %s" % (t[1], s)
                elif d == 0:
                    if type(self.zerofloatre) == StringType:
                        self.zerofloatre = re.compile(self.zerofloatre)

                    if self.zerofloatre.search(s):
                        raise UnderflowError, "invalid %s: %s" % (t[1], s)

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
                if d:
                    return base64.decodestring(d)
                else:
                    return ''
            if t[1] == "hexBinary":
                if d:
                    return decodeHexString(d)
                else:
                    return
            if t[1] == "anyURI":
                return urllib.unquote(collapseWhiteSpace(d))
            if t[1] in ("normalizedString", "token"):
                return collapseWhiteSpace(d)
        if t[0] == NS.ENC:
            if t[1] == "base64":
                if d:
                    return base64.decodestring(d)
                else:
                    return ''
        if t[0] == NS.XSD:
            if t[1] == "binary":
                try:
                    e = attrs[(None, 'encoding')]

                    if d:
                        if e == 'hex':
                            return decodeHexString(d)
                        elif e == 'base64':
                            return base64.decodestring(d)
                    else:
                        return ''
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

        raise UnknownTypeError, "unknown type `%s'" % (str(t[0]) + ':' + t[1])


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

    try:
        parser.parse(inpsrc)
    except xml.sax.SAXParseException, e:
        parser._parser = None
        raise e
    
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
    p = t.body[0]

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
