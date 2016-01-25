"""
main.py

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
import socket
import argparse

from w3af.core.ui.api import app
from w3af.core.ui.api.utils.cli import process_cmd_args_config

from w3af.core.ui.api.utils.digital_certificate import SSLCertificate


def main():
    """
    Entry point for the REST API
    :return: Zero if everything went well
    """
    try:
        args = process_cmd_args_config(app)
    except argparse.ArgumentTypeError, ate:
        print('%s' % ate)
        return 1

    # And finally start the app:
    try:

        if args.disable_ssl:
            app.run(host=app.config['HOST'], port=app.config['PORT'],
                    debug=args.verbose, use_reloader=False, threaded=True)
        else:
            cert_key = SSLCertificate().get_cert_key(app.config['HOST'])

            app.run(host=app.config['HOST'], port=app.config['PORT'],
                    debug=args.verbose, use_reloader=False, threaded=True,
                    ssl_context=cert_key)
    except socket.error, se:
        print('Failed to start REST API server: %s' % se.strerror)
        return 1

    return 0
