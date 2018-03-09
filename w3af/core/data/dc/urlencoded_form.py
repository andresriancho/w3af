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
from w3af.core.data.dc.generic.form import Form
from w3af.core.data.parsers.utils.encode_decode import urlencode
from w3af.core.data.parsers.doc.url import parse_qs
from w3af.core.data.parsers.utils.form_fields import GenericFormField
from w3af.core.data.parsers.utils.form_constants import (INPUT_TYPE_CHECKBOX,
                                                         INPUT_TYPE_RADIO,
                                                         INPUT_TYPE_TEXT,
                                                         INPUT_TYPE_SELECT)


class URLEncodedForm(Form):
    """
    This class represents an HTML form.

    :author: Andres Riancho (andres.riancho@gmail.com) |
             Javier Andalia (jandalia =at= gmail.com)
    """
    ENCODING = 'application/x-www-form-urlencoded'

    AVOID_FILLING_FORM_TYPES = {'checkbox', 'radio', 'select'}
    AVOID_STR_DUPLICATES = {INPUT_TYPE_CHECKBOX,
                            INPUT_TYPE_RADIO,
                            INPUT_TYPE_SELECT}

    @staticmethod
    def content_type_matches(headers):
        conttype, header_name = headers.iget('content-type', '')
        return URLEncodedForm.ENCODING in conttype.lower()

    @staticmethod
    def can_parse(post_data):
        try:
            parse_qs(post_data)
        except:
            return False
        else:
            return True

    @classmethod
    def from_postdata(cls, headers, post_data):
        if not URLEncodedForm.content_type_matches(headers):
            raise ValueError('Request is not %s.' % URLEncodedForm.ENCODING)

        if not URLEncodedForm.can_parse(post_data):
            raise ValueError('Failed to parse post_data as Form.')

        parsed_data = parse_qs(post_data)
        urlencoded_form = cls()

        for key, value_list in parsed_data.iteritems():
            for value in value_list:
                form_field = GenericFormField(INPUT_TYPE_TEXT, key, value)
                urlencoded_form.add_form_field(form_field)

        return urlencoded_form

    def __str__(self):
        """
        This method returns a string representation of the Form object.

        Please note that if the form has radio/select/checkboxes the
        first value will be put into the string representation and the
        others will be lost.

        :see: Unittest in test_form.py
        :return: string representation of the Form object.
        """
        d = dict()
        d.update(self.items())

        for key in d:
            key_type = self.get_parameter_type(key, default=None)
            if key_type in self.AVOID_STR_DUPLICATES:
                d[key] = d[key][:1]

        return urlencode(d, encoding=self.encoding, safe='')

    def get_type(self):
        return 'URL encoded form'

