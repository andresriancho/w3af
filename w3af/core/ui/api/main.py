#!/bin/python
from flask import Flask, jsonify, request

app = Flask('w3af')


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
    raise NotImplementedError


@app.route('/scans/', methods=['GET'])
def list_scans():
    """
    :return: A JSON containing a list of:
        - Scan resource URL (eg. /scans/1)
        - Scan target
    """
    raise NotImplementedError


@app.route('/scans/<int:scan_id>', methods=['DELETE'])
def scan_clear(scan_id):
    """
    Clear all the scan information

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be cleared.
    """
    raise NotImplementedError


@app.route('/scans/<int:scan_id>/status', methods=['GET'])
def scan_status(scan_id):
    """
    :param scan_id: The scan ID
    :return: The scan status
    """
    raise NotImplementedError


@app.route('/scans/<int:scan_id>/pause', methods=['GET'])
def scan_pause(scan_id):
    """
    Pause a scan

    :param scan_id: The scan ID to pause
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be paused.
    """
    raise NotImplementedError


@app.route('/scans/<int:scan_id>/stop', methods=['GET'])
def scan_stop(scan_id):
    """
    Stop a scan

    :param scan_id: The scan ID to stop
    :return: Empty result if success, 403 if the current state indicates that
             the scan can't be stopped.
    """
    raise NotImplementedError


@app.route('/scans/<int:scan_id>/log', methods=['GET'])
def scan_log(scan_id):
    """
    :param scan_id: The scan ID to retrieve the scan
    :return: The scan log contents
    """
    raise NotImplementedError


@app.route('/kb/', methods=['GET'])
def list_kb():
    """
    List vulnerabilities stored in the KB

    Filters:

        * /kb/?name= returns only vulnerabilities which contain the specified
          string in the vulnerability name. (contains)

        * /kb/?location_a= returns only vulnerabilities which match the location
          (equals)

        * /kb/?location_b= returns only vulnerabilities which match the location
          (equals)

        * /kb/?url= returns only vulnerabilities for a specific URL (startswith)

    If more than one filter is specified they are combined using AND.

    :return: A JSON containing a list of:
        - KB resource URL (eg. /kb/3)
        - The KB id (eg. 3)
        - The vulnerability name
        - The vulnerability URL
        - Location A
        - Location B
    """
    raise NotImplementedError


@app.route('/kb/<int:vulnerability_id>', methods=['GET'])
def get_kb(vulnerability_id):
    """
    The whole information related to the specified vulnerability ID

    :param vulnerability_id: The vulnerability ID to query
    :return: All the vulnerability information
    """
    raise NotImplementedError
