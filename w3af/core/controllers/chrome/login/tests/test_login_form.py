"""
test_login_form.py

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
import unittest

from w3af.core.controllers.chrome.login.login_form import LoginForm


class TestLoginForm(unittest.TestCase):
    def test_in(self):
        form_1 = LoginForm()
        form_1.set_submit_css_selector('a')
        form_1.set_username_css_selector('a')
        form_1.set_password_css_selector('a')
        form_1.set_parent_css_selector('a')

        form_2 = LoginForm()
        form_2.set_submit_css_selector('a')
        form_2.set_username_css_selector('a')
        form_2.set_password_css_selector('a')
        form_2.set_parent_css_selector('a')

        form_3 = LoginForm()
        form_3.set_submit_css_selector('b')
        form_3.set_username_css_selector('a')
        form_3.set_password_css_selector('a')
        form_3.set_parent_css_selector('a')

        l = [form_1, form_2]

        self.assertIn(form_1, l)
        self.assertNotIn(form_3, l)

        self.assertEqual(form_1, form_2)
        self.assertNotEqual(form_1, form_3)
