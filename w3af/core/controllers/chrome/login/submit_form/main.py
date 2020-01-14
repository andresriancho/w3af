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

from w3af.core.controllers.chrome.login.submit_form.strategies.press_enter import PressEnterStrategy
from w3af.core.controllers.chrome.login.submit_form.strategies.form_input_submit import FormInputSubmitStrategy


class FormSubmitter(object):

    STRATEGIES = [PressEnterStrategy,
                  FormInputSubmitStrategy]

    def __init__(self, chrome, form, login_form_url, username, password, debugging_id):
        self.chrome = chrome
        self.form = form
        self.login_form_url = login_form_url
        self.username = username
        self.password = password
        self.debugging_id = debugging_id

    def submit_form(self):
        """
        :return: Yield None after each form submission. Forms are submitted
                 using different strategies which could generate a valid
                 session or not.
        """
        for strategy_klass in self.STRATEGIES:
            strategy = strategy_klass(self.chrome,
                                      self.form,
                                      self.username,
                                      self.password,
                                      self.debugging_id)

            try:
                for _ in self._submit_and_restore(strategy):
                    yield strategy
            except Exception as e:
                msg = 'Form submit strategy %s raised exception: "%s" (did: %s)'
                args = (strategy.get_name(),
                        e,
                        self.debugging_id)
                om.out.debug(msg % args)

    def _submit_and_restore(self, strategy):
        for _ in strategy.submit_form():
            yield

            # Restore the previous state before trying a new one
            self.chrome.load_url(self.login_form_url)
            self.chrome.wait_for_load()

