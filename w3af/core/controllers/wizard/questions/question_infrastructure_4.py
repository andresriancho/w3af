"""
question_infrastructure_4.py

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

import w3af.core.data.kb.config as cf


class question_infrastructure_4(question):
    """
    This is the first question of the wizard, where you have to speficy the target.
    """
    def __init__(self, w3af_core):
        question.__init__(self, w3af_core)

        self._question_id = 'infrastructure_4'

        self._question_title = 'Plugin selection'

        self._question_str = 'w3af has a group of plugins that fetch information about the target'
        self._question_str += ' application using Internet search engines. In order to enable or'
        self._question_str += ' disable those plugins, we need to know the following:'

    def _get_option_objects(self):
        """
        :return: A list of options for this question.
        """
        self._d1 = 'Is the target web application reachable from the Internet?'
        o1 = opt_factory(self._d1, True, self._d1, 'boolean')

        ol = OptionList()
        ol.add(o1)

        return ol

    def get_next_question_id(self, options_list):
        cf.cf.save('reachable_from_internet',
                   options_list[self._d1].get_value())

        # The next question
        if cf.cf.get('reachable_from_internet'):
            return 'infrastructure_internet_1'
        else:
            return None
