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

from core.data.kb.vuln import Vuln
from core.data.kb.info import Info
from core.data.kb.shell import shell


class InMemoryKnowledgeBase(object):
    '''
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can exchange information.

    Data is stored on memory.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        self._kb = {}
        self._kb_lock = threading.RLock()

    def save(self, calling_instance, variable_name, value):
        '''
        This method saves the variable_name value to a dict.
        '''
        name = self._get_real_name(calling_instance)

        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[name] = {variable_name: value}
            else:
                self._kb[name][variable_name] = value

    def append_uniq(self, location_a, location_b, info_inst):
        '''
        Append to a location in the KB if and only if there it no other
        vulnerability in the same location for the same URL and parameter.

        Does this in a thread-safe manner.

        @return: True if the vuln was added. False if there was already a
                 vulnerability in the KB location with the same URL and
                 parameter.
        '''
        if not isinstance(info_inst, Info):
            ValueError('append_unique requires an info object as parameter.')

        with self._kb_lock:
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

            self.append(location_a, location_b, info_inst)
            return True

    def append(self, calling_instance, variable_name, value):
        '''
        This method appends the variable_name value to a dict.
        '''
        name = self._get_real_name(calling_instance)

        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[name] = {variable_name: [value]}
            else:
                if variable_name in self._kb[name]:
                    self._kb[name][variable_name].append(value)
                else:
                    self._kb[name][variable_name] = [value]

    def get(self, plugin_name, variable_name=None):
        '''
        @param plugin_name: The plugin that saved the data to the
                                kb.info Typically the name of the plugin,
                                but could also be the plugin instance.

        @param variable_name: The name of the variables under which the vuln
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
                if variable_name is None:
                    return self._kb[name]
                elif variable_name not in self._kb[name]:
                    return []
                else:
                    return self._kb[name][variable_name]

    def get_all_entries_of_class(self, klass):
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

    def get_all_shells(self):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.get_all_entries_of_class(shell)

    def dump(self):
        return self._kb

    def cleanup(self):
        '''
        Cleanup internal data.
        '''
        with self._kb_lock:
            self._kb.clear()

    def _get_real_name(self, data):
        if isinstance(data, basestring):
            return data
        else:
            return data.get_name()


class DBKnowledgeBase(object):
    '''
    This class saves the data that is sent to it by plugins. It is the only way
    in which plugins can exchange information.

    Data is stored in a DB.

    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        # TODO: Read the comment in password_profiling about performance
        self._kb = {}
        self._kb_lock = threading.RLock()

    def save(self, calling_instance, variable_name, value):
        '''
        This method saves the variable_name value to a dict.
        '''
        name = self._get_real_name(calling_instance)

        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[name] = {variable_name: value}
            else:
                self._kb[name][variable_name] = value

    def append_uniq(self, location_a, location_b, info_inst):
        '''
        Append to a location in the KB if and only if there it no other
        vulnerability in the same location for the same URL and parameter.

        Does this in a thread-safe manner.

        @return: True if the vuln was added. False if there was already a
                 vulnerability in the KB location with the same URL and
                 parameter.
        '''
        if not isinstance(info_inst, Info):
            ValueError('append_unique requires an info object as parameter.')

        with self._kb_lock:
            for saved_vuln in self.get(location_a, location_b):
                if saved_vuln.get_var() == info_inst.get_var() and\
                    saved_vuln.get_url() == info_inst.get_url() and \
                        saved_vuln.get_dc().keys() == info_inst.get_dc().keys():
                    return False

            self.append(location_a, location_b, info_inst)
            return True

    def append(self, calling_instance, variable_name, value):
        '''
        This method appends the variable_name value to a dict.
        '''
        name = self._get_real_name(calling_instance)

        with self._kb_lock:
            if name not in self._kb.keys():
                self._kb[name] = {variable_name: [value]}
            else:
                if variable_name in self._kb[name]:
                    self._kb[name][variable_name].append(value)
                else:
                    self._kb[name][variable_name] = [value]

    def get(self, plugin_name, variable_name=None):
        '''
        @param plugin_name: The plugin that saved the data to the
                                kb.info Typically the name of the plugin,
                                but could also be the plugin instance.

        @param variable_name: The name of the variables under which the vuln
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
                if variable_name is None:
                    return self._kb[name]
                elif variable_name not in self._kb[name]:
                    return []
                else:
                    return self._kb[name][variable_name]

    def get_all_entries_of_class(self, klass):
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

    def get_all_shells(self):
        '''
        @return: A list of all vulns reported by all plugins.
        '''
        return self.get_all_entries_of_class(shell)

    def dump(self):
        return self._kb

    def cleanup(self):
        '''
        Cleanup internal data.
        '''
        with self._kb_lock:
            self._kb.clear()

    def _get_real_name(self, data):
        if isinstance(data, basestring):
            return data
        else:
            return data.get_name()

KnowledgeBase = InMemoryKnowledgeBase

kb = KnowledgeBase()
