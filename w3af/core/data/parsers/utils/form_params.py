# -*- coding: utf8 -*-
"""
form_params.py

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
import operator
import random

from ruamel.ordereddict import ordereddict as OrderedDict

import w3af.core.controllers.output_manager as om
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.dc.utils.multipart import is_file_like
from w3af.core.data.parsers.doc.url import URL


DEFAULT_FORM_ENCODING = 'application/x-www-form-urlencoded'

INPUT_TYPE_FILE = 'file'
INPUT_TYPE_CHECKBOX = 'checkbox'
INPUT_TYPE_RADIO = 'radio'
INPUT_TYPE_TEXT = 'text'
INPUT_TYPE_HIDDEN = 'hidden'
INPUT_TYPE_SUBMIT = 'submit'
INPUT_TYPE_SELECT = 'select'
INPUT_TYPE_PASSWD = 'password'

ALL_INPUT_TYPES = (INPUT_TYPE_FILE, INPUT_TYPE_CHECKBOX, INPUT_TYPE_RADIO,
                   INPUT_TYPE_TEXT, INPUT_TYPE_HIDDEN, INPUT_TYPE_SUBMIT,
                   INPUT_TYPE_SELECT, INPUT_TYPE_PASSWD)

MODE_ALL = 'all'
MODE_TB = 'tb'
MODE_TMB = 'tmb'
MODE_T = 't'
MODE_B = 'b'


class FormField(object):

    __slots__ = ('input_type', 'name', 'value', 'autocomplete')

    def __init__(self, input_type, name, value, autocomplete=False):
        self.input_type = input_type
        self.name = name
        self.value = value
        self.autocomplete = autocomplete


class FormParameters(OrderedDict):
    """
    This class represents an HTML form.

    :author: Andres Riancho (andres.riancho@gmail.com) |
             Javier Andalia (jandalia =at= gmail.com)
    """
    # Max
    TOP_VARIANTS = 15
    MAX_VARIANTS_TOTAL = 10 ** 9
    SEED = 1

    AVOID_FILLING_FORM_TYPES = {INPUT_TYPE_CHECKBOX,
                                INPUT_TYPE_RADIO,
                                INPUT_TYPE_SELECT}

    AVOID_STR_DUPLICATES = {INPUT_TYPE_CHECKBOX,
                            INPUT_TYPE_RADIO,
                            INPUT_TYPE_SELECT}

    def __init__(self, init_vals=(), encoding=DEFAULT_ENCODING):
        super(FormParameters, self).__init__(init_vals)

        # Internal variables
        # Form method defaults to GET if not found
        self._method = 'GET'
        self._action = None
        self._autocomplete = None

        # Two completely different types of encoding, first the enctype for the
        # form: multipart/urlencoded, then the charset encoding (UTF-8, etc.)
        self._form_encoding = DEFAULT_FORM_ENCODING
        self._encoding = encoding

    def get_form_encoding(self):
        return self._form_encoding

    def set_form_encoding(self, form_encoding):
        self._form_encoding = form_encoding

    def get_encoding(self):
        return self._encoding

    def set_encoding(self, new_encoding):
        self._encoding = new_encoding

    def get_action(self):
        """
        :return: The Form action.
        """
        return self._action

    def set_action(self, action):
        if not isinstance(action, URL):
            msg = 'The action of a Form must be of url.URL type.'
            raise TypeError(msg)
        self._action = action

    def get_autocomplete(self):
        return self._autocomplete

    def set_autocomplete(self, autocomplete):
        self._autocomplete = autocomplete

    def get_method(self):
        """
        :return: The Form method.
        """
        return self._method

    def set_method(self, method):
        self._method = method.upper()

    def get_file_name(self, pname, default=None):
        """
        When the form is created by parsing an HTTP request which contains a
        multipart/form, it is possible to know the name of the file which is
        being uploaded.

        This method returns the name of the file being uploaded given the
        parameter name (pname) where it was sent.
        """
        #TODO
        return self._file_names.get(pname, default)

    def set_file_name(self, pname, fname):
        #TODO
        self._file_names[pname] = fname

    def get_file_vars(self):
        """
        :return: The name of the variables which are of file type
        """
        file_keys = []

        for k, v_lst in self.items():
            for v in v_lst:
                if is_file_like(v):
                    file_keys.append(k)

        return file_keys

    def setdefault_var(self, form_name, form_field):
        """
        Auxiliary setter for name=value with support repeated parameter names
        """
        form_fields = self.setdefault(form_name, [])
        form_fields.append(form_field)

    def add_input(self, attrs):
        """
        Adds an input to the Form object. Input examples:
            <INPUT type="text" name="email"><BR>
            <INPUT type="radio" name="sex" value="Male"> Male<BR>

        :param attrs: attrs=[("class", "screen")]
        """
        input_name = get_value_by_key(attrs, 'name', 'id')

        if not input_name:
            # Nothing to add
            return '', ''

        # Find the attr type and value, setting the default type to text (if
        # missing in the tag) and the default value to an empty string (if
        # missing)
        input_type = self.get_value_by_key(attrs, 'type') or self.INPUT_TYPE_TEXT
        input_type = input_type.lower()

        input_value = get_value_by_key(attrs, 'value') or ''

        autocomplete = get_value_by_key(attrs, 'autocomplete') or None
        autocomplete = False if autocomplete.lower() == 'off' else True

        form_field = FormField(input_type, input_name, input_value,
                               autocomplete=autocomplete)

        # Save the attr_type
        self[input_name] = form_field

        # Return what we've saved
        return input_name, input_value

    def get_parameter_type(self, input_name, default=INPUT_TYPE_TEXT):
        """
        :return: The input_type for the parameter name
        """
        form_field = self.get(input_name, None)
        if form_field is None:
            return default

        return form_field.input_type

    def get_variants(self, mode=MODE_TMB):
        """
        Generate all Form's variants by mode:
          "all" - all values
          "tb" - only top and bottom values
          "tmb" - top, middle and bottom values
          "t" - top values
          "b" - bottom values
        """
        if mode not in (MODE_ALL, MODE_TB, MODE_TMB, MODE_T, MODE_B):
            raise ValueError('Invalid mode')

        yield self

        # Nothing to do
        if not self._selects:
            return

        secret_value = self.SECRET_VALUE
        sel_names = self._selects.keys()
        matrix = self._selects.values()

        # Build self variant based on `sample_path`
        for sample_path in self._get_sample_paths(mode, matrix):
            # Clone self, don't use copy.deepcopy b/c of perf
            self_variant = self.deepish_copy()

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

    def _get_sample_paths(self, mode, matrix):

        if mode in [MODE_T, MODE_TB]:
            yield [0] * len(matrix)

        if mode in [MODE_B, MODE_TB]:
            yield [-1] * len(matrix)
        # mode in [MODE_TMB, MODE_ALL]
        elif mode in [MODE_TMB, MODE_ALL]:

            variants_total = self._get_variants_count(matrix, mode)

            # Combinatoric explosion. We only want TOP_VARIANTS paths top.
            # Create random sample. We ensure that random sample is unique
            # matrix by using `SEED` in the random generation
            if variants_total > self.TOP_VARIANTS:
                # Inform user
                msg = ('w3af found an HTML form that has several'
                       'checkbox, radio and select input tags inside.'
                       ' Testing all combinations of those values would'
                       ' take too much time, the framework will only'
                       ' test %s randomly distributed variants.')
                om.out.debug(msg % self.TOP_VARIANTS)

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
                    yield self._decode_path(path, matrix)

            # Less than TOP_VARIANTS elems in matrix
            else:
                # Compress matrix dimensions to (N x Mc) where 1 <= Mc <=3
                if mode == MODE_TMB:
                    for row, vector in enumerate(matrix):
                        # Create new 3-length vector
                        if len(vector) > 3:
                            new_vector = [vector[0],
                                          vector[len(vector) / 2],
                                          vector[-1]]
                            matrix[row] = new_vector

                    # New variants total
                    variants_total = self._get_variants_count(matrix, mode)

                # Now get all paths!
                for path in xrange(variants_total):
                    decoded_path = self._decode_path(path, matrix)
                    yield decoded_path

    def _decode_path(self, path, matrix):
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

    def _get_variants_count(self, matrix, mode):
        """

        :param matrix:
        :param tmb:
        """
        if mode in [MODE_T, MODE_B]:
            return 1
        elif mode == MODE_TB:
            return 2
        else:
            len_fun = (lambda x: min(len(x), 3)) if mode == MODE_TMB else len
            return reduce(operator.mul, map(len_fun, matrix))

    def deepish_copy(self):
        """
        This method returns a deep copy of the Form instance. I'm NOT using
        copy.deepcopy(self) here because its very slow!

        :return: A copy of myself.
        """
        init_val = deepish_copy(self).items()
        copy = FormParameters()
        copy.update(init_val)

        # Internal variables
        copy._method = self._method
        copy._action = self._action
        copy._autocomplete = self._autocomplete
        copy._form_encoding = self._form_encoding
        copy._encoding = self._encoding

        return copy

    def __reduce__(self):
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)

        encoding = self.get_encoding()

        return self.__class__, (items, encoding), inst_dict

    #def __repr__(self):
    #    args = (id(self), self._method, self._action, self.keys())
    #    return '<FormParams(%s) %s %s %s>' % args

    def get_parameter_type_count(self):
        passwd = text = other = 0

        #
        # Count the parameter types
        #
        for _, form_field in self.items():

            if form_field.input_type == self.INPUT_TYPE_PASSWD:
                passwd += 1
            elif form_field.input_type == self.INPUT_TYPE_TEXT:
                text += 1
            else:
                other += 1

        return text, passwd, other

    def is_login_form(self):
        """
        :return: True if this is a login form.
        """
        text, passwd, other = self.get_parameter_type_count()

        # Classic login form
        if text == 1 and passwd == 1:
            return True

        # Password-only login form
        elif text == 0 and passwd == 1:
            return True

        return False

    def is_registration_form(self):
        """
        :return: True if this is a registration form, a text input (user) and
                 two password fields (passwd and confirmation)
        """
        text, passwd, other = self.get_parameter_type_count()
        if passwd == 2 and text >= 1:
            return True

        return False

    def is_password_change_form(self):
        """
        :return: True if this is a password change form containing:
                    * Old password
                    * New password
                    * Confirm
        """
        text, passwd, other = self.get_parameter_type_count()
        if passwd == 3:
            return True

        return False


def deepish_copy(org):
    """
    Much, much faster than deepcopy, for a dict of the simple python types.

    http://writeonly.wordpress.com/2009/05/07/deepcopy-is-a-pig-for-simple-data/
    """
    out = OrderedDict().fromkeys(org)

    for k, v in org.iteritems():
        try:
            out[k] = v.copy()   # dicts, sets
        except AttributeError:
            try:
                out[k] = v[:]   # lists, tuples, strings, unicode
            except TypeError:
                out[k] = v      # ints

    return out


def get_value_by_key(attrs, *args):
    """
    Helper to get attributes

    :param attrs: The attributes for input
    :param args: The attributes we want to query
    :return: The first value for the attribute specified in args
    """
    for search_attr_key in args:
        for attr in attrs:
            if attr[0] == search_attr_key:
                return attr[1]
    return None
