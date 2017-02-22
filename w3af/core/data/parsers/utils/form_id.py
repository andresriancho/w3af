"""
form_id.py

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

from collections import OrderedDict


class FormID(object):
    """
    This class describes the form attributes. This is usually used to call
    FormID.matches(FormIDMatcher) to verify if a form should be crawled or
    not.

    :see: https://github.com/andresriancho/w3af/issues/15161
    """
    def __init__(self, action=None, inputs=None, attributes=None,
                 hosted_at_url=None, method=None):
        """
        :param action: URL (object) where the form is sent
        :param inputs: A list with the names of the form parameters
        :param attributes: The form tag attributes as seen in the HTML
        :param hosted_at_url: The URL (object) where the form appeared
        :param method: The HTTP method used to submit the form
        """
        self.action = action
        self.inputs = inputs
        self.attributes = attributes
        self.hosted_at_url = hosted_at_url
        self.method = method

    def matches_one_of(self, form_matcher_list):
        for form_matcher in form_matcher_list.get_form_ids():
            if self.matches(form_matcher):
                return True

        return False

    def matches(self, form_matcher):
        """
        :param form_matcher: A FormIDMatcher instance as configured by the user
        :return: True if the other form matches self according to the rules
                 defined in https://github.com/andresriancho/w3af/issues/15161
        """
        # First we check the things which take less time, if these fail, we return
        # quickly and have less performance impact
        if form_matcher.inputs is not None:
            for input_name in form_matcher.inputs:
                if input_name not in self.inputs:
                    return False

        if form_matcher.attributes is not None:
            self_attribute_values = self.attributes.items()
            for attribute, attribute_value in form_matcher.attributes.iteritems():
                if (attribute, attribute_value) not in self_attribute_values:
                    return False

        if form_matcher.method is not None and self.method is not None:
            if form_matcher.method.lower() != self.method.lower():
                return False

        # Now we match the slower things, which have more impact on performance
        if form_matcher.action is not None:
            action_url_path = self.action.get_path()
            if not form_matcher.action.match(action_url_path):
                return False

        if form_matcher.hosted_at_url is not None:
            hosted_at_url_path = self.hosted_at_url.get_path()
            if not form_matcher.hosted_at_url.match(hosted_at_url_path):
                return False

        return True

    def to_json(self):
        """
        We need to let the user know which new forms we've found. In order to
        do that we just convert this object to JSON and print it to the logs.

        :return: This object as a JSON dict
        """
        data = OrderedDict([('action', self.action.get_path()),
                            ('hosted_at_url', self.hosted_at_url.get_path()),
                            ('inputs', self.inputs),
                            ('attributes', self.attributes),
                            ('method', self.method)])
        return json.dumps(data)
