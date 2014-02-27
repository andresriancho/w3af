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
import operator
import random

import w3af.core.controllers.output_manager as om

from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.dc.data_container import DataContainer
from w3af.core.data.parsers.encode_decode import urlencode
from w3af.core.data.parsers.url import URL


class Form(DataContainer):
    """
    This class represents a HTML form.

    :author: Andres Riancho (andres.riancho@gmail.com) |
             Javier Andalia (jandalia =at= gmail.com)
    """
    # Max
    TOP_VARIANTS = 15
    MAX_VARIANTS_TOTAL = 10 ** 9
    SEED = 1

    INPUT_TYPE_FILE = 'file'
    INPUT_TYPE_CHECKBOX = 'checkbox'
    INPUT_TYPE_RADIO = 'radio'
    INPUT_TYPE_TEXT = 'text'
    INPUT_TYPE_HIDDEN = 'hidden'
    INPUT_TYPE_SUBMIT = 'submit'
    INPUT_TYPE_SELECT = 'select'

    def __init__(self, init_val=(), encoding=DEFAULT_ENCODING):
        super(Form, self).__init__(init_val, encoding)

        # Internal variables
        self._method = None
        self._action = None
        self._types = {}
        self._files = []
        self._selects = {}
        self._submit_map = {}

        # This is used for processing checkboxes
        self._secret_value = "3_!21#47w@"

    def get_action(self):
        """
        :return: The Form action.
        """
        return self._action

    def set_action(self, action):
        """
        >>> f = Form()
        >>> f.set_action('http://www.google.com/')
        Traceback (most recent call last):
          ...
        TypeError: The action of a Form must be of url.URL type.
        >>> f = Form()
        >>> action = URL('http://www.google.com/')
        >>> f.set_action(action)
        >>> f.get_action() == action
        True
        """
        if not isinstance(action, URL):
            raise TypeError('The action of a Form must be of '
                            'url.URL type.')
        self._action = action

    def get_method(self):
        """
        :return: The Form method.
        """
        return self._method

    def set_method(self, method):
        self._method = method.upper()

    def get_file_vars(self):
        return self._files

    def _set_var(self, name, value):
        """
        Auxiliary setter for name=value
        """
        # added to support repeated parameter names
        vals = self.setdefault(name, [])
        vals.append(value)

    def add_file_input(self, attrs):
        """
        Adds a file input to the Form
        :param attrs: attrs=[("class", "screen")]
        """
        name = ''

        for attr in attrs:
            if attr[0] == 'name':
                name = attr[1]
                break

        if not name:
            for attr in attrs:
                if attr[0] == 'id':
                    name = attr[1]
                    break

        if name:
            self._files.append(name)
            self._set_var(name, '')
            # TODO: This does not work if there are different parameters in a form
            # with the same name, and different types
            self._types[name] = self.INPUT_TYPE_FILE

    def __str__(self):
        """
        This method returns a string representation of the Form object.

        Please note that if the form has radio/select/checkboxes the
        first value will be put into the string representation and the
        others will be lost.

        @see: Unittest in test_form.py
        :return: string representation of the Form object.
        """
        d = dict(self)
        d.update(self._submit_map)

        avoid_duplicates = (self.INPUT_TYPE_CHECKBOX, self.INPUT_TYPE_RADIO,
                            self.INPUT_TYPE_SELECT)

        for key in d:
            key_type = self._types.get(key, None)
            if key_type in avoid_duplicates:
                d[key] = d[key][:1]

        return urlencode(d, encoding=self.encoding)

    def add_submit(self, name, value):
        """
        This is something I hadn't thought about !
        <input type="submit" name="b0f" value="Submit Request">
        """
        self._submit_map[name] = value

    def add_input(self, attrs):
        """
        Adds an input to the Form object. Input examples:
            <INPUT type="text" name="email"><BR>
            <INPUT type="radio" name="sex" value="Male"> Male<BR>

        :param attrs: attrs=[("class", "screen")]
        """
        # Set the default input type to text.
        attr_type = self.INPUT_TYPE_TEXT
        name = value = ''

        # Try to get the name:
        for attr in attrs:
            if attr[0] == 'name':
                name = attr[1]
        if not name:
            for attr in attrs:
                if attr[0] == 'id':
                    name = attr[1]

        if not name:
            return (name, value)

        # Find the attr_type
        for attr in attrs:
            if attr[0] == 'type':
                attr_type = attr[1].lower()

        # Find the default value
        for attr in attrs:
            if attr[0] == 'value':
                value = attr[1]

        if attr_type == self.INPUT_TYPE_SUBMIT:
            self.add_submit(name, value)
        else:
            self._set_var(name, value)

        # Save the attr_type
        self._types[name] = attr_type

        #
        # TODO May be create special internal method instead of using
        # add_input()?
        #
        return (name, value)

    def get_type(self, name):
        return self._types[name]

    def add_check_box(self, attrs):
        """
        Adds checkbox field
        """
        name, value = self.add_input(attrs)

        if not name:
            return

        if name not in self._selects:
            self._selects[name] = []

        if value not in self._selects[name]:
            self._selects[name].append(value)
            self._selects[name].append(self._secret_value)

        self._types[name] = self.INPUT_TYPE_CHECKBOX

    def add_radio(self, attrs):
        """
        Adds radio field
        """
        name, value = self.add_input(attrs)

        if not name:
            return

        self._types[name] = self.INPUT_TYPE_RADIO

        if name not in self._selects:
            self._selects[name] = []

        #
        # FIXME: how do you maintain the same value in self._selects[name]
        # and in self[name] ?
        #
        if value not in self._selects[name]:
            self._selects[name].append(value)

    def add_select(self, name, options):
        """
        Adds one more select field with options
        Options is list of options attrs (tuples)
        """
        if not name:
            return

        self._selects.setdefault(name, [])
        self._types[name] = self.INPUT_TYPE_SELECT

        value = ""
        for option in options:
            for attr in option:
                if attr[0].lower() == "value":
                    value = attr[1]
                    self._selects[name].append(value)

        self._set_var(name, value)

    def get_variants(self, mode="tmb"):
        """
        Generate all Form's variants by mode:
          "all" - all values
          "tb" - only top and bottom values
          "tmb" - top, middle and bottom values
          "t" - top values
          "b" - bottom values
        """

        if mode not in ("all", "tb", "tmb", "t", "b"):
            raise ValueError("mode must be in ('all', 'tb', 'tmb', 't', 'b')")

        yield self

        # Nothing to do
        if not self._selects:
            return

        secret_value = self._secret_value
        sel_names = self._selects.keys()
        matrix = self._selects.values()

        # Build self variant based on `sample_path`
        for sample_path in self._getSamplePaths(mode, matrix):
            # Clone self
            self_variant = self.copy()

            for row_index, col_index in enumerate(sample_path):
                sel_name = sel_names[row_index]
                try:
                    value = matrix[row_index][col_index]
                except IndexError:
                    """
                    This handles "select" tags that have no options inside.

                    The get_variants method should return a variant with the
                    select tag name that is always an empty string.

                    This case reported by Taras at
                    https://sourceforge.net/apps/trac/w3af/ticket/171015
                    """
                    value = ''

                if value != secret_value:
                    # FIXME: Needs to support repeated parameter names
                    self_variant[sel_name] = [value]
                else:
                    # FIXME: Is it solution good? Simply delete unwanted
                    #        send checkboxes?
                    #
                    # We might had removed it before
                    if self_variant.get(sel_name):
                        del self_variant[sel_name]

            yield self_variant

    def _getSamplePaths(self, mode, matrix):

        if mode in ["t", "tb"]:
            yield [0] * len(matrix)

        if mode in ["b", "tb"]:
            yield [-1] * len(matrix)
        # mode in ["tmb", "all"]
        elif mode in ["tmb", "all"]:

            variants_total = self._get_variantsCount(matrix, mode)

            # Combinatoric explosion. We only want TOP_VARIANTS paths top.
            # Create random sample. We ensure that random sample is unique
            # matrix by using `SEED` in the random generation
            if variants_total > self.TOP_VARIANTS:
                # Inform user
                om.out.information("w3af found an HTML form that has several"
                                   " checkbox, radio and select input tags inside. Testing "
                                   "all combinations of those values would take too much "
                                   "time, the framework will only test %s randomly "
                                   "distributed variants." % self.TOP_VARIANTS)

                # Init random object. Set our seed so we get the same variants
                # in two runs. This is important for users because they expect
                # the tool to find the same vulnerabilities in two consecutive
                # scans!
                rand = random.Random()
                rand.seed(self.SEED)

                # xrange in python2 has the following issue:
                # >>> xrange(10**10)
                # Traceback (most recent call last):
                # File "<stdin>", line 1, in <module>
                # OverflowError: long int too large to convert to int
                #
                # Which was amazingly reported by one of our users
                # http://sourceforge.net/apps/trac/w3af/ticket/161481
                #
                # Given that we want to test SOME of the combinations we're
                # going to settle with a rand.sample from the first
                # MAX_VARIANTS_TOTAL (=10**9) items (that works in python2)
                #
                # >>> xrange(10**9)
                # xrange(1000000000)
                # >>>

                variants_total = min(variants_total, self.MAX_VARIANTS_TOTAL)

                for path in rand.sample(xrange(variants_total),
                                        self.TOP_VARIANTS):
                    yield self._decodePath(path, matrix)

            # Less than TOP_VARIANTS elems in matrix
            else:
                # Compress matrix dimensions to (N x Mc) where 1 <= Mc <=3
                if mode == "tmb":
                    for row, vector in enumerate(matrix):
                        # Create new 3-length vector
                        if len(vector) > 3:
                            new_vector = [vector[0]]
                            new_vector.append(vector[len(vector) / 2])
                            new_vector.append(vector[-1])
                            matrix[row] = new_vector

                    # New variants total
                    variants_total = self._get_variantsCount(matrix, mode)

                # Now get all paths!
                for path in xrange(variants_total):
                    decoded_path = self._decodePath(path, matrix)
                    yield decoded_path

    def _decodePath(self, path, matrix):
        """
        Decode the integer `path` into a tuple of ints where the ith-elem
        is the index to select from vector given by matrix[i].

        Diego Buthay (dbuthay@gmail.com) made a significant contribution to
        the used algorithm.

        :param path: integer
        :param matrix: list of lists
        :return: Tuple of integers
        """
        # Hack to make the algorithm work.
        matrix.append([1])
        get_count = lambda i: reduce(operator.mul, map(len, matrix[i + 1:]))
        remainder = path
        decoded_path = []

        for i in xrange(len(matrix) - 1):
            base = get_count(i)
            decoded_path.append(remainder / base)
            remainder = remainder % base

        # Restore state, pop out [1]
        matrix.pop()

        return decoded_path

    def _get_variantsCount(self, matrix, mode):
        """

        :param matrix:
        :param tmb:
        """
        if mode in ["t", "b"]:
            return 1
        elif mode == "tb":
            return 2
        else:
            len_fun = (lambda x: min(len(x), 3)) if mode == "tmb" else len
            return reduce(operator.mul, map(len_fun, matrix))
