"""
paginate.py

Copyright 2018 Andres Riancho

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
PAGINATION_PAGE_COUNT = 20


def paginate(functor, *args, **kwargs):
    """

    :param functor: The function that returns results to paginate
    :param args: Arguments for the function
    :param kwargs: Arguments for the function
    :return: Yield results as they arrive
    """
    start = 0

    while True:
        page_items = 0

        for result in functor(start, PAGINATION_PAGE_COUNT, *args, **kwargs):
            page_items += 1
            yield result

        if page_items < PAGINATION_PAGE_COUNT:
            break

        start += PAGINATION_PAGE_COUNT
