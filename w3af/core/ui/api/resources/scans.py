from flask import jsonify
from w3af.core.ui.api import app
from w3af.core.ui.api.utils.scans import get_core_for_scan
from w3af.core.ui.api.utils.error import abort


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
    # TODO: Run scan start in a thread and save the thread in the SCANS module
    #       level variable
    raise NotImplementedError


@app.route('/scans/', methods=['GET'])
def list_scans():
    """
    :return: A JSON containing a list of:
        - Scan resource URL (eg. /scans/1)
        - Scan target
    """
    # TODO: Write initial mock for this
    raise NotImplementedError


@app.route('/scans/<int:scan_id>', methods=['DELETE'])
def scan_clear(scan_id):
    """
    Clear all the scan information

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be cleared.
    """
    w3af_core = get_core_for_scan(scan_id)
    if w3af_core is None:
        abort(404, 'Scan not found')

    if not w3af_core.can_clear():
        abort(403, 'Scan is not ready to be cleared')

    w3af_core.clear()

    return jsonify({'message': 'Success'})


@app.route('/scans/<int:scan_id>/status', methods=['GET'])
def scan_status(scan_id):
    """
    :param scan_id: The scan ID
    :return: The scan status
    """
    w3af_core = get_core_for_scan(scan_id)
    if w3af_core is None:
        abort(404, 'Scan not found')

    if not w3af_core.can_clear():
        abort(403, 'Scan is not ready to be cleared')

    return jsonify(w3af_core.status.get_status_as_dict())


@app.route('/scans/<int:scan_id>/pause', methods=['GET'])
def scan_pause(scan_id):
    """
    Pause a scan

    :param scan_id: The scan ID to pause
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be paused.
    """
    w3af_core = get_core_for_scan(scan_id)
    if w3af_core is None:
        abort(404, 'Scan not found')

    if not w3af_core.can_pause():
        abort(403, 'Scan can not be paused')

    w3af_core.pause()

    return jsonify({'message': 'Success'})


@app.route('/scans/<int:scan_id>/stop', methods=['GET'])
def scan_stop(scan_id):
    """
    Stop a scan

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be stopped.
    """
    w3af_core = get_core_for_scan(scan_id)
    if w3af_core is None:
        abort(404, 'Scan not found')

    if not w3af_core.can_pause():
        abort(403, 'Scan can not be paused')

    # TODO: Run this in a different thread
    w3af_core.stop()

    return jsonify({'message': 'Stopping scan'})


@app.route('/scans/<int:scan_id>/log', methods=['GET'])
def scan_log(scan_id):
    """
    :param scan_id: The scan ID to retrieve the scan
    :return: The scan log contents
    """
    raise NotImplementedError