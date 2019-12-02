# -*- coding: utf-8 -*-
"""
filter_printable.py

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
import json
import datetime


class DateTimeJSONEncoder(json.JSONEncoder):
    """
    https://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript

    This small encoder allows us to handle datetime instances when
    doing "json.dumps()"
    """
    # pylint: disable=E0202
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)
    # pylint: enable=E0202