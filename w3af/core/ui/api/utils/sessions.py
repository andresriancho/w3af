"""
sessions.py

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
from flask import jsonify

from functools import wraps

from w3af.core.ui.api.db.master import SCANS


def check_session_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        scan_id = kwargs['scan_id']
        if scan_id not in SCANS:
            return jsonify({
                'code': 404,
                'message': 'Session with ID %s does not exist' % scan_id
            }), 404
        return f(*args, **kwargs)
    return decorated


def check_plugin_type_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        scan_id = kwargs['scan_id']
        plugin_type = kwargs['plugin_type']

        w3af = SCANS[scan_id].w3af_core
        if plugin_type not in w3af.plugins.get_plugin_types():
            return jsonify({ 'code': 404,
                             'message': 'Plugin type %s not found' % plugin_type
                          }), 404
        return f(*args, **kwargs)
    return decorated


def check_plugin_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        scan_id = kwargs['scan_id']
        plugin_type = kwargs['plugin_type']
        plugin = kwargs['plugin']

        w3af = SCANS[scan_id].w3af_core
        if plugin not in w3af.plugins.get_plugin_list(plugin_type):
            return jsonify({
                'code': 404,
                'message': 'Plugin %s not found in list of %s plugins' % (
                    plugin,
                    plugin_type)
                }), 404
        return f(*args, **kwargs)
    return decorated
