# -*- coding: utf8 -*-
"""
form.py

Copyright 2006 Andres Riancho

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
from w3af.core.data.fuzzer.form_filler import smart_fill, smart_fill_file
from w3af.core.data.dc.generic.kv_container import KeyValueContainer
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.parsers.utils.form_params import FormParameters
from w3af.core.data.parsers.utils.form_constants import (INPUT_TYPE_CHECKBOX,
                                                         INPUT_TYPE_RADIO,
                                                         INPUT_TYPE_SELECT,
                                                         INPUT_TYPE_TEXT,
                                                         INPUT_TYPE_PASSWD)


class Form(KeyValueContainer):
    """
    This class represents an HTML form.

    :author: Andres Riancho (andres.riancho@gmail.com) |
             Javier Andalia (jandalia =at= gmail.com)
    """
    AVOID_FILLING_FORM_TYPES = {'checkbox', 'radio', 'select'}
    AVOID_STR_DUPLICATES = {INPUT_TYPE_CHECKBOX,
                            INPUT_TYPE_RADIO,
                            INPUT_TYPE_SELECT}

    def __init__(self, form_params=None):
        """
        :note: I'm wrapping some of the form_params methods in order to provide
               extra features. I deliberately avoided a generic "forward-all"
               wrapper here, since I want to be in control and really know
               what is going to be forwarded to self.form_params.

        :param form_params: An instance of FormParameters
        """
        form_params = FormParameters() if form_params is None else form_params
        self.form_params = form_params

        # We don't send any value in init_val because we're forwarding almost
        # all magic methods (__getitem__, __setitem__, etc.) to the
        # self.form_params attribute, which helps keep the two (FormParameters
        # and Form) instances in sync
        super(Form, self).__init__(init_val=(),
                                   encoding=form_params.get_encoding())

    def get_form_params(self):
        return self.form_params

    def get_autocomplete(self):
        return self.form_params.get_autocomplete()

    def add_form_field(self, form_field):
        return self.form_params.add_form_field(form_field)

    def get_parameter_type(self, var_name, default=INPUT_TYPE_TEXT):
        return self.form_params.get_parameter_type(var_name, default=default)

    def get_file_vars(self):
        return self.form_params.get_file_vars()

    def get_file_name(self, var_name, default=None):
        """
        Here we're implementing this function as a simplification of our
        architecture and to avoid two implementation of smart_fill, since
        we really know that an URLEncoded Form will never have the file names
        (only available in multipart AND when created from parsed post-data)
        """
        return default

    def is_login_form(self):
        return self.form_params.is_login_form()

    def is_registration_form(self):
        return self.form_params.is_registration_form()

    def is_password_change_form(self):
        return self.form_params.is_password_change_form()

    def get_parameter_type_count(self):
        return self.form_params.get_parameter_type_count()

    def get_method(self):
        return self.form_params.get_method()

    def get_action(self):
        return self.form_params.get_action()

    def iteritems(self):
        for k, v in self.form_params.iteritems():
            yield k, v

    def items(self):
        return self.form_params.items()

    def keys(self):
        return self.form_params.keys()

    def iterkeys(self):
        for k in self.form_params.iterkeys():
            yield k

    def update(self, *args, **kwargs):
        return self.form_params.update(*args, **kwargs)

    def __str__(self):
        """
        Each form subclass (URLEncoded and Multipart form) need to implement
        their own __str__.
        """
        raise NotImplementedError

    def __setitem__(self, key, value):
        self.form_params[key] = value

    def __getitem__(self, item):
        return self.form_params[item]

    def __delitem__(self, key):
        del self.form_params[key]

    def __contains__(self, item):
        return item in self.form_params

    def __iter__(self):
        return iter(self.form_params)

    def __reversed__(self):
        return reversed(self.form_params)

    def __nonzero__(self):
        return bool(self.form_params)

    def __reduce__(self):
        return self.__class__, (self.form_params,), {'token': self.token}

    def __setstate__(self, state):
        self.token = state['token']

    def get_type(self):
        """
        Each form subclass (URLEncoded and Multipart form) need to implement
        their own get_type.
        """
        raise NotImplementedError

    def smart_fill(self):
        """
        :return: Fills all the empty parameters (which should be filled)
                 using the smart_fill function.
        """
        file_variables = self.get_file_vars()

        for var_name, value, path, setter in self.iter_setters():
            if self.get_parameter_type(var_name) in self.AVOID_FILLING_FORM_TYPES:
                continue

            if isinstance(value, DataToken):
                # This is the value which is being fuzzed (the payload) and
                # I don't want to change/fill it
                continue

            # The basic idea here is that if the form has files in it, we'll
            # need to fill that input with a file (gif, txt, html) in order
            # to go through the form validations
            if var_name in file_variables:
                file_name = self.get_file_name(var_name, None)
                setter(smart_fill_file(var_name, file_name))

            #   Fill only if the parameter does NOT have a value set.
            #
            #   The reason of having this already set would be that the form
            #   has something like this:
            #
            #   <input type="text" name="p" value="foobar">
            #
            elif value == '':
                setter(smart_fill(var_name))

    def get_login_tokens(self):
        """
        :return: Tokens associated with the login (username and password)
        """
        assert self.is_login_form(), 'Login form is required'

        user_token = None
        pass_token = None

        #
        # Count the parameter types
        #
        for token in self.iter_tokens():

            ptype = self.get_parameter_type(token.get_name()).lower()

            if ptype == INPUT_TYPE_PASSWD:
                pass_token = token
            elif ptype == INPUT_TYPE_TEXT:
                user_token = token

        return user_token, pass_token

    def set_login_username(self, username):
        """
        Sets the username field to the desired value. This requires a login form
        """
        assert self.is_login_form(), 'Login form is required'

        text, passwd, other = self.get_parameter_type_count()
        assert text == 1, 'Login form with username is required'

        for k, v, path, setter in self.iter_setters():
            if self.get_parameter_type(k).lower() == INPUT_TYPE_TEXT:
                setter(username)

    def set_login_password(self, password):
        """
        Sets the password field to the desired value. This requires a login form
        """
        assert self.is_login_form(), 'Login form is required'

        for k, v, path, setter in self.iter_setters():
            if self.get_parameter_type(k).lower() == INPUT_TYPE_PASSWD:
                setter(password)
