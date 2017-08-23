# -*- coding: utf-8 -*-
"""
data_container.py

Copyright 2014 Andres Riancho

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
import copy

from itertools import chain, izip_longest

from w3af.core.data.db.disk_item import DiskItem
from w3af.core.data.constants.encodings import UTF8
from w3af.core.data.dc.utils.token import DataToken
from w3af.core.data.misc.encoding import smart_str_ignore


class DataContainer(DiskItem):
    MAX_PRINTABLE = 65

    def __init__(self, encoding=UTF8):
        super(DataContainer, self).__init__()
        self.encoding = encoding
        self.token = None

    def get_encoding(self):
        return self.encoding

    def get_type(self):
        return 'Generic data container'

    @classmethod
    def from_postdata(cls, headers, post_data):
        raise NotImplementedError

    def _to_str_with_separators(self, key_val_sep, pair_sep):
        """
        :warning: The subclass needs to implement it
        """
        raise NotImplementedError

    def token_filter(self, token_path, token_value):
        """
        This function is called when iterating over tokens, only tokens which
        match the filter (return True) are going to be included in the result.

        By default all tokens are included.

        iter_setters is the only method which should filter tokens based on
        this method, all other token iterators use iter_setter internally, so
        they are going to receive the benefits.

        :param token_path: A tuple with the path to the token, ie. ('a', 0)
        :param token_value: The value for this token, ie. 'foobar'
        """
        return True

    def get_token(self):
        return self.token

    def set_token(self, set_token_path):
        """
        Sets the token in the DataContainer to point to the variable specified
        in set_token_path. Usually set_token_path will be one of:
            * ('id',) - When the data container doesn't support repeated params
            * ('id', 3) - When it does
            * A DataToken instance which holds the path

        :raises: An exception when the DataContainer does NOT contain the
                 specified path in *args to find the variable
        :return: The token if we were able to set it in the DataContainer
        """
        override_token = False
        try:
            # Try to get the path from the parameter, if it is a DataToken
            # instance this will succeed.
            token_path = set_token_path.get_path()
            override_token = True
        except AttributeError:
            token_path = set_token_path

        for key, val, i_token_path, setter in self.iter_setters():
            if i_token_path == token_path:

                if override_token:
                    # Use token provided in parameter
                    token = set_token_path

                elif isinstance(val, DataToken):
                    # We've already done a set_token(...) for this token path
                    # in the past, and now we're doing it again. Don't double
                    # wrap the pre-existing token!
                    token = val
                else:
                    token = DataToken(key, val, i_token_path)

                setter(token)
                self.token = token

                return token

        path_str = lambda path: '(%s)' % ', '.join([smart_str_ignore(i) for i in path])
        ppath = path_str(token_path)
        vpath = ' - '.join([path_str(p) for _, _, p, _ in self.iter_setters()])

        if vpath:
            msg = 'Invalid token path "%s". Valid paths are: %s'
            raise RuntimeError(msg % (ppath, vpath))
        else:
            msg = 'Invalid token path "%s". No valid paths for "%s"'
            raise RuntimeError(msg % (ppath, self.get_type()))

    def iter_tokens(self):
        """
        DataToken instances unbound to any data container are (mostly)
        useless. Most likely you should use iter_bound_tokens

        :yield: DataToken instances to help in the fuzzing process of this
                DataContainer.
        """
        for key, val, token_path, setter in self.iter_setters():
            if self.token_filter(token_path, val):
                yield DataToken(key, val, token_path)

    def iter_bound_tokens(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/580
        :see: Mostly used in Mutant._create_mutants_worker
        :yield: Tuples with:
                    - A copy of self
                    - A token set to the right location in the copy of self
        """
        for key, val, token_path, setter in self.iter_setters():
            dcc = copy.deepcopy(self)
            token = dcc.set_token(token_path)

            yield dcc, token

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The key as a string
                    * The value as a string
                    * The setter to modify the value
        """
        raise NotImplementedError

    def get_param_names(self):
        """
        :return: A list with the names of the parameters for this DataContainer,
                 while this sounds easy there are some cases like JSON or
                 XMLRPC data containers where it actually requires some work
                 to be done.
        """
        return [t.get_name() for t in self.iter_tokens()]

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self which is
                 shorter in length than MAX_PRINTABLE
        """
        raise NotImplementedError

    def is_variant_of(self, other):
        """
        :return: True if self and other are both of the same DataContainer type,
                 have the same token names, and for each token the type (int or
                 string) is the same.
        """
        for tself, tother in izip_longest(chain(self.iter_tokens()),
                                          chain(other.iter_tokens()),
                                          fillvalue=None):
            if None in (tself, tother):
                # One data container has more parameters than the other one
                return False

            if tself.get_name() != tother.get_name():
                # The names of the parameters need to be the same (and in the
                # same order too)
                return False

            try:
                digit_self = tself.get_value().isdigit()
                digit_other = tother.get_value().isdigit()
            except AttributeError:
                # In some cases the value is not a string, so it doesn't have
                # the isdigit method, we don't know how to compare these, so
                # we just return False
                return False

            if digit_other != digit_self:
                return False

        return True

    def get_headers(self):
        """
        Override in sub-classes with care.

        :return: A tuple list with the headers required to send the
                 self._post_data to the wire. For example, if the data is
                 url-encoded:
                    a=3&b=2

                 This method returns:
                    Content-Length: 7
                    Content-Type: application/x-www-form-urlencoded

                 When someone queries this object for the headers using
                 get_headers(), we'll include these. Hopefully this means that
                 the required headers will make it to the wire.
        """
        return []

    @property
    def all_items(self):
        return str(self)

    def get_eq_attrs(self):
        return ['all_items']

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        """
        DataContainer sub-classes need to implement the __str__ method to be
        able to serialize themselves to be sent to the wire.

        __str__ will need to work together with get_headers() to create
        something that makes sense on the other side.
        """
        raise NotImplementedError