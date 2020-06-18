"""
main.py

Copyright 2020 Andres Riancho

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
from w3af.core.controllers import output_manager as om

from w3af.core.controllers.chrome.login.find_form.strategies.form_tag import FormTagStrategy
from w3af.core.controllers.chrome.login.find_form.strategies.password_and_parent import PasswordAndParentStrategy


class FormFinder(object):

    STRATEGIES = [
        FormTagStrategy,
        PasswordAndParentStrategy
    ]

    def __init__(self, chrome, debugging_id):
        self.chrome = chrome
        self.debugging_id = debugging_id

    def find_forms(self):
        """
        :return: Yield forms as they are found by each strategy
        """
        identified_forms = []

        for strategy_klass in self.STRATEGIES:
            strategy = strategy_klass(self.chrome, self.debugging_id)

            try:
                for form in strategy.find_forms():
                    if form in identified_forms:
                        continue

                    identified_forms.append(form)
                    yield form
            except Exception as e:
                msg = 'Form finder strategy %s raised exception: "%s" (did: %s)'
                args = (strategy.get_name(),
                        e,
                        self.debugging_id)
                om.out.debug(msg % args)
