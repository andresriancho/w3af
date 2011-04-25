'''
wsdlParser.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException

try:
    import extlib.SOAPpy.SOAPpy as SOAPpy
    om.out.debug('wsdlParser is using the bundled SOAPpy library')
except ImportError:
    try:
        import SOAPpy
        om.out.debug('wsdlParser is using the systems SOAPpy library')
    except ImportError:
        raise w3afException('You have to install SOAPpy lib.')

import xml.parsers.expat as expat


class wsdlParser:
    '''
    This class parses WSDL documents.

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__( self ):
        self._proxy = None
        
    def is_WSDL(self, data):
        '''
        This is not a 100% accurate test, the real WSDL parsing is performed
        in "SOAPpy.WSDL.Proxy( xmlData )". This test was mostly added to enhance
        framework's performance.
        
        @parameter data: A string that might represent a WSDL
        @return: True if the data parameter is a WSDL document.
        '''
        if '<definitions' in data[:150] or '<wsdl:definitions' in data[:150]:
            return True
        else:
            return False
        
    def setWsdl( self, xmlData ):
        '''
        @parameter xmlData: The WSDL to parse. At this point, we really don't know if it really is a WSDL document.
        '''
        if not self.is_WSDL(xmlData):
            raise w3afException('The body content is not a WSDL.')
        else:
            try:
                self._proxy = SOAPpy.WSDL.Proxy( xmlData )
            except expat.ExpatError:
                raise w3afException('The body content is not a WSDL.')
            except Exception, e:
                msg = 'The body content is not a WSDL.'
                msg += ' Unhandled exception in SOAPpy: "' + str(e) + '".'
                om.out.debug(msg)
                raise w3afException(msg)
        
    def getNS( self, method ):
        '''
        @method: The method name
        @return: The namespace of the WSDL
        '''
        if method in self._proxy.methods.keys():
            return str(self._proxy.methods[ method ].namespace)
        else:
            raise w3afException('Unknown method name.')
            
    def getAction( self, methodName ):
        '''
        @methodName: The method name
        @return: The soap action.
        '''
        if methodName in self._proxy.methods.keys():
            return str(self._proxy.methods[ methodName ].soapAction)
        else:
            raise w3afException('Unknown method name.')
    
    def getLocation( self, methodName ):
        '''
        @methodName: The method name
        @return: The soap action.
        '''
        if methodName in self._proxy.methods.keys():
            return str(self._proxy.methods[ methodName ].location)
        else:
            raise w3afException('Unknown method name.') 
    
    def getMethods( self ):
        '''
        @wsdlDocument: The XML document
        @return: The methods defined in the WSDL
        '''
        res = []
        for methodName in self._proxy.methods.keys():
            remoteMethodObject = remoteMethod()
            remoteMethodObject.setMethodName( str( methodName ) )
            remoteMethodObject.setNamespace( self.getNS( methodName ) )
            remoteMethodObject.setAction( self.getAction( methodName ) )
            remoteMethodObject.setLocation( self.getLocation( methodName ) )
            remoteMethodObject.setParameters(
                                            self.getMethodParams( methodName ) )
            res.append( remoteMethodObject )
        return res
    
    def getMethodParams( self,  methodName ):
        '''
        @methodName: The method name
        @return: The soap action.
        '''
        if not methodName in self._proxy.methods.keys():
            raise w3afException('Unknown method name.')
        else:
            res = []
            inps = self._proxy.methods[ methodName ].inparams
            for param in range(len(inps)):
                details = inps[param]
                parameterObject = parameter()
                parameterObject.setName( str(details.name) )
                parameterObject.setType( str(details.type[1]) )
                parameterObject.setNs( str(details.type[0]) )
                res.append( parameterObject )
            return res


class parameter:
    '''
    This class represents a parameter in a SOAP call.
    '''
    def __init__( self ):
        self._type = ''
        self._name = ''
        self._ns = ''

    def getName( self ):
        return self._name
    
    def setName( self, name ):
        self._name = name
    
    def getNs( self ):
        return self._ns
    
    def setNs( self, namespace ):
        self._ns = namespace

    def getType( self ):
        return self._type
    
    def setType( self, paramType ):
        self._type = paramType

class remoteMethod:
    '''
    This class represents a remote method call.
    '''
    def __init__( self ):
        self._name = ''
        self._action = ''
        self._namespace = ''
        self._inParameters = None
        self._location = ''
        
    def getMethodName( self ):
        return self._name
        
    def setMethodName( self, name ):
        self._name = name
    
    def getAction( self ):
        return self._action
        
    def setAction( self, action ):
        self._action = action
    
    def getLocation( self ):
        return self._location
        
    def setLocation( self, location ):
        self._location = location
    
    def getNamespace( self ):
        return self._namespace
        
    def setNamespace( self, namespace ):
        self._namespace = namespace
        
    def getParameters( self ):
        return self._inParameters
        
    def setParameters( self, inparams ):
        self._inParameters = inparams
    
