"""Parse web services description language to get SOAP methods.

Rudimentary support."""

ident = '$Id: WSDL.py,v 1.11 2005/02/21 20:16:15 warnes Exp $'
from version import __version__

import wstools
from Client import SOAPProxy, SOAPAddress
from Config import Config
import urllib

class Proxy:
    """WSDL Proxy.
    
    SOAPProxy wrapper that parses method names, namespaces, soap actions from
    the web service description language (WSDL) file passed into the
    constructor.  The WSDL reference can be passed in as a stream, an url, a
    file name, or a string.

    Loads info into self.methods, a dictionary with methodname keys and values
    of WSDLTools.SOAPCallinfo.

    For example,
    
        url = 'http://www.xmethods.org/sd/2001/TemperatureService.wsdl'
        wsdl = WSDL.Proxy(url)
        print len(wsdl.methods)          # 1
        print wsdl.methods.keys()        # getTemp


    See WSDLTools.SOAPCallinfo for more info on each method's attributes.
    """

    def __init__(self, wsdlsource, config=Config, **kw ):

        reader = wstools.WSDLTools.WSDLReader()
        self.wsdl = None

        # From Mark Pilgrim's "Dive Into Python" toolkit.py--open anything.
        if self.wsdl is None and hasattr(wsdlsource, "read"):
            #print 'stream'
            self.wsdl = reader.loadFromStream(wsdlsource)

        # NOT TESTED (as of April 17, 2003)
        #if self.wsdl is None and wsdlsource == '-':
        #    import sys
        #    self.wsdl = reader.loadFromStream(sys.stdin)
        #    print 'stdin'

        if self.wsdl is None:
            try: 
                file(wsdlsource)
                self.wsdl = reader.loadFromFile(wsdlsource)
                #print 'file'
            except (IOError, OSError): 
                pass

        if self.wsdl is None:
            try:
                stream = urllib.urlopen(wsdlsource)
                self.wsdl = reader.loadFromStream(stream, wsdlsource)
            except (IOError, OSError): pass

        if self.wsdl is None:
            import StringIO
            self.wsdl = reader.loadFromString(str(wsdlsource))
            #print 'string'

        # Package wsdl info as a dictionary of remote methods, with method name
        # as key (based on ServiceProxy.__init__ in ZSI library).
        self.methods = {}
        service = self.wsdl.services[0]
        port = service.ports[0]
        name = service.name
        binding = port.getBinding()
        portType = binding.getPortType()
        for operation in portType.operations:
            callinfo = wstools.WSDLTools.callInfoFromWSDL(port, operation.name)
            self.methods[callinfo.methodName] = callinfo

        self.soapproxy = SOAPProxy('http://localhost/dummy.webservice',
                                   config=config, **kw)

    def __str__(self): 
        s = ''
        for method in self.methods.values():
            s += str(method)
        return s

    def __getattr__(self, name):
        """Set up environment then let parent class handle call.

        Raises AttributeError is method name is not found."""

        if not self.methods.has_key(name): raise AttributeError, name

        callinfo = self.methods[name]
        self.soapproxy.proxy = SOAPAddress(callinfo.location)
        self.soapproxy.namespace = callinfo.namespace
        self.soapproxy.soapaction = callinfo.soapAction
        return self.soapproxy.__getattr__(name)

    def show_methods(self):
        for key in self.methods.keys():
            method = self.methods[key]
            print "Method Name:", key.ljust(15)
            print
            inps = method.inparams
            for parm in range(len(inps)):
                details = inps[parm]
                print "   In #%d: %s  (%s)" % (parm, details.name, details.type)
            print
            outps = method.outparams
            for parm in range(len(outps)):
                details = outps[parm]
                print "   Out #%d: %s  (%s)" % (parm, details.name, details.type)
            print

