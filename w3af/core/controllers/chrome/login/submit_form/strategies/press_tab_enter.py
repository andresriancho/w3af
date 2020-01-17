"""
press_tab_enter.py

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


class PressTabEnterStrategy(BaseStrategy):
    def __init__(self, chrome, form, username, password, debugging_id):
        super(PressTabEnterStrategy, self).__init__(chrome, form, username, password, debugging_id)

    def submit_form(self):
        """
        Submit a form by:

            - Focusing on the password input

            - Pressing `Tab` key in chrome, which in well designed web UIs
              should move the focus to the submit button

            - Press the `Enter` key in chrome, which should submit the login
              form. Remember that the previous step focused the browser in the
              submit button.
        """
        self.fill_form()

        # We get here when the PressEnter strategy didn't work, thus the form
        # CSS selector is most likely incorrect or does not exist. We can't use:
        #
        # self.form.get_submit_css_selector()
        #
        self.chrome.focus(self.form.get_password_css_selector())

        #
        # Press tab to change focus to the submit button
        #
        self.chrome.press_tab_key()

        #
        # And now send the Enter key to (hopefully) submit the form
        #
        self.chrome.press_enter_key()

    def get_name(self):
        return 'PressTabEnter'
