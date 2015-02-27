"""
menu.py

Copyright 2008 Andres Riancho

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
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.kb.vuln_templates.utils import (get_template_names,
                                                    get_template_by_name)
from w3af.core.ui.console.menu import menu
from w3af.core.ui.console.util import suggest
from w3af.core.ui.console.config import ConfigMenu


class kbMenu(menu):

    """
    This menu is used to display information from the knowledge base
    and (in the nearest future) to manipulate it.

    :author: Alexander Berezhnoy (alexander.berezhnoy |at| gmail.com)
    """
    def __init__(self, name, console, w3afcore, parent=None, **other):
        menu.__init__(self, name, console, w3afcore, parent)
        self._load_help('kb')

        # A mapping of KB data types to how to display it.
        # Key of the data type => (KB getter, (column names), (column getters))k
        self.__getters = {
            'vulns': (
                kb.kb.get_all_vulns,
                ['Vulnerability', 'Description'],),
            'info': (
                kb.kb.get_all_infos,
                ['Info', 'Description'],),
            'shells': (
                kb.kb.get_all_shells,
                ['Shells', 'Description'],)
        }

    def _list_objects(self, descriptor, objs):
        col_names = descriptor[0]
        result = [col_names]

        for obj in objs:
            result.append([])
            row = [obj.get_name(), obj.get_desc()]

            result.append(row)

        self._console.draw_table(result)

    def _cmd_list(self, params):
        if len(params) > 0:
            for p in params:
                if p in self.__getters:
                    desc = self.__getters[p]
                    self._list_objects(desc[1:], desc[0]())
                else:
                    om.out.console('Type %s is unknown' % p)
        else:
            om.out.console('Parameter type is missing, see the help:')
            self._cmd_help(['list'])

    def _para_list(self, params, part):
        if len(params):
            return []

        return suggest(self.__getters.keys(), part)

    def _cmd_add(self, params):
        if len(params) == 0:
            om.out.console('Parameter "type" is missing, see the help:')
            self._cmd_help(['add'])
            return
        
        if len(params) > 1:
            om.out.console('Only one parameter is accepted, see the help:')
            self._cmd_help(['add'])
            return
        
        template_name = params[0]
        if template_name not in get_template_names():
            om.out.console('Type %s is unknown' % template_name)
            return
        
        # Now we use the fact that templates are configurable just like
        # plugins, misc-settings, etc.
        template_inst = get_template_by_name(template_name)
        template_menu = StoreOnBackConfigMenu(template_name, self._console,
                                              self._w3af, self, template_inst)
        
        # Note: The data is stored in the KB when the user does a "back"
        #       see the StoreOnBackConfigMenu implementation
        return template_menu
    
    def _para_add(self, params, part):
        if len(params):
            return []

        return suggest(get_template_names(), part)


class StoreOnBackConfigMenu(ConfigMenu):
    def _cmd_back(self, tokens):
        try:
            self._cmd_save(tokens)
        except (ValueError, BaseFrameworkException) as e:
            om.out.error(str(e))
            return self._console.back
        
        vuln_name = self._configurable.get_vulnerability_name()
        
        try:
            self._configurable.store_in_kb()
        except Exception, e:
            msg = 'Failed to store "%s" in the knowledge base because of a'\
                  ' configuration error at: "%s".'
            om.out.console(msg % (vuln_name, e))
        else:
            om.out.console('Stored "%s" in the knowledge base.' % vuln_name)
            
        return self._console.back
