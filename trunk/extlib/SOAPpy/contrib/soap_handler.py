
import http_server
from SOAPpy.SOAP import *
Fault = faultType
import string, sys

Config = SOAPConfig(debug=1)

class soap_handler:
    def __init__(self, encoding='UTF-8', config=Config, namespace=None):
        self.namespace          = namespace
        self.objmap             = {}
        self.funcmap            = {}
        self.config = config
        self.encoding = encoding

    def match (self, request):
        return 1

    def handle_request (self, request):
        [path, params, query, fragment] = request.split_uri()
        if request.command == 'post':
            request.collector = collector(self, request)
        else:
            request.error(400)

    def continue_request(self, data, request):
        # Everthing that follows is cripped from do_POST().
        if self.config.debug:
            print "\n***RECEIVING***\n", data, "*" * 13 + "\n"
            sys.stdout.flush()

        try:
            r, header, body = parseSOAPRPC(data, header=1, body=1)
    
            method = r._name
            args   = r._aslist
            kw     = r._asdict
    
            ns = r._ns
            resp = ""
            # For faults messages
            if ns:
                nsmethod = "%s:%s" % (ns, method)
            else:
                nsmethod = method
    
            try:
                # First look for registered functions
                if self.funcmap.has_key(ns) and \
                   self.funcmap[ns].has_key(method):
                    f = self.funcmap[ns][method]
                else: # Now look at registered objects
                    # Check for nested attributes
                    if method.find(".") != -1:
                        t = self.objmap[ns]
                        l = method.split(".")
                        for i in l:
                            t = getattr(t,i)
                        f = t
                    else:
                        f = getattr(self.objmap[ns], method)
            except:
                if self.config.debug:
                    import traceback
                    traceback.print_exc ()
                    
                resp = buildSOAP(Fault("%s:Client" % NS.ENV_T,
                   "No method %s found" % nsmethod,
                   "%s %s" % tuple(sys.exc_info()[0:2])),
                   encoding = self.encoding, config = self.config)
                status = 500
            else:
                try:
                    # If it's wrapped to indicate it takes keywords
                    # send it keywords
                    if header:
                        x = HeaderHandler(header)
    
                    if isinstance(f,MethodSig):
                        c = None
                        if f.context:  # Build context object
                           c = SOAPContext(header, body, d, self.connection, self.headers,
                                       self.headers["soapaction"])
    
                        if f.keywords:
                            tkw = {}
                            # This is lame, but have to de-unicode keywords
                            for (k,v) in kw.items():
                                tkw[str(k)] = v
                            if c:
                                tkw["_SOAPContext"] = c
                            fr = apply(f,(),tkw)
                        else:
                            if c:
                                fr = apply(f,args,{'_SOAPContext':c})
                            else:
                                fr = apply(f,args,{})
                    else:
                        fr = apply(f,args,{})
                    if type(fr) == type(self) and isinstance(fr, voidType):
                        resp = buildSOAP(kw = {'%sResponse' % method:fr},
                            encoding = self.encoding,
                            config = self.config)
                    else:
                        resp = buildSOAP(kw =
                            {'%sResponse' % method:{'Result':fr}},
                            encoding = self.encoding,
                            config = self.config)
                except Fault, e:
                    resp = buildSOAP(e, config = self.config)
                    status = 500
                except:
                    if self.config.debug:
                        import traceback
                        traceback.print_exc ()
    
                    resp = buildSOAP(Fault("%s:Server" % NS.ENV_T, \
                       "Method %s failed." % nsmethod,
                       "%s %s" % tuple(sys.exc_info()[0:2])),
                       encoding = self.encoding,
                       config = self.config)
                    status = 500
                else:
                    status = 200
        except Fault,e:
            resp = buildSOAP(e, encoding = self.encoding,
                config = self.config)
            status = 500
        except:
            # internal error, report as HTTP server error
            if self.config.debug:
                import traceback
                traceback.print_exc ()
            request.error(500)
            #self.send_response(500)
            #self.end_headers()
        else:
            request['Content-Type'] = 'text/xml; charset="%s"' % self.encoding
            request.push(resp)
            request.done()
            # got a valid SOAP response
            #self.send_response(status)
            #self.send_header("Content-type",
            #    'text/xml; charset="%s"' % self.encoding)
            #self.send_header("Content-length", str(len(resp)))
            #self.end_headers()

        if self.config.debug:
            print "\n***SENDING***\n", resp, "*" * 13 + "\n"
            sys.stdout.flush()

        """
        # We should be able to shut down both a regular and an SSL
        # connection, but under Python 2.1, calling shutdown on an
        # SSL connections drops the output, so this work-around.
        # This should be investigated more someday.

        if self.config.SSLserver and \
            isinstance(self.connection, SSL.Connection):
            self.connection.set_shutdown(SSL.SSL_SENT_SHUTDOWN |
                SSL.SSL_RECEIVED_SHUTDOWN)
        else:
            self.connection.shutdown(1)
        """

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
        


class collector:
    "gathers input for POST and PUT requests"

    def __init__ (self, handler, request):

        self.handler = handler
        self.request = request
        self.data = ''

        # make sure there's a content-length header
        cl = request.get_header ('content-length')

        if not cl:
            request.error (411)
        else:
            cl = string.atoi (cl)
            # using a 'numeric' terminator
            self.request.channel.set_terminator (cl)

    def collect_incoming_data (self, data):
        self.data = self.data + data

    def found_terminator (self):
        # set the terminator back to the default
        self.request.channel.set_terminator ('\r\n\r\n')
        self.handler.continue_request (self.data, self.request)


if __name__ == '__main__':

    import asyncore
    import http_server

    class Thing:
    
        def badparam(self, param):
            if param == 'good param':
                return 1
            else:
                return Fault(faultstring='bad param')
    
        def dt(self, aDateTime):
            return aDateTime

    thing = Thing()
    soaph = soap_handler()
    soaph.registerObject(thing)
    
    hs = http_server.http_server('', 10080)
    hs.install_handler(soaph)
    
    asyncore.loop()

