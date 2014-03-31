"""
list_option.py

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

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.option_types import LIST


class ListOption(BaseOption):

    LST_VALIDATION_RE = re.compile(
        '((".*?"|\'.*?\'|.*?),)*(".*?"|\'.*?\'|.*?)', re.U)
    LST_PARSE_RE = re.compile('(".*?"|\'.*?\'|.*?),', re.U)
    _type = LIST

    def _get_str(self, value):
        if isinstance(value, list):
            return ','.join([str(i) for i in value])

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'True' or 'a,b,c'

        Based on the value parameter and the option type, I have to create a nice
        looking object like True or ['a','b','c'].
        """
        if isinstance(value, list):
            self._value = value
            return

        self._value = self.validate(value)

    def validate(self, value):
        temp_value = value + ','
        mo = self.LST_VALIDATION_RE.match(temp_value)
        try:
            matched_str = mo.group(0)
            assert matched_str == temp_value
        except Exception:
            msg = 'Invalid list format in user configuration: "%s".' % value
            raise BaseFrameworkException(msg)
        else:
            res = []
            list_items = self.LST_PARSE_RE.findall(temp_value)

            for item in list_items:

                item = item.strip()
                if item == '':
                    continue

                # Now I check for single and double quotes
                if (item.startswith('"') and item.endswith('"')) or \
                   (item.startswith("'") and item.endswith("'")):
                    res.append(item[1:-1])
                else:
                    res.append(item)

            return res
