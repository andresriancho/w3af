"""
press_enter.py

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
from w3af.core.controllers.chrome.login.submit_form.strategies.base_strategy import BaseStrategy


class PressEnterStrategy(BaseStrategy):
    def __init__(self, chrome, form, username, password, debugging_id):
        super(PressEnterStrategy, self).__init__(chrome, form, username, password, debugging_id)

    def submit_form(self):
        """
        Submit a form by pressing the `Enter` key in chrome
        """
        self.fill_form()

        # If the previous steps were able to identify the submit button then
        # focus on that and send Enter
        if self.form.get_submit_css_selector():
            self.chrome.focus(self.form.get_submit_css_selector())
        else:
            self.chrome.focus(self.form.get_password_css_selector())

        #
        # And now send the Enter key to (hopefully) submit the form
        #
        self.chrome.press_enter_key()

    def get_name(self):
        return 'PressEnter'
