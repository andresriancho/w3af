'''
baseOutputPlugin.py

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

from core.controllers.basePlugin.basePlugin import basePlugin
import inspect

class baseOutputPlugin(basePlugin):
    '''
    This is the base class for data output, all output plugins should inherit from it and implement the following methods :
        1. debug( message, verbose )
        2. information( message, verbose )
        3. error( message, verbose )
        4. vulnerability( message, verbose )

    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def getType( self ):
        return 'output'

    def __init__(self):
        basePlugin.__init__( self )
        self.verbosity = 0
        
    def debug(self, message ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method debug' )

    def information(self, message, verbose):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for information messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method information' )

    def error(self, message, verbose):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for error messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method error' )

    def vulnerability(self, message ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for vulnerability messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method vulnerability' )

    def console(self, message ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action for vulnerability messages.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method console' )
    
    def logHttp(self, request, response ):
        '''
        This method is called from the output managerobject. The OM object was called from a plugin
        or from the framework. This method should take an action to log HTTP requests and responses.
        
        @return: No value is returned.
        '''
        raise w3afException('Plugin is not implementing required method logHttp.' )
        
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptionsXML()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        if 'verbosity' in OptionList.keys():
            self.verbosity = OptionList['verbosity']
        

    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/display.xsd
        
        This method MUST be implemented on every plugin. 
        
        @return: XML String
        @see: core/display.xsd
        '''
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="verbosity">\
                <default>0</default>\
                <desc>Verbosity level for this plugin.</desc>\
                <type>integer</type>\
            </Option>\
        </OptionList>\
        '
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be 
        runned before the current one.
        '''
        return []

    def getCaller( self, whatStackItem=4 ):
        '''
        What I'm going to do is to:
            - inspect the stack and try to find a reference to a plugin
            - if a plugin is the caller, then i'll return something like audit.xss
            - if no plugin is in the caller stack, i'll return the stack item specified by whatStackItem
        
        Maybe you are asking yourself why whatStackItem == 4, well, this is why:
            I know that getCaller method will be in the stack
            I also know that the method that calls getCaller will be in the stack
            I also know that the om.out.XYZ method will be in the stack
            That's 3... so... number 4 is the one that really called me.
        
        @return: The caller of the om.out.XYZ method; this is used to make output more readable.
        '''
        theStack = inspect.stack()
        
        found = False
        for item in theStack:
            if item[1].startswith('plugins/'):
                found = True
                break
        
        if found:
            # Now I have the caller item from the stack, I want to do some things with it...        
            res = item[1].replace('plugins/','')
            res = res.replace('/','.')
            res = res.replace('.py','')
        else:
            # From the unknown caller, I just need the name of the function
            item = theStack[ whatStackItem ]
            res = item[1].split('/')[-1:][0]
            res = res.replace('.py','')
        
        return res
        
    def getMessageCache(self):
        '''
        Ouput plugins with caches should implement this method.
        Used in the webUI.
        '''
        return {}
