"""
base_strategy.py

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


class BaseStrategy(object):
    def __init__(self, chrome, form, username, password, debugging_id):
        self.chrome = chrome
        self.form = form
        self.username = username
        self.password = password
        self.debugging_id = debugging_id

    def fill_form(self):
        """
        Fills the form by instrumenting typing on the inputs
        """
        self.chrome.type_text(self.username,
                              self.form.get_username_css_selector())

        self.chrome.type_text(self.password,
                              self.form.get_password_css_selector())
