"""
routes.py

Copyright 2015 Andres Riancho

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
from w3af.core.ui.api import app


def list_subroutes(request):
    """
    Lists routes under the current branch

    :param request: A flask.request object (usually the most recent HTTP request)
    :return: A list of possible routes under the requested path
    """
    if str(request.url_rule).rstrip('/') != request.path.rstrip('/'):
    # Be user friendly: replace internal variable names such as '<int:scan_id>'
    # with the values the client requested.
        request.path = request.path.rstrip('/') + ('/')
        urls = [request.path +
                i.rule[len(request.path):].partition('/')[2]
                for i in app.url_map.iter_rules() if
                i.rule[:len(request.url_rule.rule)] == request.url_rule.rule]
    else:
        urls = [i.rule for i in app.url_map.iter_rules() if
                i.rule[:len(request.url_rule.rule)] == request.url_rule.rule]
    return urls
