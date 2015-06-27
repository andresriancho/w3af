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
from w3af.core.controllers.dependency_check.dependency_check import dependency_check


def parse_host_port(host_port):
    try:
        host, port = host_port.split(':')
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid host:port specified')

    try:
        port = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid port number (1-65535)')

    if port > 65535 or port < 0:
        raise argparse.ArgumentTypeError('Invalid port number (1-65535)')

    if not host:
        raise argparse.ArgumentTypeError('Empty bind IP address')

    return host, port


def parse_arguments():
    """
    Parses the command line arguments
    :return: The parse result from argparse
    """
    parser = argparse.ArgumentParser(description='REST API for w3af')

    parser.add_argument('host:port', action='store',
                        help='Specify address where the REST API will listen'
                             ' for HTTP requests. If not specified 127.0.0.1:'
                             '5000 will be used.',
                        default='127.0.0.1:5000',
                        nargs='?',
                        type=parse_host_port)

    parser.add_argument('-p',
                        required=False,
                        default=False,
                        dest='password',
                        help='[Required] SHA512-hashed password for HTTP basic'
                             ' authentication.')

    parser.add_argument('-u',
                        required=False,
                        default='admin',
                        dest='username',
                        help='Username required for basic auth. If not '
                             'specified, this will default to "admin".')

    parser.add_argument('-v',
                        required=False,
                        default=False,
                        dest='verbose',
                        action='store_true',
                        help='Enables verbose output')

    args = parser.parse_args()

    host_port = getattr(args, 'host:port')
    args.host = host_port[0]
    args.port = host_port[1]

    return args


def main():
    """
    Entry point for the REST API
    :return: Zero if everything went well
    """
    # Check if I have all needed dependencies
    dependency_check()

    args = parse_arguments()

    try:
      # Check password has been specified and is a 512-bit hex string
      # (ie, that it looks like a SHA512 hash)
      int(args.password, 16) and len(args.password) == 128
    except:
      print('Error: Please specify a valid SHA512-hashed plaintext as password'
            ' using the "-p" flag.')
      return 1

    app.config['USERNAME'] = args.username
    app.config['PASSWORD'] = args.password

    try:
        app.run(host=args.host, port=args.port,
                debug=args.verbose, use_reloader=False)
    except socket.error, se:
        print('Failed to start REST API server: %s' % se.strerror)
        return 1

    return 0
