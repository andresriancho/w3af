"""
log.py

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

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.error import abort
from w3af.core.ui.api.utils.auth import requires_auth
from w3af.core.ui.api.utils.scans import get_scan_info_from_id


RESULTS_PER_PAGE = 200


@app.route('/scans/<int:scan_id>/log', methods=['GET'])
@requires_auth
def scan_log(scan_id):
    """
    :param scan_id: The scan ID to retrieve the scan
    :return: The scan log contents, paginated using 200 entries per page
    """
    scan_info = get_scan_info_from_id(scan_id)
    if scan_info is None:
        abort(404, 'Scan not found')

    if scan_info.output is None:
        abort(404, 'Scan output not found')

    page = request.args.get('page', None)
    _id = request.args.get('id', None)

    if page is not None and not page.isdigit():
        abort(400, 'Invalid page number')

    if _id is not None and not _id.isdigit():
        abort(400, 'Invalid log id')

    if page is not None and _id is not None:
        abort(400, 'Can only paginate using one of "page" or "id"')

    next, next_url, log_entries = paginate_logs(scan_id, scan_info, page, _id)

    return jsonify({'next': next,
                    'next_url': next_url,
                    'entries': log_entries})


def paginate_logs(scan_id, scan_info, page, _id):
    """
    Decides which pagination method to use (pages or by id) and returns the
    log entries.

    :param scan_id: The scan ID
    :param scan_info: The scan information
    :param page: The page number
    :param _id: The first log id to include in the results
    :return: A tuple containing:
                * next: The next id or page to query for more logs, or None
                * next_url: The URL to continue retrieving data, or None
                * log_entries: The log lines
    """
    if page is not None or _id is None:
        #
        #   Paginate using the "page" parameter if the "page" is specified or
        #   by default when "page" is not set and "id" is not set either
        #
        page = int(page) if page is not None else 0
        start = RESULTS_PER_PAGE * page
        end = start + RESULTS_PER_PAGE

        messages = scan_info.output.get_entries(start, end)

        more = True if len(scan_info.output.log) > end else False
        next = page + 1 if more else None
        next_url = '/scans/%s/log?page=%s' % (scan_id, next) if more else None
        log_entries = [m.to_json() for m in messages]

        return next, next_url, log_entries

    else:
        #
        #   Paginate by log "id"
        #
        start_id = int(_id)
        end_id = start_id + RESULTS_PER_PAGE

        messages = scan_info.output.get_entries(start_id, end_id)

        more = True if len(scan_info.output.log) > end_id else False
        next = end_id if more else None
        next_url = '/scans/%s/log?id=%s' % (scan_id, next) if more else None
        log_entries = [m.to_json() for m in messages]

        return next, next_url, log_entries