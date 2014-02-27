"""
opt_factory.py

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
from w3af.core.data.options.bool_option import BoolOption
from w3af.core.data.options.integer_option import IntegerOption
from w3af.core.data.options.float_option import FloatOption
from w3af.core.data.options.string_option import StringOption
from w3af.core.data.options.url_option import URLOption
from w3af.core.data.options.ipport_option import IPPortOption
from w3af.core.data.options.ip_option import IPOption
from w3af.core.data.options.port_option import PortOption
from w3af.core.data.options.list_option import ListOption
from w3af.core.data.options.regex_option import RegexOption
from w3af.core.data.options.combo_option import ComboOption
from w3af.core.data.options.input_file_option import InputFileOption
from w3af.core.data.options.output_file_option import OutputFileOption
from w3af.core.data.options.url_list_option import URLListOption

from w3af.core.data.options.option_types import (
    BOOL, INT, FLOAT, STRING, URL, IPPORT,
    LIST, REGEX, COMBO, INPUT_FILE,
    OUTPUT_FILE, PORT, IP, URL_LIST)


def opt_factory(name, default_value, desc, _type, help='', tabid=''):
    """
    A factory function which will generate one of the Option objects based
    on the _type passed as parameter.
    """
    option_klasses = {
        BOOL: BoolOption,
        INT: IntegerOption,
        FLOAT: FloatOption,
        STRING: StringOption,
        URL: URLOption,
        URL_LIST: URLListOption,
        IPPORT: IPPortOption,
        LIST: ListOption,
        REGEX: RegexOption,
        COMBO: ComboOption,
        INPUT_FILE: InputFileOption,
        OUTPUT_FILE: OutputFileOption,
        PORT: PortOption,
        IP: IPOption,
    }

    return option_klasses[_type](name, default_value, desc, _help=help,
                                 tabid=tabid)
