"""
scans.py

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
from threading import Thread, Event
from flask import jsonify, request

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.db.master import SCANS
from w3af.core.ui.api.utils.scans import (get_scan_info_from_id,
                                          start_scan_helper,
                                          get_new_scan_id,
                                          create_temp_profile)
from w3af.core.data.parsers.doc.url import URL
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import BaseFrameworkException


@app.route('/scans/', methods=['POST'])
def start_scan():
    """
    Starts a new w3af scan

    Receive a JSON containing:
        - A list with the target URLs
        - The profile (eg. the content of fast_scan.pw3af)

    :return: A JSON containing:
        - The URL to the newly created scan (eg. /scans/1)
        - The newly created scan ID (eg. 1)
    """
    if not request.json or not 'scan_profile' in request.json:
        abort(400, 'Expected scan_profile in JSON object')

    if not request.json or not 'target_urls' in request.json:
        abort(400, 'Expected target_urls in JSON object')

    scan_profile = request.json['scan_profile']
    target_urls = request.json['target_urls']

    #
    # First make sure that there are no other scans running, remember that this
    # REST API is an MVP and we can only run one scan at the time (for now)
    #
    scan_infos = SCANS.values()
    if not all([si is None for si in scan_infos]):
        abort(400, 'This version of the REST API does not support'
                   ' concurrent scans. Remember to DELETE finished scans'
                   ' before starting a new one.')

    #
    # Before trying to start a new scan we verify that the scan profile is
    # valid and return an informative error if it's not
    #
    scan_profile_file_name, profile_path = create_temp_profile(scan_profile)
    w3af_core = w3afCore()

    try:
        w3af_core.profiles.use_profile(scan_profile_file_name,
                                       workdir=profile_path)
    except BaseFrameworkException, bfe:
        abort(400, str(bfe))

    #
    # Now that we know that the profile is valid I verify the scan target info
    #
    if not len(target_urls):
        abort(400, 'No target URLs specified')

    for target_url in target_urls:
        try:
            URL(target_url)
        except ValueError:
            abort(400, 'Invalid URL: "%s"' % target_url)

    target_options = w3af_core.target.get_options()
    target_option = target_options['target']
    try:
        target_option.set_value([URL(u) for u in target_urls])
        w3af_core.target.set_options(target_options)
    except BaseFrameworkException, bfe:
        abort(400, str(bfe))

    #
    # Finally, start the scan in a different thread
    #
    scan_id = get_new_scan_id()
    scan_info_setup = Event()

    args = (target_urls, scan_profile, scan_info_setup)
    t = Thread(target=start_scan_helper, name='ScanThread', args=args)
    t.daemon = True

    t.start()

    # Wait until the thread starts
    scan_info_setup.wait()

    return jsonify({'message': 'Success',
                    'id': scan_id,
                    'href': '/scans/%s' % scan_id}), 201


@app.route('/scans/', methods=['GET'])
def list_scans():
    """
    :return: A JSON containing a list of:
        - Scan resource URL (eg. /scans/1)
        - Scan target
        - Scan status
    """
    data = []

    for scan_id, scan_info in SCANS.iteritems():

        if scan_info is None:
            continue

        target_urls = scan_info.target_urls
        status = scan_info.w3af_core.status.get_simplified_status()
        errors = True if scan_info.exception is not None else False

        data.append({'id': scan_id,
                     'href': '/scans/%s' % scan_id,
                     'target_urls': target_urls,
                     'status': status,
                     'errors': errors})

    return jsonify({'items': data})


@app.route('/scans/<int:scan_id>', methods=['DELETE'])
def scan_delete(scan_id):
    """
    Clear all the scan information

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be cleared.
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    if not scan_info.w3af_core.can_clear():
        abort(403, 'Scan is not ready to be cleared')

    scan_info.w3af_core.cleanup()
    SCANS[scan_id] = None

    return jsonify({'message': 'Success'})


@app.route('/scans/<int:scan_id>/status', methods=['GET'])
def scan_status(scan_id):
    """
    :param scan_id: The scan ID
    :return: The scan status
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    status = scan_info.w3af_core.status.get_status_as_dict()
    status['exception'] = str(scan_info.exception)

    return jsonify(status)


@app.route('/scans/<int:scan_id>/pause', methods=['GET'])
def scan_pause(scan_id):
    """
    Pause a scan

    :param scan_id: The scan ID to pause
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be paused.
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    if not scan_info.w3af_core.can_pause():
        abort(403, 'Scan can not be paused')

    scan_info.w3af_core.pause()

    return jsonify({'message': 'Success'})


@app.route('/scans/<int:scan_id>/stop', methods=['GET'])
def scan_stop(scan_id):
    """
    Stop a scan

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be stopped.
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    if not scan_info.w3af_core.can_stop():
        abort(403, 'Scan can not be paused')

    t = Thread(target=scan_info.w3af_core.stop, name='ScanStopThread', args=())
    t.daemon = True
    t.start()

    return jsonify({'message': 'Stopping scan'})


@app.route('/scans/<int:scan_id>/log', methods=['GET'])
def scan_log(scan_id):
    """
    :param scan_id: The scan ID to retrieve the scan
    :return: The scan log contents, paginated using 200 entries per page
    """
    page = request.args.get('page', 0)
    results_per_page = 200

    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    if scan_info.output is None:
        abort(404, 'Scan output not found')

    start = results_per_page * page
    end = start + results_per_page

    messages = scan_info.output[start:end]

    more = True if len(scan_info.output) > end else False

    return jsonify({'next': page + 1,
                    'more': more,
                    'entries': [m.to_json() for m in messages]})