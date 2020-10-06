"""
password_and_parent.py

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
from w3af.core.controllers.chrome.login.find_form.strategies.base_find_form_strategy import \
    BaseFindFormStrategy


class PasswordAndParentStrategy(BaseFindFormStrategy):

    def find_forms(self):
        """
        The algorithm is implemented in dom_analyzer.js

        :return: Yield forms which are identified by the strategy algorithm
        """
        for login_form in self.chrome.get_login_forms_without_form_tags(self.exact_css_selectors):
            yield login_form

    @staticmethod
    def get_name():
        return 'PasswordAndParent'
