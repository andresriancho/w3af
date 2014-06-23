"""
file_templates.py

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
import os

from w3af import ROOT_PATH
from w3af.core.data.fuzzer.utils import rand_alnum, rand_alpha
from w3af.core.data.misc.encoding import smart_str


TEMPLATE_DIR = os.path.join(ROOT_PATH, 'core', 'data', 'constants',
                            'file_templates')


def get_file_from_template(extension):
    file_name = "%s.%s" % (rand_alpha(7), extension)

    template_file = os.path.join(TEMPLATE_DIR, 'template.%s' % extension)
    if os.path.exists(template_file):
        file_content = file(template_file).read()
        success = True
    else:
        file_content = rand_alnum(64)
        success = False

    return success, file_content, file_name


def get_template_with_payload(extension, payload):
    success, file_content, file_name = get_file_from_template(extension)
    # TODO: Add support for file types which have some type of CRC
    file_content = file_content.replace('A' * 239, smart_str(payload))
    return success, file_content, file_name
