'''
knowledge_base.py

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
import cPickle

from core.data.fuzzer.utils import rand_alpha
from core.data.db.dbms import get_default_persistent_db_instance
from core.data.db.disk_set import DiskSet
from core.data.parsers.url import URL
from core.data.request.fuzzable_request import FuzzableRequest
from core.data.kb.vuln import Vuln
from core.data.kb.info import Info
from core.data.kb.shell import Shell


class BasicKnowledgeBase(object): 
    '''
    This is a base class from which all implementations of KnowledgeBase will
    inherit. It has the basic utility methods that will be used.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        self._kb_lock = threading.RLock()
    
        self.FILTERS = {'URL': self.filter_url,
                        'VAR': self.filter_var}
        
    def append_uniq(self, location_a, location_b, info_inst, filter_by='VAR'):
        '''
        Append to a location in the KB if and only if there it no other
        vulnerability in the same location for the same URL and parameter.

        Does this in a thread-safe manner.

        @param filter_by: One of 'VAR' of 'URL'. Only append to the kb in
                          (location_a, location_b) if there is NO OTHER info
                          in that location with the same:
                              - 'VAR': URL,Variable,DataContainer.keys()
                              - 'URL': URL

        @return: True if the vuln was added. False if there was already a
                 vulnerability in the KB location with the same URL and
                 parameter.
        '''
        if not isinstance(info_inst, Info):
            raise ValueError('append_uniq requires an info object as parameter.')
        
        filter_function = self.FILTERS.get(filter_by, None)
        
        if filter_function is None:
            raise ValueError('append_uniq only knows about URL or VAR filters.')

        with self._kb_lock:
            
            if filter_function(location_a, location_b, info_inst):
                self.append(location_a, location_b, info_inst)
                return True
            
            return False

    def filter_url(self, location_a, location_b, info_inst):
        '''
        @return: True if there is no other info in (location_a, location_b)
                 with the same URL as the info_inst.
        '''
        for saved_vuln in self.get(location_a, location_b):
            if saved_vuln.get_url() == info_inst.get_url():
                return False
        
        return True

    def filter_var(self, location_a, location_b, info_inst):
        '''
        @return: True if there is no other info in (location_a, location_b)
                 with the same URL,Variable,DataContainer.keys() as the
                 info_inst.
        '''
        for saved_vuln in self.get(location_a, location_b):
            
            if saved_vuln.get_var() == info_inst.get_var() and\
            saved_vuln.get_url() == info_inst.get_url():
            
                if saved_vuln.get_dc() is None and\
                info_inst.get_dc() is None:
                    return False
                
                if saved_vuln.get_dc() is not None and\
                info_inst.get_dc() is not None:
                    
                    if saved_vuln.get_dc().keys() == info_inst.get_dc().keys():
                        return False
        
        return True

    def get_all_vulns(self):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.get_all_entries_of_class(Vuln)

    def get_all_infos(self):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.get_all_entries_of_class(Info)

    def get_all_shells(self, w3af_core=None):
        '''
        @param w3af_core: The w3af_core used in the current scan
        @see: Shell.__reduce__ to understand why we need the w3af_core 
        @return: A list of all vulns reported by all plugins.
        '''
        all_shells = []

        for shell in self.get_all_entries_of_class(Shell):
            if w3af_core is not None:
                shell.set_url_opener(w3af_core.uri_opener)
                shell.set_worker_pool(w3af_core.worker_pool)

            all_shells.append(shell)

        return all_shells

    def _get_real_name(self, data):
        if isinstance(data, basestring):
            return data
        else:
            return data.get_name()

    def append(self, location_a, location_b, value):
        '''
        This method appends the location_b value to a dict.
        '''
        raise NotImplementedError

    def get(self, plugin_name, location_b=None):
        '''
        @param plugin_name: The plugin that saved the data to the
                                kb.info Typically the name of the plugin,
                                but could also be the plugin instance.

        @param location_b: The name of the variables under which the vuln
                                 objects were saved. Typically the same name of
                                 the plugin, or something like "vulns", "errors",
                                 etc. In most cases this is NOT None. When set
                                 to None, a dict with all the vuln objects found
                                 by the plugin_name is returned.

        @return: Returns the data that was saved by another plugin.
        '''
        raise NotImplementedError

    def get_all_entries_of_class(self, klass):
        '''
        @return: A list of all objects of class == klass that are saved in the kb.
        '''
        raise NotImplementedError

    def clear(self, location_a, location_b):
        '''
        Clear any values stored in (location_a, location_b)
        '''
        raise NotImplementedError
    
    def raw_write(self, location_a, location_b, value):
        '''
        This method saves the value to (location_a,location_b)
        '''
        raise NotImplementedError

    def raw_read(self, location_a, location_b):
        '''
        This method reads the value from (location_a,location_b)
        '''
        raise NotImplementedError
    
    def dump(self):
        raise NotImplementedError

    def cleanup(self):
        '''
        Cleanup all internal data.
        '''
        raise NotImplementedError
    
class InMemoryKnowledgeBase(BasicKnowledgeBase):
    '''
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can exchange information.

    Data is stored on memory.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''
    def __init__(self):
        super(InMemoryKnowledgeBase, self).__init__()
        self._kb = {}

    def clear(self, location_a, location_b):
        if location_a in self._kb:
            if location_b in self._kb[location_a]:
                del self._kb[location_a][location_b] 
                
    def raw_write(self, location_a, location_b, value):
        '''
        This method saves the value to (location_a,location_b)
        '''
        name = self._get_real_name(location_a)

        with self._kb_lock:
            if name not in self._kb:
                self._kb[name] = {location_b: value}
            else:
                self._kb[name][location_b] = value

    def append(self, location_a, location_b, value):
        '''
        This method appends the location_b value to a dict.
        '''
        name = self._get_real_name(location_a)

        with self._kb_lock:
            if name not in self._kb:
                self._kb[name] = {location_b: [value]}
            else:
                if location_b in self._kb[name]:
                    self._kb[name][location_b].append(value)
                else:
                    self._kb[name][location_b] = [value]
    
    def get(self, plugin_name, location_b=None):
        '''
        @param plugin_name: The plugin that saved the data to the
                                kb.info Typically the name of the plugin,
                                but could also be the plugin instance.

        @param location_b: The name of the variables under which the vuln
                                 objects were saved. Typically the same name of
                                 the plugin, or something like "vulns", "errors",
                                 etc. In most cases this is NOT None. When set
                                 to None, a dict with all the vuln objects found
                                 by the plugin_name is returned.

        @return: Returns the data that was saved by another plugin.
        '''
        name = self._get_real_name(plugin_name)

        with self._kb_lock:
            if name not in self._kb:
                return []
            else:
                if location_b is None:
                    return self._kb[name]
                elif location_b not in self._kb[name]:
                    return []
                else:
                    return self._kb[name][location_b]
    
    raw_read = get

    def get_all_entries_of_class(self, klass):
        '''
        @return: A list of all objects of class == klass that are saved in the kb.
        '''
        res = []

        with self._kb_lock:
            for pdata in self._kb.itervalues():
                for vals in pdata.itervalues():
                    if not isinstance(vals, list):
                        continue
                    for v in vals:
                        if isinstance(v, klass):
                            res.append(v)
        return res

    def dump(self):
        return self._kb

    def cleanup(self):
        '''
        Cleanup internal data.
        '''
        with self._kb_lock:
            self._kb.clear()


class DBKnowledgeBase(BasicKnowledgeBase):
    '''
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can exchange information.

    Data is stored in a DB.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        super(DBKnowledgeBase, self).__init__()
        
        self.urls = DiskSet()
        self.fuzzable_requests = DiskSet()
        
        self.db = get_default_persistent_db_instance()

        columns = [('location_a', 'TEXT'),
                   ('location_b', 'TEXT'),
                   ('pickle', 'BLOB')]

        self.table_name = rand_alpha(30)
        self.db.create_table(self.table_name, columns)
        self.db.create_index(self.table_name, ['location_a', 'location_b'])
        self.db.commit()

    def clear(self, location_a, location_b):
        location_a = self._get_real_name(location_a)
        
        query = "DELETE FROM %s WHERE location_a = ? and location_b = ?"
        params = (location_a, location_b)
        self.db.execute(query % self.table_name, params)

    def raw_write(self, location_a, location_b, value):
        '''
        This method saves value to (location_a,location_b) but previously
        clears any pre-existing values.
        '''
        if isinstance(value, Info):
            raise TypeError('Use append or append_uniq to store vulnerabilities')
        
        location_a = self._get_real_name(location_a)
        
        self.clear(location_a, location_b)
        self.append(location_a, location_b, value, ignore_type=True)

    def raw_read(self, location_a, location_b):
        '''
        This method reads the value from (location_a,location_b)
        '''
        location_a = self._get_real_name(location_a)
        result = self.get(location_a, location_b)
        
        if len(result) > 1:
            msg = 'Incorrect use of raw_write/raw_read, found %s.'
            raise RuntimeError(msg % result)
        elif len(result) == 0:
            return []
        else:
            return result[0]

    def append(self, location_a, location_b, value, ignore_type=False):
        '''
        This method appends the location_b value to a dict.
        '''
        if not ignore_type and not isinstance(value, (Info, Shell)):
            msg = 'You MUST use raw_write/raw_read to store non-info objects'\
                  ' to the KnowledgeBase.'
            raise TypeError(msg)
        
        location_a = self._get_real_name(location_a)
        
        pickled_obj = cPickle.dumps(value)
        t = (location_a, location_b, pickled_obj)
        
        query = "INSERT INTO %s VALUES (?, ?, ?)" % self.table_name
        self.db.execute(query, t)

    def get(self, location_a, location_b):
        '''
        @param location_a: The plugin that saved the data to the
                           kb.info Typically the name of the plugin,
                           but could also be the plugin instance.

        @param location_b: The name of the variables under which the vuln
                                 objects were saved. Typically the same name of
                                 the plugin, or something like "vulns", "errors",
                                 etc. In most cases this is NOT None. When set
                                 to None, a dict with all the vuln objects found
                                 by the plugin_name is returned.

        @return: Returns the data that was saved by another plugin.
        '''
        location_a = self._get_real_name(location_a)
        
        if location_b is None:
            query = 'SELECT pickle FROM %s WHERE location_a = ?'
            params = (location_a,)
        else:
            query = 'SELECT pickle FROM %s WHERE location_a = ?'\
                                           ' and location_b = ?'
            params = (location_a, location_b)
        
        result_lst = []
        
        results = self.db.select(query % self.table_name, params)
        for r in results:
            obj = cPickle.loads(r[0])
            result_lst.append(obj)
        
        return result_lst

    def get_all_entries_of_class(self, klass):
        '''
        @return: A list of all objects of class == klass that are saved in the kb.
        '''
        query = 'SELECT pickle FROM %s'
        results = self.db.select(query % self.table_name)
        
        result_lst = []

        for r in results:
            obj = cPickle.loads(r[0])
            if isinstance(obj, klass):
                result_lst.append(obj)
        
        return result_lst

    def dump(self):
        result_dict = {}
        
        query = 'SELECT location_a, location_b, pickle FROM %s'
        results = self.db.select(query % self.table_name)
        
        for location_a, location_b, pickle in results:
            obj = cPickle.loads(pickle)
            
            if location_a not in result_dict:
                result_dict[location_a] = {location_b: [obj,]}
            elif location_b not in result_dict[location_a]:
                result_dict[location_a][location_b] = [obj,]
            else:
                result_dict[location_a][location_b].append(obj)
                
        return result_dict

    def cleanup(self):
        '''
        Cleanup internal data.
        '''
        self.db.execute("DELETE FROM %s WHERE 1=1" % self.table_name)
        self.urls.clear()
        self.fuzzable_requests.clear()
    
    def remove(self):
        self.db.drop_table(self.table_name)
    
    def get_all_known_urls(self):
        '''
        @return: A DiskSet with all the known URLs as URL objects.
        '''
        return self.urls
    
    def add_url(self, url):
        '''
        @return: True if the URL was previously unknown 
        '''
        if not isinstance(url, URL):
            msg = 'add_url requires a URL as parameter got %s instead.'
            raise TypeError(msg % type(url))
        
        return self.urls.add(url)
    
    def get_all_known_fuzzable_requests(self):
        '''
        @return: A DiskSet with all the known URLs as URL objects.
        '''
        return self.fuzzable_requests
    
    def add_fuzzable_request(self, fuzzable_request):
        '''
        @return: True if the FuzzableRequest was previously unknown 
        '''
        if not isinstance(fuzzable_request, FuzzableRequest):
            msg = 'add_fuzzable_request requires a FuzzableRequest as parameter.'\
                  'got %s instead.'
            raise TypeError(msg % type(fuzzable_request))
        
        self.add_url(fuzzable_request.get_url())
        
        return self.fuzzable_requests.add(fuzzable_request)
        

KnowledgeBase = DBKnowledgeBase

kb = KnowledgeBase()
