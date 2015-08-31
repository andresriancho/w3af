"""
javascript.py

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
from .main import get_context, get_context_iter







# Note that the order is important! The most specific contexts should be first
JS_CONTEXTS = []


def get_js_context(data, payload):
    """
    :return: A list which contains lists of all contexts where the payload lives
    """
    return get_context(data, payload, JS_CONTEXTS)


def get_js_context_iter(data, payload):
    """
    :return: A context iterator
    """
    for context in get_context_iter(data, payload, JS_CONTEXTS):
        yield context
