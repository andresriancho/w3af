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
import copy

from ruamel.ordereddict import ordereddict as OrderedDict
from types import NoneType

import w3af.core.controllers.output_manager as om

from w3af.core.data.dc.utils.multipart import is_file_like
from w3af.core.data.constants.encodings import DEFAULT_ENCODING
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.parsers.utils.form_id import FormID
from w3af.core.data.parsers.utils.form_fields import (FileFormField,
                                                      get_value_by_key,
                                                      SelectFormField,
                                                      GenericFormField,
                                                      RadioFormField,
                                                      CheckboxFormField)
from w3af.core.data.parsers.utils.form_constants import (DEFAULT_FORM_ENCODING,
                                                         INPUT_TYPE_CHECKBOX,
                                                         INPUT_TYPE_RADIO,
                                                         INPUT_TYPE_TEXT,
                                                         INPUT_TYPE_SELECT,
                                                         INPUT_TYPE_PASSWD,
                                                         INPUT_TYPE_FILE,
                                                         MODE_ALL, MODE_TB,
                                                         MODE_TMB, MODE_T,
                                                         MODE_B)


class FormParameters(OrderedDict):
    """
    This class represents an HTML form, the information is stored as follows:

        * Instance keys are the form parameter names

        * The value for each key is a list containing one or more values for
          the parameter name. This list exists to support repeated parameter
          names.

        * The form meta-data is stored in a different in-memory dict "meta",
          where we store the form parameter type, multiple values (in the case
          of radio/checkbox/select inputs), etc.

    The current value for each parameter is only stored in the main instance,
    not in the "meta" attribute.

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

    OPTION_MATRIX_FORM_TYPES = {INPUT_TYPE_CHECKBOX,
                                INPUT_TYPE_RADIO,
                                INPUT_TYPE_SELECT}

    AVOID_STR_DUPLICATES = {INPUT_TYPE_CHECKBOX,
                            INPUT_TYPE_RADIO,
                            INPUT_TYPE_SELECT}

    def __init__(self, init_vals=(), meta=None, encoding=DEFAULT_ENCODING,
                 method='GET', action=None, form_encoding=DEFAULT_FORM_ENCODING,
                 attributes=None, hosted_at_url=None):
        """

        :param init_vals: Initial form params
        :param meta: Form parameter meta-data (indicates the input type)
        :param encoding: Form encoding
        :param method: GET, POST, etc.
        :param action: URL where the form is sent
        :param form_encoding: url, multipart, etc.
        :param attributes: The form tag attributes as seen in the HTML
        :param hosted_at_url: The URL where the form appeared
        """
        # pylint: disable=E1002
        super(FormParameters, self).__init__(init_vals)
        # pylint: enable=E1002

        # Form parameter meta-data
        self.meta = meta if meta is not None else {}

        # Defaults
        self._autocomplete = None
        self._action = None
        self._method = 'GET'

        # Two completely different types of encoding, first the enctype for the
        # form: multipart/urlencoded, then the charset encoding (UTF-8, etc.)
        self._form_encoding = DEFAULT_FORM_ENCODING
        self._encoding = DEFAULT_ENCODING

        # Call the setters (in a specific order!) so they can mangle the form
        # params if required
        #
        # https://github.com/andresriancho/w3af/issues/11998
        # https://github.com/andresriancho/w3af/issues/11997
        self.set_encoding(encoding)
        self.set_method(method)
        self.set_action(action)
        self.set_form_encoding(form_encoding)

        # We need these for the form-id matching feature
        # https://github.com/andresriancho/w3af/issues/15161
        self._hosted_at_url = hosted_at_url
        self._attributes = attributes

    def get_form_id(self):
        """
        :return: A FormID which can be used to compare two forms
        :see: https://github.com/andresriancho/w3af/issues/15161
        """
        return FormID(action=self._action,
                      inputs=self.meta.keys(),
                      attributes=self._attributes,
                      hosted_at_url=self._hosted_at_url,
                      method=self._method)

    def get_form_encoding(self):
        return self._form_encoding

    def set_form_encoding(self, form_encoding):
        """
        This method is a little bit more complex than I initially expected,
        since it needs to handle cases where the HTML form was created with
        a set of attributes that don't make sense together. For example take
        a look at this:

        <form action="" method="get" enctype="multipart/form-data">
            <input type="text" name="test" value="тест">
            <input type="submit" name="submit">
        </form>

        Chrome and Firefox will send this as a GET request with a query string
        containing both the text and submit params in url-encoded form. This
        means that they override the "user defined" multipart.

        Situations like this triggered bugs:
            https://github.com/andresriancho/w3af/issues/11997
            https://github.com/andresriancho/w3af/issues/11998

        So I had to change the method to be a little bit smarter and override
        the form encoding in specific cases.

        :param form_encoding: The user-defined string in the HTML which
                              specifies the form encoding to use.
        :return:
        """
        if 'multipart/' in form_encoding.lower() and self.get_method() == 'GET':
            form_encoding = DEFAULT_FORM_ENCODING

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
        if not isinstance(action, (URL, NoneType)):
            msg = 'The action of a Form must be of URL type.'
            raise TypeError(msg)
        self._action = action

    def get_autocomplete(self):
        return self._autocomplete

    def set_autocomplete(self, autocomplete):
        if autocomplete in (False, True):
            self._autocomplete = autocomplete
            return

        if autocomplete is None:
            autocomplete = 'on'

        self._autocomplete = False if autocomplete.lower() == 'off' else True

    def get_method(self):
        """
        :return: The Form method.
        """
        return self._method

    def set_method(self, method):
        """
        Form method defaults to GET if not found
        :param method: HTTP method
        :return: None
        """
        self._method = method.upper()

    def has_post_data(self):
        """
        When w3af translates the form params into a request at
        FuzzableRequest.from_form() it uses this method to determine if the
        form parameters are send in the query string or in the post-data

        :return: True if we should send the params in the post-data
        """
        if self.get_method().upper() in ('POST', 'PUT', 'PATCH'):
            return True

        return False

    def get_file_name(self, pname, default=None):
        """
        When the form is created by parsing an HTTP request which contains a
        multipart/form, it is possible to know the name of the file which is
        being uploaded.

        This method returns the name of the file being uploaded given the
        parameter name (pname) where it was sent.
        """
        form_field_list = self.meta.get(pname, None)

        if form_field_list is None:
            return default

        for form_field in form_field_list:
            if isinstance(form_field, FileFormField):
                return form_field.file_name

        return default

    def set_file_name(self, parameter_name, file_name):
        form_field_list = self.meta.get(parameter_name)

        if form_field_list is None:
            raise KeyError('Parameter "%s" not found in form' % parameter_name)

        for form_field in form_field_list:
            if isinstance(form_field, FileFormField):
                form_field.file_name = file_name
                return True

        return False

    def get_file_vars(self):
        """
        :return: The name of the variables which are of file type
        """
        file_keys = set()

        for k, v_lst in self.meta.iteritems():
            for v in v_lst:
                if isinstance(v, FileFormField):
                    file_keys.add(k)

        # pylint: disable=E1133
        for k, v_lst in self.items():
            for v in v_lst:
                if is_file_like(v):
                    file_keys.add(k)
        # pylint: enable=E1133

        return list(file_keys)

    def add_form_field(self, form_field):
        """
        Auxiliary setter for name=value with support repeated parameter names
        """
        form_fields = self.meta.setdefault(form_field.name, [])
        form_fields.append(form_field)

        # pylint: disable=E1101
        form_values = self.setdefault(form_field.name, [])
        form_values.append(form_field.value or '')
        # pylint: enable=E1101

    def add_field_by_attr_items(self, attr_items):
        """
        This method exists for historical reasons only, use add_field_by_attrs
        whenever possible.

        :param attr_items: Items for attr
        :return: The same as add_field_by_attrs
        """
        attrs = dict(attr_items)
        return self.add_field_by_attrs(attrs)

    def add_field_by_attrs(self, attrs):
        """
        Adds an input to the Form object. Input examples:
            <INPUT type="text" name="email"><BR>
            <INPUT type="radio" name="sex" value="Male"> Male<BR>

        :param attrs: attrs=[("class", "screen")]
        """
        should_add_new, form_field = self.form_field_factory(attrs)
        if form_field is None:
            return None

        # Save the form field
        if should_add_new:
            self.add_form_field(form_field)

        # Return what we've created/saved
        return form_field

    def form_field_factory(self, attributes):
        """
        Create a new form field (in most cases) or update an existing FormField
        instance.

        :param attributes: The tag attributes for the newly found form input
        :return: The newly created / updated form field
        """
        input_name = get_value_by_key(attributes, 'name', 'id')

        if input_name is None:
            return False, None

        # shortcut
        snf = self.meta.get(input_name, [])

        # Find the attr type and value, setting the default type to text (if
        # missing in the tag) and the default value to an empty string (if
        # missing)
        input_type = get_value_by_key(attributes, 'type') or INPUT_TYPE_TEXT
        input_type = input_type.lower()

        input_value = get_value_by_key(attributes, 'value') or ''

        autocomplete = get_value_by_key(attributes, 'autocomplete') or ''
        autocomplete = False if autocomplete.lower() == 'off' else True

        should_add_new = True

        if input_type == INPUT_TYPE_SELECT:
            input_values = get_value_by_key(attributes, 'values') or []
            form_field = SelectFormField(input_name, input_values)

        elif input_type == INPUT_TYPE_RADIO:
            match_fields = [ff for ff in snf if ff.input_type is INPUT_TYPE_RADIO]

            if match_fields:
                form_field = match_fields[-1]
                form_field.values.append(input_value)
                should_add_new = False
            else:
                form_field = RadioFormField(input_name, [input_value])

        elif input_type == INPUT_TYPE_CHECKBOX:
            match_fields = [ff for ff in snf if ff.input_type is INPUT_TYPE_CHECKBOX]

            if match_fields:
                form_field = match_fields[-1]
                form_field.values.append(input_value)
                should_add_new = False
            else:
                form_field = CheckboxFormField(input_name, [input_value])

        elif input_type == INPUT_TYPE_FILE:
            file_name = get_value_by_key(attributes, 'filename')
            form_field = FileFormField(input_name,
                                       value=input_value,
                                       file_name=file_name)

        else:
            form_field = GenericFormField(input_type, input_name, input_value,
                                          autocomplete=autocomplete)

        return should_add_new, form_field

    def get_parameter_type(self, input_name, default=INPUT_TYPE_TEXT):
        """
        :return: The input_type for the parameter name
        """
        form_field = self.meta.get(input_name, None)
        if form_field is None:
            return default

        return form_field[0].input_type

    def get_option_names(self):
        option_names = []

        for form_field_list in self.meta.itervalues():
            for form_field in form_field_list:
                if form_field.input_type in self.OPTION_MATRIX_FORM_TYPES:
                    option_names.append(form_field.name)

        return option_names

    def get_option_matrix(self):
        option_matrix = []

        for form_field_list in self.meta.itervalues():
            for form_field in form_field_list:
                if form_field.input_type in self.OPTION_MATRIX_FORM_TYPES:
                    option_matrix.append(form_field.values)

        return option_matrix

    def get_variants(self, mode=MODE_TMB):
        """
        Generate all FormParams' variants by mode:
          'all' - all values
          'tb'  - only top and bottom values
          'tmb' - top, middle and bottom values
          't'   - top values
          'b'   - bottom values
        """
        if mode not in (MODE_ALL, MODE_TB, MODE_TMB, MODE_T, MODE_B):
            raise ValueError('Invalid variants mode: "%s"' % mode)

        yield self

        option_names = self.get_option_names()

        # Nothing to do
        if not option_names:
            return

        matrix = self.get_option_matrix()

        # Build self variant based on `sample_path`
        for sample_path in self._get_sample_paths(mode, matrix):
            # Clone self, don't use copy.deepcopy b/c of perf
            self_variant = self.deepish_copy()

            for option_name_index, option_value_index in enumerate(sample_path):
                option_name = option_names[option_name_index]
                try:
                    value = matrix[option_name_index][option_value_index]
                except IndexError:
                    """
                    This handles "select" tags that have no options inside.

                    The get_variants method should return a variant with the
                    select tag name that is always an empty string.

                    This case reported by Taras at
                    https://sourceforge.net/apps/trac/w3af/ticket/171015
                    """
                    value = ''

                # FIXME: Needs to support repeated parameter names
                self_variant[option_name] = [value]

            yield self_variant

    def _get_sample_paths(self, mode, matrix):
        """
        :param mode: One of the variant modes, as specified by the user
        :param matrix: The form select/radio matrix
        :return: Yield the paths to be used to generate the variants
        """
        if mode in [MODE_T, MODE_TB]:
            yield [0] * len(matrix)

        if mode in [MODE_B, MODE_TB]:
            yield [-1] * len(matrix)

        elif mode in [MODE_TMB, MODE_ALL]:

            variants_total = self._get_variants_count(matrix, mode)

            # Combinatoric explosion. We only want TOP_VARIANTS paths top.
            # Create random sample. We ensure that random sample is unique
            # matrix by using `SEED` in the random generation
            if variants_total > self.TOP_VARIANTS:
                # Inform user
                msg = ('w3af found an HTML form that has several'
                       ' checkbox, radio and select input tags inside.'
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

                variants_total = min(variants_total, self.MAX_VARIANTS_TOTAL)

                for _ in xrange(self.TOP_VARIANTS):
                    path = rand.randint(0, variants_total)
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
        the this algorithm.

        :param path: integer
        :param matrix: list of lists
        :return: Tuple of integers
        """
        # Hack to make the algorithm work.
        matrix.append([1])

        get_count = lambda y: reduce(operator.mul, map(len, matrix[y + 1:]))
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
        :param mode: One of the variant modes, as specified by the user
        :param matrix: The form select/radio matrix
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
        init_val = copy.deepcopy(self.items())
        self_copy = FormParameters(init_vals=init_val,
                                   meta=self.meta,
                                   attributes=self._attributes,
                                   hosted_at_url=self._hosted_at_url)

        # Internal variables
        self_copy.set_method(self.get_method())
        self_copy.set_action(self.get_action())
        self_copy.set_autocomplete(self.get_autocomplete())
        self_copy.set_form_encoding(self.get_form_encoding())
        self_copy.set_encoding(self.get_encoding())

        return self_copy

    def __reduce__(self):
        items = [(k, self[k]) for k in self]
        inst_dict = vars(self).copy()
        inst_dict.pop('_keys', None)

        encoding = self.get_encoding()

        return self.__class__, (items, encoding), inst_dict

    def __repr__(self):
        items = []

        # pylint: disable=E1133
        for key, value_list in self.iteritems():
            for value in value_list:
                kv = "'%s': '%s'" % (key, value)
                items.append(kv)
        # pylint: enable=E1133

        data = ', '.join(items)

        args = (self._method, self._action, data)
        return '<FormParams (%s %s {%s})>' % args

    def get_parameter_type_count(self):
        passwd = text = other = 0

        #
        # Count the parameter types
        #
        for form_field_list in self.meta.itervalues():
            for form_field in form_field_list:

                if form_field.input_type == INPUT_TYPE_PASSWD:
                    passwd += 1
                elif form_field.input_type == INPUT_TYPE_TEXT:
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
