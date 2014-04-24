"""
js_re_extract.py

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
from w3af.core.data.parsers.utils.re_extract import ReExtract


class JSReExtract(ReExtract):
    """
    Before sending to the regular expression matching, extract the string values
    from the javascript code, and only apply the RE's to those.

    This reduces false positives in the RE's.

    https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/String

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    STRING_DELIMS = {'"', "'"}

    def __init__(self, doc_string, base_url, encoding):
        simplified_doc_string = self._extract_string_vals(doc_string)
        super(JSReExtract, self).__init__(doc_string, base_url, encoding, True)

    def _extract_string_vals(self, doc_string):
        string_vals = []
        current_string = ''
        inside_string = True
        string_delim = None
        escape_next = False

        for c in doc_string:
            if not inside_string and c not in self.STRING_DELIMS:
                # Just random JS code
                continue

            if not inside_string and c in self.STRING_DELIMS:
                pass
            
        return ' \n'.join(string_vals)