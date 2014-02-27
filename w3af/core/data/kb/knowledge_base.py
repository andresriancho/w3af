"""
knowledge_base.py

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
import threading
import cPickle
import types
import collections

from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.db.dbms import get_default_persistent_db_instance
from w3af.core.data.db.disk_set import DiskSet
from w3af.core.data.parsers.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.shell import Shell
from weakref import WeakValueDictionary


class BasicKnowledgeBase(object): 
    """
    This is a base class from which all implementations of KnowledgeBase will
    inherit. It has the basic utility methods that will be used.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        self._kb_lock = threading.RLock()
    
        self.FILTERS = {'URL': self.filter_url,
                        'VAR': self.filter_var}
        
    def append_uniq(self, location_a, location_b, info_inst, filter_by='VAR'):
        """
        Append to a location in the KB if and only if there it no other
        vulnerability in the same location for the same URL and parameter.

        Does this in a thread-safe manner.

        :param filter_by: One of 'VAR' of 'URL'. Only append to the kb in
                          (location_a, location_b) if there is NO OTHER info
                          in that location with the same:
                              - 'VAR': URL,Variable,DataContainer.keys()
                              - 'URL': URL

        :return: True if the vuln was added. False if there was already a
                 vulnerability in the KB location with the same URL and
                 parameter.
        """
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
        """
        :return: True if there is no other info in (location_a, location_b)
                 with the same URL as the info_inst.
        """
        for saved_vuln in self.get(location_a, location_b):
            if saved_vuln.get_url() == info_inst.get_url():
                return False
        
        return True

    def filter_var(self, location_a, location_b, info_inst):
        """
        :return: True if there is no other info in (location_a, location_b)
                 with the same URL,Variable,DataContainer.keys() as the
                 info_inst.
        """
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
        """
        :return: A list of all vulns reported by all plugins.
        """
        return self.get_all_entries_of_class(Vuln)

    def get_all_infos(self):
        """
        :return: A list of all vulns reported by all plugins.
        """
        return self.get_all_entries_of_class(Info)

    def get_all_shells(self, w3af_core=None):
        """
        :param w3af_core: The w3af_core used in the current scan
        @see: Shell.__reduce__ to understand why we need the w3af_core 
        :return: A list of all vulns reported by all plugins.
        """
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
        """
        This method appends the location_b value to a dict.
        """
        raise NotImplementedError

    def get(self, plugin_name, location_b=None):
        """
        :param plugin_name: The plugin that saved the data to the
                                kb.info Typically the name of the plugin,
                                but could also be the plugin instance.

        :param location_b: The name of the variables under which the vuln
                                 objects were saved. Typically the same name of
                                 the plugin, or something like "vulns", "errors",
                                 etc. In most cases this is NOT None. When set
                                 to None, a dict with all the vuln objects found
                                 by the plugin_name is returned.

        :return: Returns the data that was saved by another plugin.
        """
        raise NotImplementedError

    def get_all_entries_of_class(self, klass):
        """
        :return: A list of all objects of class == klass that are saved in the kb.
        """
        raise NotImplementedError

    def clear(self, location_a, location_b):
        """
        Clear any values stored in (location_a, location_b)
        """
        raise NotImplementedError
    
    def raw_write(self, location_a, location_b, value):
        """
        This method saves the value to (location_a,location_b)
        """
        raise NotImplementedError

    def raw_read(self, location_a, location_b):
        """
        This method reads the value from (location_a,location_b)
        """
        raise NotImplementedError
    
    def dump(self):
        raise NotImplementedError

    def cleanup(self):
        """
        Cleanup all internal data.
        """
        raise NotImplementedError


class DBKnowledgeBase(BasicKnowledgeBase):
    """
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can exchange information.

    Data is stored in a DB.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        super(DBKnowledgeBase, self).__init__()
        
        self.urls = DiskSet()
        self.fuzzable_requests = DiskSet()
        
        self.db = get_default_persistent_db_instance()

        columns = [('location_a', 'TEXT'),
                   ('location_b', 'TEXT'),
                   ('uniq_id', 'TEXT'),
                   ('pickle', 'BLOB')]

        self.table_name = rand_alpha(30)
        self.db.create_table(self.table_name, columns)
        self.db.create_index(self.table_name, ['location_a', 'location_b'])
        self.db.create_index(self.table_name, ['uniq_id',])
        self.db.commit()
        
        # TODO: Why doesn't this work with a WeakValueDictionary?
        self.observers = {} #WeakValueDictionary()
        self.type_observers = {} #WeakValueDictionary()
        self.url_observers = []
        self._observer_id = 0

    def clear(self, location_a, location_b):
        location_a = self._get_real_name(location_a)
        
        query = "DELETE FROM %s WHERE location_a = ? and location_b = ?"
        params = (location_a, location_b)
        self.db.execute(query % self.table_name, params)

    def raw_write(self, location_a, location_b, value):
        """
        This method saves value to (location_a,location_b) but previously
        clears any pre-existing values.
        """
        if isinstance(value, Info):
            raise TypeError('Use append or append_uniq to store vulnerabilities')
        
        location_a = self._get_real_name(location_a)
        
        self.clear(location_a, location_b)
        self.append(location_a, location_b, value, ignore_type=True)

    def raw_read(self, location_a, location_b):
        """
        This method reads the value from (location_a,location_b)
        """
        location_a = self._get_real_name(location_a)
        result = self.get(location_a, location_b, check_types=False)
        
        if len(result) > 1:
            msg = 'Incorrect use of raw_write/raw_read, found %s rows.'
            raise RuntimeError(msg % result)
        elif len(result) == 0:
            return []
        else:
            return result[0]
    
    def _get_uniq_id(self, obj):
        if isinstance(obj, Info):
            return obj.get_uniq_id()
        else:
            if isinstance(obj, collections.Iterable):
                concat_all = ''.join([str(i) for i in obj])
                return str(hash(concat_all))
            else:
                return str(hash(obj))

    def append(self, location_a, location_b, value, ignore_type=False):
        """
        This method appends the location_b value to a dict.
        """
        if not ignore_type and not isinstance(value, (Info, Shell)):
            msg = 'You MUST use raw_write/raw_read to store non-info objects'\
                  ' to the KnowledgeBase.'
            raise TypeError(msg)
        
        location_a = self._get_real_name(location_a)
        uniq_id = self._get_uniq_id(value)
        
        pickled_obj = cPickle.dumps(value)
        t = (location_a, location_b, uniq_id, pickled_obj)
        
        query = "INSERT INTO %s VALUES (?, ?, ?, ?)" % self.table_name
        self.db.execute(query, t)
        self._notify(location_a, location_b, value)

    def get(self, location_a, location_b, check_types=True):
        """
        :param location_a: The plugin that saved the data to the
                           kb.info Typically the name of the plugin,
                           but could also be the plugin instance.

        :param location_b: The name of the variables under which the vuln
                           objects were saved. Typically the same name of
                           the plugin, or something like "vulns", "errors",
                           etc. In most cases this is NOT None. When set
                           to None, a dict with all the vuln objects found
                           by the plugin_name is returned.

        :return: Returns the data that was saved by another plugin.
        """
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
            
            if check_types and not isinstance(obj, (Info, Shell)):
                raise TypeError('Use raw_write and raw_read to query the'
                                ' knowledge base for non-Info objects')
            
            result_lst.append(obj)
        
        return result_lst

    def get_by_uniq_id(self, uniq_id):
        query = 'SELECT pickle FROM %s WHERE uniq_id = ?'
        params = (uniq_id,)
        
        result = self.db.select_one(query % self.table_name, params)
        
        if result is not None:
            result = cPickle.loads(result[0])
        
        return result

    def add_observer(self, location_a, location_b, observer):
        """
        Add the observer function to the observer list. The function will be
        called when there is a change in (location_a, location_b).
        
        You can use None in location_a or location_b as wildcards.
        
        The observer function needs to be a function which takes three params:
            * location_a
            * location_b
            * value that's added to the kb location
        
        :return: None
        """
        if not isinstance(location_a, (basestring, types.NoneType)) or \
        not isinstance(location_a, (basestring, types.NoneType)):
            raise TypeError('Observer locations need to be strings or None.')
        
        observer_id = self.get_observer_id()
        self.observers[(location_a, location_b, observer_id)] = observer
    
    def add_types_observer(self, type_filter, observer):
        """
        Add the observer function to the list of functions to be called when a
        new object that is of type "type_filter" is added to the KB.
        
        The type_filter must be one of Info, Vuln or Shell.
        
        :return: None
        """
        if type_filter not in (Info, Vuln, Shell):
            msg = 'The type_filter needs to be one of Info, Vuln or Shell'
            raise TypeError(msg)
        
        observer_id = self.get_observer_id()
        self.type_observers[(type_filter, observer_id)] = observer
        
    def get_observer_id(self):
        self._observer_id += 1
        return self._observer_id
    
    def _notify(self, location_a, location_b, value):
        """
        Call the observer if the location_a/location_b matches with the
        configured observers.
        
        :return: None
        """
        # Note that I copy the items list in order to iterate though it without
        # any issues like the size changing
        for (obs_loc_a, obs_loc_b, _), observer in self.observers.items()[:]:
            
            if obs_loc_a is None and obs_loc_b is None:
                observer(location_a, location_b, value)
                continue

            if obs_loc_a == location_a and obs_loc_b is None:
                observer(location_a, location_b, value)
                continue
            
            if obs_loc_a == location_a and obs_loc_b == location_b:
                observer(location_a, location_b, value)
                continue
        
        for (type_filter, _), observer in self.type_observers.items()[:]:
            if isinstance(value, type_filter):
                observer(location_a, location_b, value)

    def get_all_entries_of_class(self, klass):
        """
        :return: A list of all objects of class == klass that are saved in the kb.
        """
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
        """
        Cleanup internal data.
        """
        self.db.execute("DELETE FROM %s WHERE 1=1" % self.table_name)
        
        # Remove the old, create new.
        self.urls.cleanup()
        self.urls = DiskSet()
        
        self.fuzzable_requests.cleanup()
        self.fuzzable_requests = DiskSet()
        
        self.observers.clear()
    
    def remove(self):
        self.db.drop_table(self.table_name)
        self.urls.cleanup()
        self.fuzzable_requests.cleanup()
        self.observers.clear()
    
    def get_all_known_urls(self):
        """
        :return: A DiskSet with all the known URLs as URL objects.
        """
        return self.urls

    def add_url_observer(self, observer):
        self.url_observers.append(observer)

    def _notify_url_observers(self, new_url):
        """
        Call the observer with new_url.
        
        :return: None
        """
        # Note that I copy the items list in order to iterate though it without
        # any issues like the size changing
        for observer in self.url_observers[:]:            
            observer(new_url)
    
    def add_url(self, url):
        """
        :return: True if the URL was previously unknown 
        """
        if not isinstance(url, URL):
            msg = 'add_url requires a URL as parameter got %s instead.'
            raise TypeError(msg % type(url))
        
        self._notify_url_observers(url)
        return self.urls.add(url)
    
    def get_all_known_fuzzable_requests(self):
        """
        :return: A DiskSet with all the known URLs as URL objects.
        """
        return self.fuzzable_requests
    
    def add_fuzzable_request(self, fuzzable_request):
        """
        :return: True if the FuzzableRequest was previously unknown 
        """
        if not isinstance(fuzzable_request, FuzzableRequest):
            msg = 'add_fuzzable_request requires a FuzzableRequest as parameter.'\
                  'got %s instead.'
            raise TypeError(msg % type(fuzzable_request))
        
        self.add_url(fuzzable_request.get_url())
        
        return self.fuzzable_requests.add(fuzzable_request)
        

KnowledgeBase = DBKnowledgeBase

kb = KnowledgeBase()
