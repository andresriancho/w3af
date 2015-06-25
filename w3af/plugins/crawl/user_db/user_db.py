"""
user_dir.py

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
import csv
import os

import w3af.core.controllers.output_manager as om

OS = 'os'
APPLICATION = 'applications'
DB_PATH = os.path.dirname(os.path.realpath(__file__))


def get_users_from_csv(ident):
    """
    :return: A list of users from the user dir database.
    """
    assert ident in (APPLICATION, OS), 'Invalid identification'

    csv_db = os.path.join(DB_PATH, '%s.csv' % ident)
    file_handler = file(csv_db, 'rb')
    reader = csv.reader(file_handler)

    while True:
        try:
            csv_row = reader.next()
        except StopIteration:
            break
        except csv.Error:
            # line contains NULL byte, and other similar things.
            # https://github.com/andresriancho/w3af/issues/1490
            msg = 'user_dir: Ignoring data with CSV error at line "%s"'
            om.out.debug(msg % reader.line_num)
            continue

        try:
            desc, user = csv_row
        except ValueError:
            if not csv_row:
                continue

            if csv_row[0].startswith('#'):
                continue

            om.out.debug('Invalid user_dir input: "%r"' % csv_row)
        else:
            yield desc, user