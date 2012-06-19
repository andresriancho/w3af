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
import threading
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.kb.shell as shell

from multiprocessing.managers import BaseManager

__all__ = ['KnowledgeBaseServer','KnowledgeBaseClient','kb']


class KnowledgeBase:
    '''
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can talk to each other.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    def __init__(self):
        self._kb = {}
        self._kb_lock = threading.RLock()

    def save( self, callingInstance, variableName, value ):
        '''
        This method saves the variableName value to a dict.
        '''
        name = self._get_real_name(callingInstance)
        
        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[ name ] = {variableName: value}
            else:
                self._kb[ name ][ variableName ] = value
        
    def append( self, callingInstance, variableName, value ):
        '''
        This method appends the variableName value to a dict.
        '''
        name = self._get_real_name(callingInstance)

        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[name] = {variableName: [value]}
            else:
                if variableName in self._kb[ name ] :
                    self._kb[name][variableName].append(value)
                else:
                    self._kb[name][variableName] = [value]
        
    def getData( self, pluginWhoSavedTheData, variableName=None ):
        '''
        @parameter pluginWhoSavedTheData: The plugin that saved the data to the
                                          kb.info Typically the name of the plugin,
                                          but could also be the plugin instance.
        
        @parameter variableName: The name of the variables under which the vuln 
                                 objects were saved. Typically the same name of
                                 the plugin, or something like "vulns", "errors",
                                 etc. In most cases this is NOT None. When set 
                                 to None, a dict with all the vuln objects found
                                 by the pluginWhoSavedTheData is returned.
        
        @return: Returns the data that was saved by another plugin.
        '''
        name = self._get_real_name(pluginWhoSavedTheData)
            
        res = []
        
        with self._kb_lock:
            if name not in self._kb.keys():
                res = []
            else:
                if variableName is None:
                    res = self._kb[name]
                elif variableName not in self._kb[name].keys():
                    res = []
                else:
                    res = self._kb[name][variableName]
                    
        return res

    def getAllEntriesOfClass(self, klass):
        '''
        @return: A list of all objects of class == klass that are saved in the kb.
        '''
        res = []
        
        with self._kb_lock:
            for pdata in self._kb.values():
                for vals in pdata.values():
                    if not isinstance(vals, list):
                        continue
                    for v in vals:
                        if isinstance(v, klass):
                            res.append(v)
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
    
    def cleanup(self):
        '''
        Cleanup internal data.
        '''
        with self._kb_lock:
            self._kb.clear()
    
    def _get_real_name(self, data):
        if isinstance( data, basestring ):
            return data
        else:
            return data.getName()

internal_kb = KnowledgeBase()

kb = KnowledgeBase()

class KnowledgeBaseServer(threading.Thread):

    class KnowledgeBaseManagerServer(BaseManager): pass
    KnowledgeBaseManagerServer.register('getData', callable=internal_kb.getData)
    KnowledgeBaseManagerServer.register('cleanup', callable=internal_kb.cleanup)
    KnowledgeBaseManagerServer.register('dump', callable=internal_kb.dump)
    KnowledgeBaseManagerServer.register('getAllShells', callable=internal_kb.getAllShells)
    KnowledgeBaseManagerServer.register('getAllInfos', callable=internal_kb.getAllInfos)
    KnowledgeBaseManagerServer.register('getAllVulns', callable=internal_kb.getAllVulns)
    KnowledgeBaseManagerServer.register('getAllEntriesOfClass', callable=internal_kb.getAllEntriesOfClass)
    KnowledgeBaseManagerServer.register('append', callable=internal_kb.append)
    KnowledgeBaseManagerServer.register('save', callable=internal_kb.save)
    
    def run(self):
        m = self.KnowledgeBaseManagerServer(address=('127.0.0.2', 50000), authkey='letmein')
        s = m.get_server()
        s.serve_forever()
    

class KnowledgeBaseClient(object):

    class KnowledgeBaseManagerClient(BaseManager): pass
    KnowledgeBaseManagerClient.register('getData')
    KnowledgeBaseManagerClient.register('cleanup')
    KnowledgeBaseManagerClient.register('dump')
    KnowledgeBaseManagerClient.register('getAllShells')
    KnowledgeBaseManagerClient.register('getAllInfos')
    KnowledgeBaseManagerClient.register('getAllVulns')
    KnowledgeBaseManagerClient.register('getAllEntriesOfClass')
    KnowledgeBaseManagerClient.register('append')
    KnowledgeBaseManagerClient.register('save')
    
    def start(self):
        client = self.KnowledgeBaseManagerClient(address=('127.0.0.2', 50000), authkey='letmein')
        client.connect()
        global kb
        kb = client
        return client
        
        