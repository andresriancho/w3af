"""
login_form.py

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


class LoginForm(object):
    def __init__(self):
        self.parent_css_selector = None
        self.username_css_selector = None
        self.password_css_selector = None
        self.submit_css_selector = None
        self.form_submit_strategy = None

    def get_parent_css_selector(self):
        """
        The `parent` is the DOM node which contains the:
            - input type=text
            - input type=password
            - (optional) input type=submit

        In some cases the `parent` CSS selector will point to a `form` tag,
        but in others (most likely coming from getLoginFormsWithoutFormTags)
        the selector might point to any DOM node.

        :return: The CSS selector to the parent
        """
        return self.parent_css_selector

    def set_parent_css_selector(self, css_selector):
        self.parent_css_selector = css_selector

    def set_submit_strategy(self, form_submit_strategy):
        self.form_submit_strategy = form_submit_strategy

    def get_submit_strategy(self):
        return self.form_submit_strategy

    def get_username_css_selector(self):
        return self.username_css_selector

    def get_password_css_selector(self):
        return self.password_css_selector

    def get_submit_css_selector(self):
        return self.submit_css_selector

    def set_username_css_selector(self, css_selector):
        self.username_css_selector = css_selector

    def set_password_css_selector(self, css_selector):
        self.password_css_selector = css_selector

    def set_submit_css_selector(self, css_selector):
        self.submit_css_selector = css_selector

    def __str__(self):
        msg = '<LoginForm %s / %s / %s / %s>'
        args = (self.username_css_selector,
                self.password_css_selector,
                self.submit_css_selector,
                self.form_submit_strategy.get_name() if self.form_submit_strategy else None)
        return msg % args

    def __repr__(self):
        return str(self)
