"""
question_target_2.py

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


class question_target_2(question):
    """
    This is the first question of the wizard, where you have to speficy the target.
    """
    def __init__(self, w3af_core):
        question.__init__(self, w3af_core)

        self._question_id = 'target_2'

        self._question_title = 'Target Location'

        self._question_str = 'w3af has a group of plugins that fetch information about your target application'
        self._question_str += ' using Internet search engines. In order to enable or disable those plugins, we need'
        self._question_str += ' to know the following:'

    def _get_option_objects(self):
        """
        :return: A list of options for this question.
        """

        d1 = 'Is the target web application reachable from the Internet?'
        o1 = opt_factory('internet', True, d1, 'boolean')

        ol = OptionList()
        ol.add(o1)

        return ol

    def get_next_question_id(self, options_list):

        internet = options_list['internet'].get_value()
        # FIXME: Do something with this value

        return None
