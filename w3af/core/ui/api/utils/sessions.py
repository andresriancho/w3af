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
from flask import jsonify, request

from functools import wraps

from w3af.core.ui.api.db.master import SCANS


def check_session_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        session_id = kwargs['session_id']
        if (session_id not in SCANS or
            SCANS[session_id] is None):
            return jsonify({
                'code': 404,
                'message': 'Session with ID %s does not exist'
                           ' or has been deleted' % session_id
            }), 404
        return f(*args, **kwargs)
    return decorated


def check_plugin_type_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        session_id = kwargs['session_id']
        plugin_type = kwargs['plugin_type']

        w3af = SCANS[session_id].w3af_core
        if plugin_type not in w3af.plugins.get_plugin_types():
            return jsonify({'code': 404,
                            'message': 'Plugin type %s not found' % plugin_type
                          }), 404
        if (request.method == 'PATCH' and plugin_type.lower() == 'output'):
            return jsonify({'code': 403,
                            'message': 'Cannot set output plugin options. At'
                                       ' present, only the built-in REST API'
                                       ' output is supported.'
                          }), 403
        return f(*args, **kwargs)
    return decorated


def check_plugin_exists(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        session_id = kwargs['session_id']
        plugin_type = kwargs['plugin_type']
        plugin = kwargs['plugin']

        w3af = SCANS[session_id].w3af_core
        if plugin not in w3af.plugins.get_plugin_list(plugin_type):
            return jsonify({
                'code': 404,
                'message': 'Plugin %s not found in list of %s plugins' % (
                    plugin,
                    plugin_type)
                }), 404
        return f(*args, **kwargs)
    return decorated

def enable_or_disable_plugin(w3af, plugin, plugin_type, enable=False):
        plugin_list = w3af.plugins.get_enabled_plugins(plugin_type)
        if (enable and
                plugin not in plugin_list):
            plugin_list.append(plugin)
        elif (not enable and
                plugin in plugin_list):
            plugin_list.remove(plugin)
        w3af.plugins.set_plugins(plugin_list, plugin_type)
