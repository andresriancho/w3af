"""
question_infrastructure_1.py

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


class question_infrastructure_1(question):
    """
    This is the first question of the wizard, where you have to speficy the target.
    """
    def __init__(self, w3af_core):
        question.__init__(self, w3af_core)

        self._question_id = 'infrastructure_1'

        self._question_title = 'Target URL'

        self._question_str = 'In this step you should specify the URL of the target web application.'
        self._question_str += ' Remember that you can separate different URLs with commas like this: \n'
        self._question_str += '    - http://host.tld/a.php , http://host.tld/b.php'

    def _get_option_objects(self):
        """
        :return: A list of options for this question.
        """
        self._d1 = 'Target URL'
        o1 = opt_factory('target', 'http://example.com', self._d1, 'url_list')

        ol = OptionList()
        ol.add(o1)

        return ol

    def get_next_question_id(self, options_list):
        # I don't care about the target OS for these tests, so I add them here with the default value
        o2 = opt_factory('target_os', 'unknown', '', 'string')
        o3 = opt_factory('target_framework', 'unknown', '', 'string')

        #   Manually copy the OptionList... the copy.deepcopy method fails :(
        ol_copy = OptionList()
        for o in options_list:
            ol_copy.add(o)

        # Get the "Target URL" and change it back to "target" so the core can understand it
        o1 = ol_copy['target']
        ol_copy.add(o2)
        ol_copy.add(o3)

        # Save the target to the core, all the validations are made there.
        self.w3af_core.target.set_options(ol_copy)

        # The next question
        return 'infrastructure_2'
