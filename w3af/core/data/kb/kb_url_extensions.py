"""
kb_url_extensions.py

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
import w3af.core.data.kb.knowledge_base as kb


def get_url_extensions_from_kb():
    """
    :return: A set with all the URL filename extensions that have been found
             during the scan. This is useful to reduce the number of HTTP
             requests which are sent during URL brute-forcing.

             For example, when a site only has aspx, js, css and png extensions
             a plugin might get that information using get_url_extensions_from_kb()
             and decide that it won't perform URL brute-forcing for php extensions.
    """
    all_extensions = set()
    all_urls = kb.kb.get_all_known_urls()

    for url in all_urls:
        all_extensions.add(url.get_extension())

    return all_extensions
