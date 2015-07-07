"""
error_handlers.py

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
import sys
import traceback

from flask import jsonify
from os.path import basename

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.auth import requires_auth


@app.errorhandler(404)
def not_found(error):
    response = jsonify({'code': 404,
                        'message': 'Not found'})
    response.status_code = 404
    return response


@app.errorhandler(405)
def method_not_allowed(error):
    response = jsonify({'code': 405,
                        'message': 'Method not allowed'})
    response.status_code = 405
    return response


@app.errorhandler(500)
def error_500_handler(error):
    """
    This error handler will catch all unhandled exceptions in the w3af REST API
    and return something useful to the user for debugging.

    Please note that this will only work if the Flask application is run without
    the debug flag on.
    """
    new_issue = 'https://github.com/andresriancho/w3af/issues/new'

    try:
        # Extract the filename and line number where the exception was raised
        exc_type, exc_value, exc_traceback = sys.exc_info()
        filepath = traceback.extract_tb(exc_traceback)[-1][0]
        filename = basename(filepath)
        lineno, function_name = get_last_call_info(exc_traceback)

        response = jsonify({'code': 500,
                            'message': str(error),
                            'filename': filename,
                            'line_number': lineno,
                            'function_name': function_name,
                            'exception_type': error.__class__.__name__,
                            'please': new_issue})
    except Exception, e:
        # I don't want to fail in the exception handler
        response = jsonify({'code': 500,
                            'exception': str(error),
                            'handler_exception': str(e),
                            'please': new_issue,
                            'message': 'REST API error'})

    response.status_code = 500
    return response


def get_last_call_info(main_tb):
    current = main_tb
    while getattr(current, 'tb_next', None) is not None:
        current = current.tb_next

    return current.tb_lineno, current.tb_frame.f_code.co_name


@app.route('/raise-500', methods=['GET'])
@requires_auth
def raise_500():
    """
    This exists for testing error_500_handler
    """
    raise ValueError('Foo!')
