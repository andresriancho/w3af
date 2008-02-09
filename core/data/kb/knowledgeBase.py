'''
knowledgeBase.py

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

import os,sys
from core.controllers.w3afException import w3afException
import thread
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.kb.shell as shell

class knowledgeBase:
    '''
    This class saves the data that is sent to it by plugins. It is the only way in which
    plugins can talk to each other.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self._kb = {}
        self.createLock()
    
    def destroyLock( self ):
        self._kbLock = None
    
    def createLock( self ):
        self._kbLock = thread.allocate_lock()
        
    def save( self, callingInstance, variableName, value ):
        '''
        This method saves the variableName value to a dict.
        '''
        if isinstance( callingInstance, basestring ):
            name = callingInstance
        else:
            name = callingInstance.getName()
        
        if self.getLock():
            if name not in self._kb.keys():
                self._kb[ name ] = {variableName: value}
            else:
                self._kb[ name ][ variableName ] = value
            self.releaseLock()
        
    def append( self, callingInstance, variableName, value ):
        '''
        This method appends the variableName value to a dict.
        '''
        if isinstance( callingInstance, basestring ):
            name = callingInstance
        else:
            name = callingInstance.getName()
        
        if self.getLock():
            if name not in self._kb.keys():
                self._kb[ name ] = {variableName:[value,]}
            else:
                if variableName in self._kb[ name ] :
                    self._kb[ name ][ variableName ].extend( [value,] )
                else:
                    self._kb[ name ][ variableName ] = [value,]
            self.releaseLock()
        
    def getData( self, pluginWhoSavedTheData, variableName ):
        '''
        @return: Returns the data that was saved by another plugin.
        '''
        res = []
        if self.getLock():
            if pluginWhoSavedTheData not in self._kb.keys():
                res = []
            else:
                if variableName not in self._kb[pluginWhoSavedTheData].keys():
                    res = []
                else:
                    res = self._kb[pluginWhoSavedTheData][variableName]
            self.releaseLock()
        return res
    
    def getLock(self):
        try:
            self._kbLock.acquire()
        except:
            return False
        else:
            return True
    
    def releaseLock(self):
        try:
            self._kbLock.release()
        except:
            return False
        else:
            return True

    def getAllEntriesOfClass( self, klass ):
        '''
        @return: A list of all objects of class == klass that are saved in the kb.
        '''
        res = []
        if self.getLock():
            for pluginName in self._kb:
                for savedName in self._kb[ pluginName ]:
                    if isinstance( self._kb[ pluginName ][ savedName ], list ):
                        for i in self._kb[ pluginName ][ savedName ]:
                            if isinstance( i, klass ):
                                res.append( i )
            self.releaseLock()
        return res
    
    def getAllVulns( self ):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.getAllEntriesOfClass( vuln.vuln )
    
    def getAllInfos( self ):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.getAllEntriesOfClass( info.info )
    
    def getAllShells( self ):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.getAllEntriesOfClass( shell.shell )
        
    def dump(self):
        return self._kb
        
kb = knowledgeBase()
