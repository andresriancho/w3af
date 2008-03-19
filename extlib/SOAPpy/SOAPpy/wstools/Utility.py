# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

ident = "$Id: Utility.py,v 1.20 2005/02/09 18:33:05 boverhof Exp $"

import types
import string, httplib, smtplib, urllib, socket, weakref
from os.path import isfile
from string import join, strip, split
from UserDict import UserDict
from cStringIO import StringIO
from TimeoutSocket import TimeoutSocket, TimeoutError
from urlparse import urlparse
from httplib import HTTPConnection, HTTPSConnection
from exceptions import Exception

import xml.dom.minidom
from xml.dom import Node

import logging
from c14n import Canonicalize
from Namespaces import SCHEMA, SOAP, XMLNS, ZSI_SCHEMA_URI


try:
    from xml.dom.ext import SplitQName
except:
    def SplitQName(qname):
        '''SplitQName(qname) -> (string, string)
        
           Split Qualified Name into a tuple of len 2, consisting 
           of the prefix and the local name.  
    
           (prefix, localName)
        
           Special Cases:
               xmlns -- (localName, 'xmlns')
               None -- (None, localName)
        '''
        
        l = qname.split(':')
        if len(l) == 1:
            l.insert(0, None)
        elif len(l) == 2:
            if l[0] == 'xmlns':
                l.reverse()
        else:
            return
        return tuple(l)


class NamespaceError(Exception):
    """Used to indicate a Namespace Error."""


class RecursionError(Exception):
    """Used to indicate a HTTP redirect recursion."""


class ParseError(Exception):
    """Used to indicate a XML parsing error."""


class DOMException(Exception):
    """Used to indicate a problem processing DOM."""


class Base:
    """Base class for instance level Logging"""
    def __init__(self, module=__name__):
        self.logger = logging.getLogger('%s-%s(%x)' %(module, self.__class__, id(self)))


class HTTPResponse:
    """Captures the information in an HTTP response message."""

    def __init__(self, response):
        self.status = response.status
        self.reason = response.reason
        self.headers = response.msg
        self.body = response.read() or None
        response.close()

class TimeoutHTTP(HTTPConnection):
    """A custom http connection object that supports socket timeout."""
    def __init__(self, host, port=None, timeout=20):
        HTTPConnection.__init__(self, host, port)
        self.timeout = timeout

    def connect(self):
        self.sock = TimeoutSocket(self.timeout)
        self.sock.connect((self.host, self.port))


class TimeoutHTTPS(HTTPSConnection):
    """A custom https object that supports socket timeout. Note that this
       is not really complete. The builtin SSL support in the Python socket
       module requires a real socket (type) to be passed in to be hooked to
       SSL. That means our fake socket won't work and our timeout hacks are
       bypassed for send and recv calls. Since our hack _is_ in place at
       connect() time, it should at least provide some timeout protection."""
    def __init__(self, host, port=None, timeout=20, **kwargs):
        HTTPSConnection.__init__(self, str(host), port, **kwargs)
        self.timeout = timeout

    def connect(self):
        sock = TimeoutSocket(self.timeout)
        sock.connect((self.host, self.port))
        realsock = getattr(sock.sock, '_sock', sock.sock)
        ssl = socket.ssl(realsock, self.key_file, self.cert_file)
        self.sock = httplib.FakeSocket(sock, ssl)

def urlopen(url, timeout=20, redirects=None):
    """A minimal urlopen replacement hack that supports timeouts for http.
       Note that this supports GET only."""
    scheme, host, path, params, query, frag = urlparse(url)

    if not scheme in ('http', 'https'):
        return urllib.urlopen(url)
    if params: path = '%s;%s' % (path, params)
    if query:  path = '%s?%s' % (path, query)
    if frag:   path = '%s#%s' % (path, frag)

    if scheme == 'https':
        # If ssl is not compiled into Python, you will not get an exception
        # until a conn.endheaders() call.   We need to know sooner, so use
        # getattr.
        if hasattr(socket, 'ssl'):
            conn = TimeoutHTTPS(host, None, timeout)
        else:
            import M2Crypto
            ctx = M2Crypto.SSL.Context()
            ctx.set_session_timeout(timeout)
            conn = M2Crypto.httpslib.HTTPSConnection(host, ssl_context=ctx)
            #conn.set_debuglevel(1)
    else:
        conn = TimeoutHTTP(host, None, timeout)

    conn.putrequest('GET', path)
    conn.putheader('Connection', 'close')
    conn.endheaders()
    response = None
    while 1:
        response = conn.getresponse()
        if response.status != 100:
            break
        conn._HTTPConnection__state = httplib._CS_REQ_SENT
        conn._HTTPConnection__response = None

    status = response.status

    # If we get an HTTP redirect, we will follow it automatically.
    if status >= 300 and status < 400:
        location = response.msg.getheader('location')
        if location is not None:
            response.close()
            if redirects is not None and redirects.has_key(location):
                raise RecursionError(
                    'Circular HTTP redirection detected.'
                    )
            if redirects is None:
                redirects = {}
            redirects[location] = 1
            return urlopen(location, timeout, redirects)
        raise HTTPResponse(response)

    if not (status >= 200 and status < 300):
        raise HTTPResponse(response)

    body = StringIO(response.read())
    response.close()
    return body

class DOM:
    """The DOM singleton defines a number of XML related constants and
       provides a number of utility methods for DOM related tasks. It
       also provides some basic abstractions so that the rest of the
       package need not care about actual DOM implementation in use."""

    # Namespace stuff related to the SOAP specification.

    NS_SOAP_ENV_1_1 = 'http://schemas.xmlsoap.org/soap/envelope/'
    NS_SOAP_ENC_1_1 = 'http://schemas.xmlsoap.org/soap/encoding/'

    NS_SOAP_ENV_1_2 = 'http://www.w3.org/2001/06/soap-envelope'
    NS_SOAP_ENC_1_2 = 'http://www.w3.org/2001/06/soap-encoding'

    NS_SOAP_ENV_ALL = (NS_SOAP_ENV_1_1, NS_SOAP_ENV_1_2)
    NS_SOAP_ENC_ALL = (NS_SOAP_ENC_1_1, NS_SOAP_ENC_1_2)

    NS_SOAP_ENV = NS_SOAP_ENV_1_1
    NS_SOAP_ENC = NS_SOAP_ENC_1_1

    _soap_uri_mapping = {
        NS_SOAP_ENV_1_1 : '1.1',
        NS_SOAP_ENV_1_2 : '1.2',
    }

    SOAP_ACTOR_NEXT_1_1 = 'http://schemas.xmlsoap.org/soap/actor/next'
    SOAP_ACTOR_NEXT_1_2 = 'http://www.w3.org/2001/06/soap-envelope/actor/next'
    SOAP_ACTOR_NEXT_ALL = (SOAP_ACTOR_NEXT_1_1, SOAP_ACTOR_NEXT_1_2)
    
    def SOAPUriToVersion(self, uri):
        """Return the SOAP version related to an envelope uri."""
        value = self._soap_uri_mapping.get(uri)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported SOAP envelope uri: %s' % uri
            )

    def GetSOAPEnvUri(self, version):
        """Return the appropriate SOAP envelope uri for a given
           human-friendly SOAP version string (e.g. '1.1')."""
        attrname = 'NS_SOAP_ENV_%s' % join(split(version, '.'), '_')
        value = getattr(self, attrname, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported SOAP version: %s' % version
            )

    def GetSOAPEncUri(self, version):
        """Return the appropriate SOAP encoding uri for a given
           human-friendly SOAP version string (e.g. '1.1')."""
        attrname = 'NS_SOAP_ENC_%s' % join(split(version, '.'), '_')
        value = getattr(self, attrname, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported SOAP version: %s' % version
            )

    def GetSOAPActorNextUri(self, version):
        """Return the right special next-actor uri for a given
           human-friendly SOAP version string (e.g. '1.1')."""
        attrname = 'SOAP_ACTOR_NEXT_%s' % join(split(version, '.'), '_')
        value = getattr(self, attrname, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported SOAP version: %s' % version
            )


    # Namespace stuff related to XML Schema.

    NS_XSD_99 = 'http://www.w3.org/1999/XMLSchema'
    NS_XSI_99 = 'http://www.w3.org/1999/XMLSchema-instance'    

    NS_XSD_00 = 'http://www.w3.org/2000/10/XMLSchema'
    NS_XSI_00 = 'http://www.w3.org/2000/10/XMLSchema-instance'    

    NS_XSD_01 = 'http://www.w3.org/2001/XMLSchema'
    NS_XSI_01 = 'http://www.w3.org/2001/XMLSchema-instance'

    NS_XSD_ALL = (NS_XSD_99, NS_XSD_00, NS_XSD_01)
    NS_XSI_ALL = (NS_XSI_99, NS_XSI_00, NS_XSI_01)

    NS_XSD = NS_XSD_01
    NS_XSI = NS_XSI_01

    _xsd_uri_mapping = {
        NS_XSD_99 : NS_XSI_99,
        NS_XSD_00 : NS_XSI_00,
        NS_XSD_01 : NS_XSI_01,
    }

    for key, value in _xsd_uri_mapping.items():
        _xsd_uri_mapping[value] = key


    def InstanceUriForSchemaUri(self, uri):
        """Return the appropriate matching XML Schema instance uri for
           the given XML Schema namespace uri."""
        return self._xsd_uri_mapping.get(uri)

    def SchemaUriForInstanceUri(self, uri):
        """Return the appropriate matching XML Schema namespace uri for
           the given XML Schema instance namespace uri."""
        return self._xsd_uri_mapping.get(uri)


    # Namespace stuff related to WSDL.

    NS_WSDL_1_1 = 'http://schemas.xmlsoap.org/wsdl/'
    NS_WSDL_ALL = (NS_WSDL_1_1,)
    NS_WSDL = NS_WSDL_1_1

    NS_SOAP_BINDING_1_1 = 'http://schemas.xmlsoap.org/wsdl/soap/'
    NS_HTTP_BINDING_1_1 = 'http://schemas.xmlsoap.org/wsdl/http/'
    NS_MIME_BINDING_1_1 = 'http://schemas.xmlsoap.org/wsdl/mime/'

    NS_SOAP_BINDING_ALL = (NS_SOAP_BINDING_1_1,)
    NS_HTTP_BINDING_ALL = (NS_HTTP_BINDING_1_1,)
    NS_MIME_BINDING_ALL = (NS_MIME_BINDING_1_1,)

    NS_SOAP_BINDING = NS_SOAP_BINDING_1_1
    NS_HTTP_BINDING = NS_HTTP_BINDING_1_1
    NS_MIME_BINDING = NS_MIME_BINDING_1_1

    NS_SOAP_HTTP_1_1 = 'http://schemas.xmlsoap.org/soap/http'
    NS_SOAP_HTTP_ALL = (NS_SOAP_HTTP_1_1,)
    NS_SOAP_HTTP = NS_SOAP_HTTP_1_1
    

    _wsdl_uri_mapping = {
        NS_WSDL_1_1 : '1.1',
    }
    
    def WSDLUriToVersion(self, uri):
        """Return the WSDL version related to a WSDL namespace uri."""
        value = self._wsdl_uri_mapping.get(uri)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported SOAP envelope uri: %s' % uri
            )

    def GetWSDLUri(self, version):
        attr = 'NS_WSDL_%s' % join(split(version, '.'), '_')
        value = getattr(self, attr, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported WSDL version: %s' % version
            )

    def GetWSDLSoapBindingUri(self, version):
        attr = 'NS_SOAP_BINDING_%s' % join(split(version, '.'), '_')
        value = getattr(self, attr, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported WSDL version: %s' % version
            )

    def GetWSDLHttpBindingUri(self, version):
        attr = 'NS_HTTP_BINDING_%s' % join(split(version, '.'), '_')
        value = getattr(self, attr, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported WSDL version: %s' % version
            )

    def GetWSDLMimeBindingUri(self, version):
        attr = 'NS_MIME_BINDING_%s' % join(split(version, '.'), '_')
        value = getattr(self, attr, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported WSDL version: %s' % version
            )

    def GetWSDLHttpTransportUri(self, version):
        attr = 'NS_SOAP_HTTP_%s' % join(split(version, '.'), '_')
        value = getattr(self, attr, None)
        if value is not None:
            return value
        raise ValueError(
            'Unsupported WSDL version: %s' % version
            )


    # Other xml namespace constants.
    NS_XMLNS     = 'http://www.w3.org/2000/xmlns/'



    def isElement(self, node, name, nsuri=None):
        """Return true if the given node is an element with the given
           name and optional namespace uri."""
        if node.nodeType != node.ELEMENT_NODE:
            return 0
        return node.localName == name and \
               (nsuri is None or self.nsUriMatch(node.namespaceURI, nsuri))

    def getElement(self, node, name, nsuri=None, default=join):
        """Return the first child of node with a matching name and
           namespace uri, or the default if one is provided."""
        nsmatch = self.nsUriMatch
        ELEMENT_NODE = node.ELEMENT_NODE
        for child in node.childNodes:
            if child.nodeType == ELEMENT_NODE:
                if ((child.localName == name or name is None) and
                    (nsuri is None or nsmatch(child.namespaceURI, nsuri))
                    ):
                    return child
        if default is not join:
            return default
        raise KeyError, name

    def getElementById(self, node, id, default=join):
        """Return the first child of node matching an id reference."""
        attrget = self.getAttr
        ELEMENT_NODE = node.ELEMENT_NODE
        for child in node.childNodes:
            if child.nodeType == ELEMENT_NODE:
                if attrget(child, 'id') == id:
                    return child
        if default is not join:
            return default
        raise KeyError, name

    def getMappingById(self, document, depth=None, element=None,
                       mapping=None, level=1):
        """Create an id -> element mapping of those elements within a
           document that define an id attribute. The depth of the search
           may be controlled by using the (1-based) depth argument."""
        if document is not None:
            element = document.documentElement
            mapping = {}
        attr = element._attrs.get('id', None)
        if attr is not None:
            mapping[attr.value] = element
        if depth is None or depth > level:
            level = level + 1
            ELEMENT_NODE = element.ELEMENT_NODE
            for child in element.childNodes:
                if child.nodeType == ELEMENT_NODE:
                    self.getMappingById(None, depth, child, mapping, level)
        return mapping        

    def getElements(self, node, name, nsuri=None):
        """Return a sequence of the child elements of the given node that
           match the given name and optional namespace uri."""
        nsmatch = self.nsUriMatch
        result = []
        ELEMENT_NODE = node.ELEMENT_NODE
        for child in node.childNodes:
            if child.nodeType == ELEMENT_NODE:
                if ((child.localName == name or name is None) and (
                    (nsuri is None) or nsmatch(child.namespaceURI, nsuri))):
                    result.append(child)
        return result

    def hasAttr(self, node, name, nsuri=None):
        """Return true if element has attribute with the given name and
           optional nsuri. If nsuri is not specified, returns true if an
           attribute exists with the given name with any namespace."""
        if nsuri is None:
            if node.hasAttribute(name):
                return True
            return False
        return node.hasAttributeNS(nsuri, name)

    def getAttr(self, node, name, nsuri=None, default=join):
        """Return the value of the attribute named 'name' with the
           optional nsuri, or the default if one is specified. If
           nsuri is not specified, an attribute that matches the
           given name will be returned regardless of namespace."""
        if nsuri is None:
            result = node._attrs.get(name, None)
            if result is None:
                for item in node._attrsNS.keys():
                    if item[1] == name:
                        result = node._attrsNS[item]
                        break
        else:
            result = node._attrsNS.get((nsuri, name), None)
        if result is not None:
            return result.value
        if default is not join:
            return default
        return ''

    def getAttrs(self, node):
        """Return a Collection of all attributes 
        """
        attrs = {}
        for k,v in node._attrs.items():
            attrs[k] = v.value
        return attrs

    def getElementText(self, node, preserve_ws=None):
        """Return the text value of an xml element node. Leading and trailing
           whitespace is stripped from the value unless the preserve_ws flag
           is passed with a true value."""
        result = []
        for child in node.childNodes:
            nodetype = child.nodeType
            if nodetype == child.TEXT_NODE or \
               nodetype == child.CDATA_SECTION_NODE:
                result.append(child.nodeValue)
        value = join(result, '')
        if preserve_ws is None:
            value = strip(value)
        return value

    def findNamespaceURI(self, prefix, node):
        """Find a namespace uri given a prefix and a context node."""
        attrkey = (self.NS_XMLNS, prefix)
        DOCUMENT_NODE = node.DOCUMENT_NODE
        ELEMENT_NODE = node.ELEMENT_NODE
        while 1:
            if node is None:
                raise DOMException('Value for prefix %s not found.' % prefix)
            if node.nodeType != ELEMENT_NODE:
                node = node.parentNode
                continue
            result = node._attrsNS.get(attrkey, None)
            if result is not None:
                return result.value
            if hasattr(node, '__imported__'):
                raise DOMException('Value for prefix %s not found.' % prefix)
            node = node.parentNode
            if node.nodeType == DOCUMENT_NODE:
                raise DOMException('Value for prefix %s not found.' % prefix)

    def findDefaultNS(self, node):
        """Return the current default namespace uri for the given node."""
        attrkey = (self.NS_XMLNS, 'xmlns')
        DOCUMENT_NODE = node.DOCUMENT_NODE
        ELEMENT_NODE = node.ELEMENT_NODE
        while 1:
            if node.nodeType != ELEMENT_NODE:
                node = node.parentNode
                continue
            result = node._attrsNS.get(attrkey, None)
            if result is not None:
                return result.value
            if hasattr(node, '__imported__'):
                raise DOMException('Cannot determine default namespace.')
            node = node.parentNode
            if node.nodeType == DOCUMENT_NODE:
                raise DOMException('Cannot determine default namespace.')

    def findTargetNS(self, node):
        """Return the defined target namespace uri for the given node."""
        attrget = self.getAttr
        attrkey = (self.NS_XMLNS, 'xmlns')
        DOCUMENT_NODE = node.DOCUMENT_NODE
        ELEMENT_NODE = node.ELEMENT_NODE
        while 1:
            if node.nodeType != ELEMENT_NODE:
                node = node.parentNode
                continue
            result = attrget(node, 'targetNamespace', default=None)
            if result is not None:
                return result
            node = node.parentNode
            if node.nodeType == DOCUMENT_NODE:
                raise DOMException('Cannot determine target namespace.')

    def getTypeRef(self, element):
        """Return (namespaceURI, name) for a type attribue of the given
           element, or None if the element does not have a type attribute."""
        typeattr = self.getAttr(element, 'type', default=None)
        if typeattr is None:
            return None
        parts = typeattr.split(':', 1)
        if len(parts) == 2:
            nsuri = self.findNamespaceURI(parts[0], element)
        else:
            nsuri = self.findDefaultNS(element)
        return (nsuri, parts[1])

    def importNode(self, document, node, deep=0):
        """Implements (well enough for our purposes) DOM node import."""
        nodetype = node.nodeType
        if nodetype in (node.DOCUMENT_NODE, node.DOCUMENT_TYPE_NODE):
            raise DOMException('Illegal node type for importNode')
        if nodetype == node.ENTITY_REFERENCE_NODE:
            deep = 0
        clone = node.cloneNode(deep)
        self._setOwnerDoc(document, clone)
        clone.__imported__ = 1
        return clone

    def _setOwnerDoc(self, document, node):
        node.ownerDocument = document
        for child in node.childNodes:
            self._setOwnerDoc(document, child)

    def nsUriMatch(self, value, wanted, strict=0, tt=type(())):
        """Return a true value if two namespace uri values match."""
        if value == wanted or (type(wanted) is tt) and value in wanted:
            return 1
        if not strict:
            wanted = type(wanted) is tt and wanted or (wanted,)
            value = value[-1:] != '/' and value or value[:-1]
            for item in wanted:
                if item == value or item[:-1] == value:
                    return 1
        return 0

    def createDocument(self, nsuri, qname, doctype=None):
        """Create a new writable DOM document object."""
        impl = xml.dom.minidom.getDOMImplementation()
        return impl.createDocument(nsuri, qname, doctype)

    def loadDocument(self, data):
        """Load an xml file from a file-like object and return a DOM
           document instance."""
        return xml.dom.minidom.parse(data)

    def loadFromURL(self, url):
        """Load an xml file from a URL and return a DOM document."""
        if isfile(url) is True:
            file = open(url, 'r')
        else:
            file = urlopen(url)

        try:     
            result = self.loadDocument(file)
        except Exception, ex:
            file.close()
            raise ParseError(('Failed to load document %s' %url,) + ex.args)
        else:
            file.close()
        return result

DOM = DOM()


class MessageInterface:
    '''Higher Level Interface, delegates to DOM singleton, must 
    be subclassed and implement all methods that throw NotImplementedError.
    '''
    def __init__(self, sw):
        '''Constructor, May be extended, do not override.
            sw -- soapWriter instance
        '''
        self.sw = None
        if type(sw) != weakref.ReferenceType and sw is not None:
            self.sw = weakref.ref(sw)
        else:
            self.sw = sw

    def AddCallback(self, func, *arglist):
        self.sw().AddCallback(func, *arglist)

    def Known(self, obj):
        return self.sw().Known(obj)

    def Forget(self, obj):
        return self.sw().Forget(obj)

    def canonicalize(self):
        '''canonicalize the underlying DOM, and return as string.
        '''
        raise NotImplementedError, ''

    def createDocument(self, namespaceURI=SOAP.ENV, localName='Envelope'):
        '''create Document
        '''
        raise NotImplementedError, ''

    def createAppendElement(self, namespaceURI, localName):
        '''create and append element(namespaceURI,localName), and return
        the node.
        '''
        raise NotImplementedError, ''

    def findNamespaceURI(self, qualifiedName):
        raise NotImplementedError, ''

    def resolvePrefix(self, prefix):
        raise NotImplementedError, ''

    def setAttributeNS(self, namespaceURI, localName, value):
        '''set attribute (namespaceURI, localName)=value
        '''
        raise NotImplementedError, ''

    def setAttributeType(self, namespaceURI, localName):
        '''set attribute xsi:type=(namespaceURI, localName)
        '''
        raise NotImplementedError, ''

    def setNamespaceAttribute(self, namespaceURI, prefix):
        '''set namespace attribute xmlns:prefix=namespaceURI 
        '''
        raise NotImplementedError, ''


class ElementProxy(Base, MessageInterface):
    '''
    '''
    _soap_env_prefix = 'SOAP-ENV'
    _soap_enc_prefix = 'SOAP-ENC'
    _zsi_prefix = 'ZSI'
    _xsd_prefix = 'xsd'
    _xsi_prefix = 'xsi'
    _xml_prefix = 'xml'
    _xmlns_prefix = 'xmlns'

    _soap_env_nsuri = SOAP.ENV
    _soap_enc_nsuri = SOAP.ENC
    _zsi_nsuri = ZSI_SCHEMA_URI
    _xsd_nsuri =  SCHEMA.XSD3
    _xsi_nsuri = SCHEMA.XSI3
    _xml_nsuri = XMLNS.XML
    _xmlns_nsuri = XMLNS.BASE

    standard_ns = {\
        _xml_prefix:_xml_nsuri,
        _xmlns_prefix:_xmlns_nsuri
    }
    reserved_ns = {\
        _soap_env_prefix:_soap_env_nsuri,
        _soap_enc_prefix:_soap_enc_nsuri,
        _zsi_prefix:_zsi_nsuri,
        _xsd_prefix:_xsd_nsuri,
        _xsi_prefix:_xsi_nsuri,
    }
    name = None
    namespaceURI = None

    def __init__(self, sw, message=None):
        '''Initialize. 
           sw -- SoapWriter
        '''
        self._indx = 0
        MessageInterface.__init__(self, sw)
        Base.__init__(self)
        self._dom = DOM
        self.node = None
        if type(message) in (types.StringType,types.UnicodeType):
            self.loadFromString(message)
        elif isinstance(message, ElementProxy):
            self.node = message._getNode()
        else:
            self.node = message
        self.processorNss = self.standard_ns.copy()
        self.processorNss.update(self.reserved_ns)

    def __str__(self):
        return self.toString()

    def evaluate(self, expression, processorNss=None):
        '''expression -- XPath compiled expression
        '''
        from Ft.Xml import XPath
        if not processorNss:
            context = XPath.Context.Context(self.node, processorNss=self.processorNss)
        else:
            context = XPath.Context.Context(self.node, processorNss=processorNss)
        nodes = expression.evaluate(context)
        return map(lambda node: ElementProxy(self.sw,node), nodes)

    #############################################
    # Methods for checking/setting the
    # classes (namespaceURI,name) node. 
    #############################################
    def checkNode(self, namespaceURI=None, localName=None):
        '''
            namespaceURI -- namespace of element
            localName -- local name of element
        '''
        namespaceURI = namespaceURI or self.namespaceURI
        localName = localName or self.name
        check = False
        if localName and self.node:
            check = self._dom.isElement(self.node, localName, namespaceURI)
        if not check:
            raise NamespaceError, 'unexpected node type %s, expecting %s' %(self.node, localName)

    def setNode(self, node=None):
        if node:
            if isinstance(node, ElementProxy):
                self.node = node._getNode()
            else:
                self.node = node
        elif self.node:
            node = self._dom.getElement(self.node, self.name, self.namespaceURI, default=None)
            if not node:
                raise NamespaceError, 'cant find element (%s,%s)' %(self.namespaceURI,self.name)
            self.node = node
        else:
            #self.node = self._dom.create(self.node, self.name, self.namespaceURI, default=None)
            self.createDocument(self.namespaceURI, localName=self.name, doctype=None)
        
        self.checkNode()

    #############################################
    # Wrapper Methods for direct DOM Element Node access
    #############################################
    def _getNode(self):
        return self.node

    def _getElements(self):
        return self._dom.getElements(self.node, name=None)

    def _getOwnerDocument(self):
        return self.node.ownerDocument or self.node

    def _getUniquePrefix(self):
        '''I guess we need to resolve all potential prefixes
        because when the current node is attached it copies the 
        namespaces into the parent node.
        '''
        while 1:
            self._indx += 1
            prefix = 'ns%d' %self._indx
            try:
                self._dom.findNamespaceURI(prefix, self._getNode())
            except DOMException, ex:
                break
        return prefix

    def _getPrefix(self, node, nsuri):
        '''
        Keyword arguments:
            node -- DOM Element Node
            nsuri -- namespace of attribute value
        '''
        try:
            if node and (node.nodeType == node.ELEMENT_NODE) and \
                (nsuri == self._dom.findDefaultNS(node)):
                return None
        except DOMException, ex:
            pass
        if nsuri == XMLNS.XML:
            return self._xml_prefix
        if node.nodeType == Node.ELEMENT_NODE:
            for attr in node.attributes.values():
                if attr.namespaceURI == XMLNS.BASE \
                   and nsuri == attr.value:
                        return attr.localName
            else:
                if node.parentNode:
                    return self._getPrefix(node.parentNode, nsuri)
        raise NamespaceError, 'namespaceURI "%s" is not defined' %nsuri

    def _appendChild(self, node):
        '''
        Keyword arguments:
            node -- DOM Element Node
        '''
        if node is None:
            raise TypeError, 'node is None'
        self.node.appendChild(node)

    def _insertBefore(self, newChild, refChild):
        '''
        Keyword arguments:
            child -- DOM Element Node to insert
            refChild -- DOM Element Node 
        '''
        self.node.insertBefore(newChild, refChild)

    def _setAttributeNS(self, namespaceURI, qualifiedName, value):
        '''
        Keyword arguments:
            namespaceURI -- namespace of attribute
            qualifiedName -- qualified name of new attribute value
            value -- value of attribute
        '''
        self.node.setAttributeNS(namespaceURI, qualifiedName, value)

    #############################################
    #General Methods
    #############################################
    def isFault(self):
        '''check to see if this is a soap:fault message.
        '''
        return False

    def getPrefix(self, namespaceURI):
        try:
            prefix = self._getPrefix(node=self.node, nsuri=namespaceURI)
        except NamespaceError, ex:
            prefix = self._getUniquePrefix() 
            self.setNamespaceAttribute(prefix, namespaceURI)
        return prefix

    def getDocument(self):
        return self._getOwnerDocument()

    def setDocument(self, document):
        self.node = document

    def importFromString(self, xmlString):
        doc = self._dom.loadDocument(StringIO(xmlString))
        node = self._dom.getElement(doc, name=None)
        clone = self.importNode(node)
        self._appendChild(clone)

    def importNode(self, node):
        if isinstance(node, ElementProxy):
            node = node._getNode()
        return self._dom.importNode(self._getOwnerDocument(), node, deep=1)

    def loadFromString(self, data):
        self.node = self._dom.loadDocument(StringIO(data))

    def canonicalize(self):
        return Canonicalize(self.node)

    def toString(self):
        return self.canonicalize()

    def createDocument(self, namespaceURI, localName, doctype=None):
        '''If specified must be a SOAP envelope, else may contruct an empty document.
        '''
        prefix = self._soap_env_prefix

        if namespaceURI == self.reserved_ns[prefix]:
            qualifiedName = '%s:%s' %(prefix,localName)
        elif namespaceURI is localName is None:
            self.node = self._dom.createDocument(None,None,None)
            return
        else:
            raise KeyError, 'only support creation of document in %s' %self.reserved_ns[prefix]

        document = self._dom.createDocument(nsuri=namespaceURI, qname=qualifiedName, doctype=doctype)
        self.node = document.childNodes[0]

        #set up reserved namespace attributes
        for prefix,nsuri in self.reserved_ns.items():
            self._setAttributeNS(namespaceURI=self._xmlns_nsuri, 
                qualifiedName='%s:%s' %(self._xmlns_prefix,prefix), 
                value=nsuri)

    #############################################
    #Methods for attributes
    #############################################
    def hasAttribute(self, namespaceURI, localName):
        return self._dom.hasAttr(self._getNode(), name=localName, nsuri=namespaceURI)

    def setAttributeType(self, namespaceURI, localName):
        '''set xsi:type
        Keyword arguments:
            namespaceURI -- namespace of attribute value
            localName -- name of new attribute value

        '''
        self.logger.debug('setAttributeType: (%s,%s)', namespaceURI, localName)
        value = localName
        if namespaceURI:
            value = '%s:%s' %(self.getPrefix(namespaceURI),localName)

        xsi_prefix = self.getPrefix(self._xsi_nsuri)
        self._setAttributeNS(self._xsi_nsuri, '%s:type' %xsi_prefix, value)

    def createAttributeNS(self, namespace, name, value):
        document = self._getOwnerDocument()
        attrNode = document.createAttributeNS(namespace, name, value)

    def setAttributeNS(self, namespaceURI, localName, value):
        '''
        Keyword arguments:
            namespaceURI -- namespace of attribute to create, None is for
                attributes in no namespace.
            localName -- local name of new attribute
            value -- value of new attribute
        ''' 
        prefix = None
        if namespaceURI:
            try:
                prefix = self.getPrefix(namespaceURI)
            except KeyError, ex:
                prefix = 'ns2'
                self.setNamespaceAttribute(prefix, namespaceURI)
        qualifiedName = localName
        if prefix:
            qualifiedName = '%s:%s' %(prefix, localName)
        self._setAttributeNS(namespaceURI, qualifiedName, value)

    def setNamespaceAttribute(self, prefix, namespaceURI):
        '''
        Keyword arguments:
            prefix -- xmlns prefix
            namespaceURI -- value of prefix
        '''
        self._setAttributeNS(XMLNS.BASE, 'xmlns:%s' %prefix, namespaceURI)

    #############################################
    #Methods for elements
    #############################################
    def createElementNS(self, namespace, qname):
        '''
        Keyword arguments:
            namespace -- namespace of element to create
            qname -- qualified name of new element
        '''
        document = self._getOwnerDocument()
        node = document.createElementNS(namespace, qname)
        return ElementProxy(self.sw, node)

    def createAppendSetElement(self, namespaceURI, localName, prefix=None):
        '''Create a new element (namespaceURI,name), append it
           to current node, then set it to be the current node.
        Keyword arguments:
            namespaceURI -- namespace of element to create
            localName -- local name of new element
            prefix -- if namespaceURI is not defined, declare prefix.  defaults
                to 'ns1' if left unspecified.
        '''
        node = self.createAppendElement(namespaceURI, localName, prefix=None)
        node=node._getNode()
        self._setNode(node._getNode())

    def createAppendElement(self, namespaceURI, localName, prefix=None):
        '''Create a new element (namespaceURI,name), append it
           to current node, and return the newly created node.
        Keyword arguments:
            namespaceURI -- namespace of element to create
            localName -- local name of new element
            prefix -- if namespaceURI is not defined, declare prefix.  defaults
                to 'ns1' if left unspecified.
        '''
        declare = False
        qualifiedName = localName
        if namespaceURI:
            try:
                prefix = self.getPrefix(namespaceURI)
            except:
                declare = True
                prefix = prefix or self._getUniquePrefix()
            if prefix: 
                qualifiedName = '%s:%s' %(prefix, localName)
        node = self.createElementNS(namespaceURI, qualifiedName)
        if declare:
            node._setAttributeNS(XMLNS.BASE, 'xmlns:%s' %prefix, namespaceURI)
        self._appendChild(node=node._getNode())
        return node

    def createInsertBefore(self, namespaceURI, localName, refChild):
        qualifiedName = localName
        prefix = self.getPrefix(namespaceURI)
        if prefix: 
            qualifiedName = '%s:%s' %(prefix, localName)
        node = self.createElementNS(namespaceURI, qualifiedName)
        self._insertBefore(newChild=node._getNode(), refChild=refChild._getNode())
        return node

    def getElement(self, namespaceURI, localName):
        '''
        Keyword arguments:
            namespaceURI -- namespace of element
            localName -- local name of element
        '''
        node = self._dom.getElement(self.node, localName, namespaceURI, default=None)
        if node:
            return ElementProxy(self.sw, node)
        return None

    def getAttributeValue(self, namespaceURI, localName):
        '''
        Keyword arguments:
            namespaceURI -- namespace of attribute
            localName -- local name of attribute
        '''
        if self.hasAttribute(namespaceURI, localName):
            attr = self.node.getAttributeNodeNS(namespaceURI,localName)
            return attr.value
        return None

    def getValue(self):
        return self._dom.getElementText(self.node, preserve_ws=True)    

    #############################################
    #Methods for text nodes
    #############################################
    def createAppendTextNode(self, pyobj):
        node = self.createTextNode(pyobj)
        self._appendChild(node=node._getNode())
        return node

    def createTextNode(self, pyobj):
        document = self._getOwnerDocument()
        node = document.createTextNode(pyobj)
        return ElementProxy(self.sw, node)

    #############################################
    #Methods for retrieving namespaceURI's
    #############################################
    def findNamespaceURI(self, qualifiedName):
        parts = SplitQName(qualifiedName)
        element = self._getNode()
        if len(parts) == 1:
            return (self._dom.findTargetNS(element), value)
        return self._dom.findNamespaceURI(parts[0], element)

    def resolvePrefix(self, prefix):
        element = self._getNode()
        return self._dom.findNamespaceURI(prefix, element)

    def getSOAPEnvURI(self):
        return self._soap_env_nsuri

    def isEmpty(self):
        return not self.node



class Collection(UserDict):
    """Helper class for maintaining ordered named collections."""
    default = lambda self,k: k.name
    def __init__(self, parent, key=None):
        UserDict.__init__(self)
        self.parent = weakref.ref(parent)
        self.list = []
        self._func = key or self.default

    def __getitem__(self, key):
        if type(key) is type(1):
            return self.list[key]
        return self.data[key]

    def __setitem__(self, key, item):
        item.parent = weakref.ref(self)
        self.list.append(item)
        self.data[key] = item

    def keys(self):
        return map(lambda i: self._func(i), self.list)

    def items(self):
        return map(lambda i: (self._func(i), i), self.list)

    def values(self):
        return self.list


class CollectionNS(UserDict):
    """Helper class for maintaining ordered named collections."""
    default = lambda self,k: k.name
    def __init__(self, parent, key=None):
        UserDict.__init__(self)
        self.parent = weakref.ref(parent)
        self.targetNamespace = None
        self.list = []
        self._func = key or self.default

    def __getitem__(self, key):
        self.targetNamespace = self.parent().targetNamespace
        if type(key) is types.IntType:
            return self.list[key]
        elif self.__isSequence(key):
            nsuri,name = key
            return self.data[nsuri][name]
        return self.data[self.parent().targetNamespace][key]

    def __setitem__(self, key, item):
        item.parent = weakref.ref(self)
        self.list.append(item)
        targetNamespace = getattr(item, 'targetNamespace', self.parent().targetNamespace)
        if not self.data.has_key(targetNamespace):
            self.data[targetNamespace] = {}
        self.data[targetNamespace][key] = item

    def __isSequence(self, key):
        return (type(key) in (types.TupleType,types.ListType) and len(key) == 2)

    def keys(self):
        keys = []
        for tns in self.data.keys():
            keys.append(map(lambda i: (tns,self._func(i)), self.data[tns].values()))
        return keys

    def items(self):
        return map(lambda i: (self._func(i), i), self.list)

    def values(self):
        return self.list



# This is a runtime guerilla patch for pulldom (used by minidom) so
# that xml namespace declaration attributes are not lost in parsing.
# We need them to do correct QName linking for XML Schema and WSDL.
# The patch has been submitted to SF for the next Python version.

from xml.dom.pulldom import PullDOM, START_ELEMENT
if 1:
    def startPrefixMapping(self, prefix, uri):
        if not hasattr(self, '_xmlns_attrs'):
            self._xmlns_attrs = []
        self._xmlns_attrs.append((prefix or 'xmlns', uri))
        self._ns_contexts.append(self._current_context.copy())
        self._current_context[uri] = prefix or ''

    PullDOM.startPrefixMapping = startPrefixMapping

    def startElementNS(self, name, tagName , attrs):
        # Retrieve xml namespace declaration attributes.
        xmlns_uri = 'http://www.w3.org/2000/xmlns/'
        xmlns_attrs = getattr(self, '_xmlns_attrs', None)
        if xmlns_attrs is not None:
            for aname, value in xmlns_attrs:
                attrs._attrs[(xmlns_uri, aname)] = value
            self._xmlns_attrs = []
        uri, localname = name
        if uri:
            # When using namespaces, the reader may or may not
            # provide us with the original name. If not, create
            # *a* valid tagName from the current context.
            if tagName is None:
                prefix = self._current_context[uri]
                if prefix:
                    tagName = prefix + ":" + localname
                else:
                    tagName = localname
            if self.document:
                node = self.document.createElementNS(uri, tagName)
            else:
                node = self.buildDocument(uri, tagName)
        else:
            # When the tagname is not prefixed, it just appears as
            # localname
            if self.document:
                node = self.document.createElement(localname)
            else:
                node = self.buildDocument(None, localname)

        for aname,value in attrs.items():
            a_uri, a_localname = aname
            if a_uri == xmlns_uri:
                if a_localname == 'xmlns':
                    qname = a_localname
                else:
                    qname = 'xmlns:' + a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            elif a_uri:
                prefix = self._current_context[a_uri]
                if prefix:
                    qname = prefix + ":" + a_localname
                else:
                    qname = a_localname
                attr = self.document.createAttributeNS(a_uri, qname)
                node.setAttributeNodeNS(attr)
            else:
                attr = self.document.createAttribute(a_localname)
                node.setAttributeNode(attr)
            attr.value = value

        self.lastEvent[1] = [(START_ELEMENT, node), None]
        self.lastEvent = self.lastEvent[1]
        self.push(node)

    PullDOM.startElementNS = startElementNS

#
# This is a runtime guerilla patch for minidom so
# that xmlns prefixed attributes dont raise AttributeErrors
# during cloning.
#
# Namespace declarations can appear in any start-tag, must look for xmlns
# prefixed attribute names during cloning.
#
# key (attr.namespaceURI, tag)
# ('http://www.w3.org/2000/xmlns/', u'xsd')   <xml.dom.minidom.Attr instance at 0x82227c4>
# ('http://www.w3.org/2000/xmlns/', 'xmlns')   <xml.dom.minidom.Attr instance at 0x8414b3c>
#
# xml.dom.minidom.Attr.nodeName = xmlns:xsd
# xml.dom.minidom.Attr.value =  = http://www.w3.org/2001/XMLSchema 

if 1:
    def _clone_node(node, deep, newOwnerDocument):
	"""
	Clone a node and give it the new owner document.
	Called by Node.cloneNode and Document.importNode
	"""
	if node.ownerDocument.isSameNode(newOwnerDocument):
	    operation = xml.dom.UserDataHandler.NODE_CLONED
	else:
	    operation = xml.dom.UserDataHandler.NODE_IMPORTED
	if node.nodeType == xml.dom.minidom.Node.ELEMENT_NODE:
	    clone = newOwnerDocument.createElementNS(node.namespaceURI,
						     node.nodeName)
	    for attr in node.attributes.values():
		clone.setAttributeNS(attr.namespaceURI, attr.nodeName, attr.value)

		prefix, tag = xml.dom.minidom._nssplit(attr.nodeName)
		if prefix == 'xmlns':
		    a = clone.getAttributeNodeNS(attr.namespaceURI, tag)
		elif prefix:
		    a = clone.getAttributeNodeNS(attr.namespaceURI, tag)
		else:
		    a = clone.getAttributeNodeNS(attr.namespaceURI, attr.nodeName)
		a.specified = attr.specified

	    if deep:
		for child in node.childNodes:
		    c = xml.dom.minidom._clone_node(child, deep, newOwnerDocument)
		    clone.appendChild(c)
	elif node.nodeType == xml.dom.minidom.Node.DOCUMENT_FRAGMENT_NODE:
	    clone = newOwnerDocument.createDocumentFragment()
	    if deep:
		for child in node.childNodes:
		    c = xml.dom.minidom._clone_node(child, deep, newOwnerDocument)
		    clone.appendChild(c)

	elif node.nodeType == xml.dom.minidom.Node.TEXT_NODE:
	    clone = newOwnerDocument.createTextNode(node.data)
	elif node.nodeType == xml.dom.minidom.Node.CDATA_SECTION_NODE:
	    clone = newOwnerDocument.createCDATASection(node.data)
	elif node.nodeType == xml.dom.minidom.Node.PROCESSING_INSTRUCTION_NODE:
	    clone = newOwnerDocument.createProcessingInstruction(node.target,
								 node.data)
	elif node.nodeType == xml.dom.minidom.Node.COMMENT_NODE:
	    clone = newOwnerDocument.createComment(node.data)
	elif node.nodeType == xml.dom.minidom.Node.ATTRIBUTE_NODE:
	    clone = newOwnerDocument.createAttributeNS(node.namespaceURI,
						       node.nodeName)
	    clone.specified = True
	    clone.value = node.value
	elif node.nodeType == xml.dom.minidom.Node.DOCUMENT_TYPE_NODE:
	    assert node.ownerDocument is not newOwnerDocument
	    operation = xml.dom.UserDataHandler.NODE_IMPORTED
	    clone = newOwnerDocument.implementation.createDocumentType(
		node.name, node.publicId, node.systemId)
	    clone.ownerDocument = newOwnerDocument
	    if deep:
		clone.entities._seq = []
		clone.notations._seq = []
		for n in node.notations._seq:
		    notation = xml.dom.minidom.Notation(n.nodeName, n.publicId, n.systemId)
		    notation.ownerDocument = newOwnerDocument
		    clone.notations._seq.append(notation)
		    if hasattr(n, '_call_user_data_handler'):
			n._call_user_data_handler(operation, n, notation)
		for e in node.entities._seq:
		    entity = xml.dom.minidom.Entity(e.nodeName, e.publicId, e.systemId,
				    e.notationName)
		    entity.actualEncoding = e.actualEncoding
		    entity.encoding = e.encoding
		    entity.version = e.version
		    entity.ownerDocument = newOwnerDocument
		    clone.entities._seq.append(entity)
		    if hasattr(e, '_call_user_data_handler'):
			e._call_user_data_handler(operation, n, entity)
	else:
	    # Note the cloning of Document and DocumentType nodes is
	    # implemenetation specific.  minidom handles those cases
	    # directly in the cloneNode() methods.
	    raise xml.dom.NotSupportedErr("Cannot clone node %s" % repr(node))

	# Check for _call_user_data_handler() since this could conceivably
	# used with other DOM implementations (one of the FourThought
	# DOMs, perhaps?).
	if hasattr(node, '_call_user_data_handler'):
	    node._call_user_data_handler(operation, node, clone)
	return clone

    xml.dom.minidom._clone_node = _clone_node

