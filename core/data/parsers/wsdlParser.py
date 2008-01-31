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
except:
    try:
        import SOAPpy
        om.out.debug('wsdlParser is using the systems SOAPpy library')
    except:
        raise w3afException('You have to install SOAPpy lib.')

'''
This module parses WSDL documents.

@author: Andres Riancho ( andres.riancho@gmail.com )
'''
class wsdlParser:
    
    def __init__( self ):
        self._proxy = None
        
    def setWsdl( self, xmlData ):
        try:
            self._proxy = SOAPpy.WSDL.Proxy( xmlData )
        except:
            raise w3afException('The document aint a WSDL document.')
        
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
        for i in self._proxy.methods.keys():
            rm = remoteMethod()
            rm.setMethodName( str( i ) )
            rm.setNamespace( self.getNS( i ) )
            rm.setAction( self.getAction( i ) )
            rm.setLocation( self.getLocation( i ) )
            rm.setParameters( self.getMethodParams( i ) )
            res.append( rm )
        return res
    
    def getMethodParams( self,  method ):
        '''
        @methodName: The method name
        @return: The soap action.
        '''
        if method in self._proxy.methods.keys():
            res = []
            inps = self._proxy.methods[ method ].inparams
            for param in range(len(inps)):
                details = inps[param]
                p = parameter()
                p.setName( str(details.name) )
                p.setType( str(details.type[1]) )
                p.setNs( str(details.type[0]) )
                res.append( p )
            return res
        else:
            raise w3afException('Unknown method name.')

            
class parameter:
    def __init__( self ):
        self._type = ''
        self._name = ''
        self._ns = ''

    def getName( self ): return self._name
    def setName( self, n ): self._name = n
    
    def getNs( self ): return self._ns
    def setNs( self, n ): self._ns = n

    def getType( self ): return self._type
    def setType( self, t ): self._type = t

class remoteMethod:
    def __init__( self ):
        self._name = ''
        self._action = ''
        self._namespace = ''
        self._inParameters = None
        self._location = ''
        
    def getMethodName( self ): return self._name
    def setMethodName( self, n ): self._name = n
    
    def getAction( self ): return self._action
    def setAction( self, a ): self._action = a
    
    def getLocation( self ): return self._location
    def setLocation( self, l ): self._location = l
    
    def getNamespace( self ): return self._namespace
    def setNamespace( self, n ): self._namespace = n
        
    def getParameters( self ): return self._inParameters
    def setParameters( self, o ): self._inParameters = o
    
