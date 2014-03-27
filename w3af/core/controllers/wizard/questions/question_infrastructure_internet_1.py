"""
question_infrastructure_internet_1.py

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


class question_infrastructure_internet_1(question):
    """
    This is the first question of the wizard, where you have to speficy the target.
    """
    def __init__(self, w3af_core):
        question.__init__(self, w3af_core)

        self._question_id = 'infrastructure_internet_1'

        self._question_title = 'Plugin selection'

        self._question_str = 'Please choose from the options below:'

    def _get_option_objects(self):
        """
        :return: A list of options for this question.
        """
        self._d1 = 'Find other virtual hosts using MSN search'
        o1 = opt_factory(self._d1, False, self._d1, 'boolean')

        ol = OptionList()
        ol.add(o1)

        return ol

    def get_next_question_id(self, options_list):
        plugin_list = []

        if options_list[self._d1].get_value():
            plugin_list.append('shared_hosting')

        # Set the plugins to be run
        old_discovery = self.w3af_core.plugins.get_enabled_plugins('infrastructure')
        plugin_list.extend(old_discovery)
        self.w3af_core.plugins.set_plugins(plugin_list, 'infrastructure')

        return None
