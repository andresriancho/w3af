"""
multi_json_doc.py

Copyright 2019 Andres Riancho

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


def parse_multi_json_docs(data):
    """
    In some cases the Chrome instance returns two or more JSON docs in the
    same websocket frame. When the devtools client tries to parse it using the
    JSON module it fails because it is invalid.

    This function will split the data into different JSON documents and yield
    each of them.

    Since most of the time `data` has only one JSON document, the function
    attempts to improve the performance for that step as much as possible, and
    then for the other cases it is slower.

    :param data: The input string containing one or more JSON documents
    :return: Yields N parsed JSON documents as dicts
    """
    #
    # Simplest case where only one JSON document is present
    #
    parsed_json = None

    try:
        parsed_json = json.loads(data)
    except ValueError:
        pass

    if parsed_json is not None:
        yield parsed_json
        return

    #
    # More complex case where multiple JSON documents are present
    #
    # This is slow, but we only reach this code section in less than 5% of
    # the messages that come from the wire
    #
    current_doc = ''
    parsed_json = None

    for c in data:

        current_doc += c

        try:
            parsed_json = json.loads(current_doc)
        except ValueError:
            continue

        if parsed_json is not None:
            yield parsed_json

            current_doc = ''
            parsed_json = None
