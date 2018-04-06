"""
option_types.py

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
# Numbers
INT = 'integer'
POSITIVE_INT = 'positive_integer'
FLOAT = 'float'

# Networking
IP = 'ip'
PORT = 'port'
URL = 'url'
IPPORT = 'ipport'

# HTTP
QUERY_STRING = 'query_string'
HEADER = 'header'

# Files
OUTPUT_FILE = 'output_file'
INPUT_FILE = 'input_file'

# Misc
BOOL = 'boolean'
STRING = 'string'
LIST = 'list'
REGEX = 'regex'
COMBO = 'combo'
URL_LIST = 'url_list'
FORM_ID_LIST = 'form_id_list'
