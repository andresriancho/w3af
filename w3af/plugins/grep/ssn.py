"""
ssn.py

Copyright 2008 Andres Riancho

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
import re
import itertools

from w3af.core.controllers.plugins.grep_plugin import GrepPlugin
from w3af.core.data.kb.vuln import Vuln
from w3af.plugins.grep.ssndata.ssnAreasGroups import areas_groups_map

import w3af.core.data.constants.severity as severity


class ssn(GrepPlugin):
    """
    This plugin detects the occurence of US Social Security numbers in web pages.

    :author: dliz <dliz !at! users.sourceforge.net>
    """
    # match numbers of the form: 'nnn-nn-nnnn' with some extra restrictions
    regex = ('(?:^|[^\d-])(?!(000|666))([0-6]\d{2}|7([0-6]\d|7[012]))'
             ' ?-? ?(?!00)(\d{2}) ?-? ?(?!0000)(\d{4})(?:^|[^\d-])')
    ssn_regex = re.compile(regex)

    def __init__(self):
        GrepPlugin.__init__(self)

    def grep(self, request, response):
        """
        Plugin entry point, find the SSN numbers.

        :param request: The HTTP request object.
        :param response: The HTTP response object
        :return: None.
        """
        if response.get_code() != 200:
            return

        if not response.is_text_or_html():
            return

        clear_text_body = response.get_clear_text_body()

        if clear_text_body is None:
            return

        found_ssn, validated_ssn = self._find_SSN(clear_text_body)
        
        if not validated_ssn:
            return
            
        uri = response.get_uri()
        desc = ('The URL: "%s" possibly discloses US Social Security'
                ' Number: "%s".')
        desc %= (uri, validated_ssn)
        v = Vuln('US Social Security Number disclosure', desc,
                 severity.LOW, response.id, self.get_name())
        v.set_uri(uri)

        v.add_to_highlight(found_ssn)
        self.kb_append_uniq(self, 'ssn', v, 'URL')

    def _find_SSN(self, body_without_tags):
        """
        :return: SSN as found in the text and SSN in its regular format if the
                 body had an SSN
        """
        validated_ssn = None
        ssn = None
        
        for match in self.ssn_regex.finditer(body_without_tags):
            validated_ssn = self._validate_SSN(match)
            if validated_ssn:
                ssn = match.group(0)
                ssn = ssn.strip()
                break

        return ssn, validated_ssn

    def _validate_SSN(self, potential_ssn):
        """
        This method is called to validate the digits of the 9-digit number
        found, to confirm that it is a valid SSN. All the publicly available SSN
        checks are performed. The number is an SSN if:

            1. the first three digits <= 772
            2. the number does not have all zeros in any digit group 3+2+4 i.e. 000-xx-####,
            ###-00-#### or ###-xx-0000 are not allowed
            3. the number does not start from 666-xx-####. 666 for area code is not allowed
            4. the number is not between 987-65-4320 to 987-65-4329. These are reserved for advts
            5. the number is not equal to 078-05-1120

        Source of information: wikipedia and socialsecurity.gov
        """
        try:
            area_number = int(potential_ssn.group(2))
            group_number = int(potential_ssn.group(4))
            serial_number = int(potential_ssn.group(5))
        except:
            return False

        if not group_number:
            return False
        if not serial_number:
            return False

        group = areas_groups_map.get(area_number)
        if not group:
            return False

        odd_one = xrange(1, 11, 2)
        even_two = xrange(10, 100, 2)  # (10-98 even only)
        even_three = xrange(2, 10, 2)
        odd_four = xrange(11, 100, 2)  # (11-99 odd only)
        le_group = lambda x: x <= group
        is_ssn = False

        # For little odds (odds between 1 and 9)
        if group in odd_one:
            if group_number <= group:
                is_ssn = True

        # For big evens (evens between 10 and 98)
        elif group in even_two:
            if group_number in itertools.chain(odd_one,
                                               filter(le_group, even_two)):
                is_ssn = True

        # For little evens (evens between 2 and 8)
        elif group in even_three:
            if group_number in itertools.chain(odd_one, even_two,
                                               filter(le_group, even_three)):
                is_ssn = True

        # For big odds (odds between 11 and 99)
        elif group in odd_four:
            if group_number in itertools.chain(odd_one, even_two, even_three,
                                               filter(le_group, odd_four)):
                is_ssn = True

        if is_ssn:
            return '%s-%s-%s' % (area_number, group_number, serial_number)

        return None

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugins scans every response page to find the strings that are likely
        to be the US social security numbers.
        """
