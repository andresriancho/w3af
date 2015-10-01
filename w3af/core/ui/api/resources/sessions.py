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
import threading
from multiprocessing.dummy import Process
from flask import jsonify, request

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.routes import list_subroutes
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.sessions import (check_session_exists,
                                             check_plugin_type_exists,
                                             check_plugin_exists,
                                             enable_or_disable_plugin)
from w3af.core.ui.api.db.master import SCANS
from w3af.core.ui.api.utils.scans import (get_scan_info_from_id,
                                          create_scan_helper,
                                          start_preconfigured_scan)
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.controllers.misc_settings import MiscSettings
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import *
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.doc.url import URL

SET_OPTIONS_LOCK = threading.RLock()


@app.route('/sessions/', methods=['POST'])
@requires_auth
def create_scan_session():
    """
    Creates a new w3af scan session.

    :return: A JSON containing:
        - The URL to the newly created session (eg. /sessions/0)
        - The newly created scan ID (eg. 0)
    """
    scan_id = create_scan_helper()

    return jsonify({'message': 'Success',
                    'id': scan_id,
                    'href': '/sessions/%s' % scan_id}), 201


@app.route('/sessions/<int:scan_id>', methods=['GET'])
@requires_auth
@check_session_exists
def session_info(scan_id):
    """
    Shows information about available actions for a session

    :return: 404 if scan does not exist.
             Otherwise, a list of possible routes under /sessions/<scan_id>/
    """
    urls = list_subroutes(request)
    return jsonify({'message': 'Session %s' % scan_id,
                    'available_endpoints': urls})


@app.route('/sessions/<int:scan_id>/plugins/', methods=['GET'])
@requires_auth
@check_session_exists
def list_plugin_types(scan_id):
    """
    Lists available plugin types

    :return: 404 if scan does not exist.
             Otherwise, a list of all existing plugin types.
    """
    w3af = SCANS[scan_id].w3af_core
    return jsonify({'entries': w3af.plugins.get_plugin_types()})


@app.route('/sessions/<int:scan_id>/plugins/<string:plugin_type>/',
           methods=['GET'])
@requires_auth
@check_session_exists
@check_plugin_type_exists
def get_plugin_list(scan_id, plugin_type):
    """
    Lists available plugins of type "plugin_type"

    :return: 404 if scan or plugin type does not exist.
             Otherwise, a list of all matching plugins.
    """
    w3af = SCANS[scan_id].w3af_core
    return jsonify({
        'description': " ".join(w3af.plugins.get_plugin_type_desc(
            plugin_type).split()),
        'entries': w3af.plugins.get_plugin_list(plugin_type) })


@app.route('/sessions/<int:scan_id>/plugins/<string:plugin_type>/<string:plugin>/',
           methods=['GET'])
@requires_auth
@check_session_exists
@check_plugin_type_exists
@check_plugin_exists
def get_plugin_config(**kwargs):
    """
    Shows current configuration and help text for the named plugin.

    :return: 404 if scan or plugin does not exist.
             Otherwise, a JSON object containing settings and basic help text.
    """
    scan_id = kwargs['scan_id']
    plugin_type = kwargs['plugin_type']
    plugin = kwargs['plugin']

    w3af = SCANS[scan_id].w3af_core

    opts = (
        w3af.plugins.get_plugin_options(plugin_type, plugin) or
        w3af.plugins.get_plugin_inst(plugin_type, plugin).get_options()
        )
    plugin_opts = { i.get_name():
            { "value": str(i.get_value()),
              "description": i.get_desc(),
              "type": i.get_type(),
              "default": i.get_default_value() }
        for i in opts }

    long_desc = " ".join(w3af.plugins.get_quick_instance(plugin_type, plugin)
                         .get_long_desc().split())
    enabled = plugin in w3af.plugins.get_enabled_plugins(plugin_type)

    return jsonify({ 'configuration': plugin_opts,
                     'description': long_desc,
                     'enabled' : enabled })


@app.route('/sessions/<int:scan_id>/plugins/<string:plugin_type>/<string:plugin>/',
           methods=['PATCH'])
@requires_auth
@check_session_exists
@check_plugin_type_exists
@check_plugin_exists
def set_plugin_config(**kwargs):
    """
    Allows a user to modify a single element of plugin configuration by sending
    a PATCH request.

    :return: 404 if scan or plugin does not exist.
             400 if the PATCH request is not in valid format.
             422 if the PATCH request is in valid format, but settings cannot be
             applied (eg, negative numbers where none are accepted).

             Otherwise, a JSON object confirming success and echoing the
             changed setting.
    """

    scan_id = kwargs['scan_id']
    plugin_type = kwargs['plugin_type']
    plugin = kwargs['plugin']

    w3af = SCANS[scan_id].w3af_core

    plugin_opts = (
        w3af.plugins.get_plugin_options(plugin_type, plugin) or
        w3af.plugins.get_plugin_inst(plugin_type, plugin).get_options()
    )

    opt_names = dict(request.get_json(force=True))

    if ('enabled' in opt_names and len(opt_names) == 1):
        with SET_OPTIONS_LOCK:
            enable_or_disable_plugin(w3af,
                                     plugin,
                                     plugin_type,
                                     enable=request.json['enabled'])
            return jsonify({
                'message': 'success',
                'modified': request.json
                })
    try:
        # Remove 'enabled' if included as we must set this separately
        opt_names.pop('enabled')
    except ValueError:
        pass

    for opt_name in opt_names:
        try:
            opt_value = request.json[opt_name]
            opt_type = plugin_opts[opt_name].get_type()
        except BaseFrameworkException:
            return jsonify({
                'code': '400',
                'message': '%s is not a valid option for plugin %s' %
                    (opt_name,
                     plugin)
                }), 400
        try:
            if opt_type.lower() == 'url_list':
                plugin_opts[opt_name].set_value([URL(o) for o in opt_value])
            else:
                plugin_opts[opt_name].set_value(opt_value)
        except (AttributeError, BaseFrameworkException):
            return jsonify({
                'code': '422',
                'message': 'Invalid %s option %s' % (opt_type, opt_value)
                }), 422

    with SET_OPTIONS_LOCK:
        if 'enabled' in request.json:
            enable_or_disable_plugin(w3af,
                                     plugin,
                                     plugin_type,
                                     enable=request.json['enabled'])
        w3af.plugins.set_plugin_options(plugin_type, plugin, plugin_opts)

        return jsonify({
            'message': 'success',
            'modified': request.json
            })


@app.route('/sessions/<int:scan_id>/core/<string:core_setting>/',
           methods=['GET'])
@requires_auth
@check_session_exists
def get_core_settings(scan_id, core_setting):
    """
    Shows available core settings and their current values.

    :return: 404 if scan does not exist.
             Otherwise, a JSON object containing settings and basic help text.
    """
    w3af = SCANS[scan_id].w3af_core

    core_setting = core_setting.lower()
    if core_setting == 'http':
        opts = w3af.uri_opener.settings.get_options()
    elif core_setting == 'misc':
        opts = MiscSettings().get_options()
    elif core_setting == 'target':
        opts = w3af.target.get_options()
    else:
        return jsonify({
            'code': 404,
            'message': '%s is not a valid core setting type' % core_setting }), 404

    opt_dict = { i.get_name():
            { "value": i.get_value(),
              "description": i.get_desc(),
              "type": i.get_type(),
              "default": i.get_default_value() }
        for i in opts }

    return jsonify({ '%s settings' % core_setting : opt_dict })


@app.route('/sessions/<int:scan_id>/core/<string:core_setting>/',
           methods=['PATCH'])
@requires_auth
@check_session_exists
def set_core_config(scan_id, core_setting):
    """
    Allows a user to modify core configuration by sending a PATCH request.

    :return: 404 if scan does not exist.
             400 if the PATCH request is not in valid format.
             422 if the PATCH request is in valid format, but settings cannot be
             applied (eg, negative numbers where none are accepted).

             Otherwise, a JSON object confirming success and echoing the
             changed setting.
    """
    w3af = SCANS[scan_id].w3af_core

    if core_setting == 'http':
        configurable = w3af.uri_opener.settings
    if core_setting == 'misc':
        configurable = MiscSettings()
    if core_setting == 'target':
        configurable = w3af.target

    core_opts = configurable.get_options()
    for opt_name in request.get_json(force=True):
        try:
            opt_value = request.json[opt_name]
            opt_type = core_opts[opt_name].get_type()
        except BaseFrameworkException:
            return jsonify({
                'code': '400',
                'message': '%s is not a valid option here' % opt_name
                }), 400
        try:
            if opt_type.lower() == 'url_list':
                core_opts[opt_name].set_value([URL(o) for o in opt_value])
            else:
                core_opts[opt_name].set_value(opt_value)
        except (AttributeError, BaseFrameworkException):
            return jsonify({
                'code': '422',
                'message': 'Invalid %s value %s' % (opt_type, opt_value)
                }), 422

    with SET_OPTIONS_LOCK:
        configurable.set_options(core_opts)

        if opt_name.lower() == 'target':
            SCANS[scan_id].target_urls = request.json[opt_name]

        return jsonify({
            'message': 'success',
            'modified': request.json
            })

@app.route('/sessions/<int:scan_id>/start')
@requires_auth
@check_session_exists
def start_scan_from_session(scan_id):
    scan_info_setup = threading.Event()
    args = (SCANS[scan_id], scan_info_setup)

    t = Process(target=start_preconfigured_scan, name='ScanThread', args=args)
    t.daemon = True
    t.start()

    scan_info_setup.wait()
    return jsonify({'message': 'Success',
                    'id': scan_id,
                    'href': '/scans/%s' % scan_id})
