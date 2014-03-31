"""
question_infrastructure_2.py

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
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.controllers.wizard.question import question


class question_infrastructure_2(question):
    """
    This is the first question of the wizard, where you have to speficy the
    target.
    """
    def __init__(self, w3af_core):
        question.__init__(self, w3af_core)

        self._question_id = 'infrastructure_2'

        self._question_title = 'Plugin selection'

        self._question_str = 'This step allows you to select from a group of plugins that'
        self._question_str += ' identify network and HTTP appliances that may be between'
        self._question_str += ' w3af and the target Web Application.'

    def _get_option_objects(self):
        """
        :return: A list of options for this question.
        """
        self._d1 = 'Detect active filters (IPS, WAF, Layer 7 firewalls)'
        o1 = opt_factory(self._d1, True, self._d1, 'boolean')

        self._d2 = 'Detect (reverse) proxies'
        o2 = opt_factory(self._d2, True, self._d2, 'boolean')

        self._d3 = 'Fingerprint Web Application Firewalls'
        o3 = opt_factory(self._d3, True, self._d3, 'boolean')

        self._d4 = 'Identify HTTP load balancers'
        o4 = opt_factory(self._d4, True, self._d4, 'boolean')

        ol = OptionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)

        return ol

    def get_next_question_id(self, options_list):
        plugin_list = []

        if options_list[self._d1].get_value():
            plugin_list.append('afd')

        if options_list[self._d2].get_value():
            plugin_list.append('detect_reverse_proxy')
            plugin_list.append('detect_transparent_proxy')

        if options_list[self._d3].get_value():
            plugin_list.append('fingerprint_WAF')

        if options_list[self._d4].get_value():
            plugin_list.append('halberd')

        # Set the plugins to be run
        old_discovery = self.w3af_core.plugins.get_enabled_plugins('infrastructure')
        plugin_list.extend(old_discovery)
        self.w3af_core.plugins.set_plugins(plugin_list, 'infrastructure')

        # Next question
        return 'infrastructure_3'
