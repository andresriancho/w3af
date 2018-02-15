"""
wsdl.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import xml.parsers.expat as expat

import SOAPpy

import w3af.core.controllers.output_manager as om
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.parsers.doc.url import URL


class WSDLParser(object):
    """
    This class parses WSDL documents.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        self._proxy = None

    def is_WSDL(self, data):
        """
        This is not a 100% accurate test, the real WSDL parsing is performed
        in "SOAPpy.WSDL.Proxy( xmlData )". This test was mostly added to
        enhance framework's performance.

        :param data: A string that might represent a WSDL
        :return: True if the data parameter is a WSDL document.
        """
        return False
        if '<definitions' in data[:150] or '<wsdl:definitions' in data[:150]:
            return True
        else:
            return False

    def set_wsdl(self, xmlData):
        """
        :param xmlData: The WSDL to parse. At this point, we really don't know
                        if it really is a WSDL document.
        """
        if not self.is_WSDL(xmlData):
            raise BaseFrameworkException('The body content is not a WSDL.')
        else:
            try:
                self._proxy = SOAPpy.WSDL.Proxy(xmlData)
            except expat.ExpatError:
                raise BaseFrameworkException('The body content is not a WSDL.')
            except Exception, e:
                msg = 'The body content is not a WSDL.'
                msg += ' Unhandled exception in SOAPpy: "' + str(e) + '".'
                om.out.debug(msg)
                raise BaseFrameworkException(msg)

    def get_ns(self, method):
        """
        @method: The method name
        :return: The namespace of the WSDL
        """
        if method in self._proxy.methods.keys():
            return str(self._proxy.methods[method].namespace)
        else:
            raise BaseFrameworkException('Unknown method name.')

    def get_action(self, methodName):
        """
        @methodName: The method name
        :return: The soap action as a URL object
        """
        if methodName in self._proxy.methods.keys():
            action_str = str(self._proxy.methods[methodName].soapAction)
            action_url = URL(action_str)
            return action_url
        else:
            raise BaseFrameworkException('Unknown method name.')

    def get_location(self, methodName):
        """
        @methodName: The method name
        :return: The soap action.
        """
        if methodName in self._proxy.methods.keys():
            location_str = str(self._proxy.methods[methodName].location)
            location_url = URL(location_str)
            return location_url
        else:
            raise BaseFrameworkException('Unknown method name.')

    def get_methods(self):
        """
        @wsdlDocument: The XML document
        :return: The methods defined in the WSDL
        """
        res = []
        for methodName in self._proxy.methods.keys():
            remoteMethodObject = remoteMethod()
            remoteMethodObject.set_methodName(str(methodName))
            remoteMethodObject.set_namespace(self.get_ns(methodName))
            remoteMethodObject.set_action(self.get_action(methodName))
            remoteMethodObject.set_location(self.get_location(methodName))
            remoteMethodObject.set_parameters(
                self.get_methodParams(methodName))
            res.append(remoteMethodObject)
        return res

    def get_methodParams(self, methodName):
        """
        @methodName: The method name
        :return: The soap action.
        """
        if not methodName in self._proxy.methods.keys():
            raise BaseFrameworkException('Unknown method name.')
        else:
            res = []
            inps = self._proxy.methods[methodName].inparams
            for param in xrange(len(inps)):
                details = inps[param]
                parameterObject = parameter()
                parameterObject.set_name(str(details.name))
                parameterObject.set_type(str(details.type[1]))
                parameterObject.set_ns(str(details.type[0]))
                res.append(parameterObject)
            return res


class parameter:
    """
    This class represents a parameter in a SOAP call.
    """
    def __init__(self):
        self._type = ''
        self._name = ''
        self._ns = ''

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_ns(self):
        return self._ns

    def set_ns(self, namespace):
        self._ns = namespace

    def get_type(self):
        return self._type

    def set_type(self, paramType):
        self._type = paramType


class remoteMethod:
    """
    This class represents a remote method call.
    """
    def __init__(self):
        self._name = ''
        self._action = ''
        self._namespace = ''
        self._inParameters = None
        self._location = ''

    def get_methodName(self):
        return self._name

    def set_methodName(self, name):
        self._name = name

    def get_action(self):
        return self._action

    def set_action(self, action):
        self._action = action

    def get_location(self):
        return self._location

    def set_location(self, location):
        self._location = location

    def get_namespace(self):
        return self._namespace

    def set_namespace(self, namespace):
        self._namespace = namespace

    def get_parameters(self):
        return self._inParameters

    def set_parameters(self, inparams):
        self._inParameters = inparams
