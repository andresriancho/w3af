"""
form_id_matcher_list.py

Copyright 2017 Andres Riancho

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
import json

from w3af.core.data.parsers.utils.form_id_matcher import FormIDMatcher


class FormIDMatcherList(object):
    """
    This class contains a list of form id objects that the user wants to match.
    It is used to parse the string provided by the user in the misc-settings.

    In most cases this class is constructed from user-configured json object
    such as:

        [{"action":"/products/.*",
          "inputs": ["comment"],
          "method": "get",
          "attributes": {"class": "comments-form"},
          "hosted_at_url": "/products/.*"}]

    And then used in a call to FormID.matches_one_of(...)

    :see: https://github.com/andresriancho/w3af/issues/15161
    """
    def __init__(self, form_id_list_as_str):
        """
        :param form_id_list_as_str: The form ids as a string. This comes from
                                    the user, so lots of care must be taken
                                    to parse and validate it.
        """
        self._form_ids = []

        try:
            form_id_list = json.loads(form_id_list_as_str)
        except ValueError:
            raise ValueError('The form ID list must be a valid JSON.')

        if not isinstance(form_id_list, list):
            raise ValueError('The form ID list must be a JSON list.')

        # Now we have a list containing _something_ that should be form-ids
        # we translate those into real objects and set them in the internal
        # list
        for json_list_item in form_id_list:

            # This will raise exceptions, and its ok
            form_id = FormIDMatcher.from_json_list_data(json_list_item)
            self._form_ids.append(form_id)

    def get_form_ids(self):
        return self._form_ids

    def to_json(self):
        return json.dumps([f.to_dict() for f in self._form_ids])

    def __str__(self):
        return self.to_json()

