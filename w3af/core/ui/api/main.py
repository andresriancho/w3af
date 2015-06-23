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

    if args.host not in ('127.0.0.1', 'localhost'):
        print('The REST API does not provide authentication and might expose'
              ' your system to vulnerabilities such as arbitrary file reads'
              ' through file:// protocol specified in target URLs and scan'
              ' profiles. It is NOT RECOMMENDED to bind the REST API to'
              ' a public IP address. You have been warned.\n')

    try:
        app.run(host=args.host, port=args.port,
                debug=args.verbose, use_reloader=False)
    except socket.error, se:
        print('Failed to start REST API server: %s' % se.strerror)
        return 1

    return 0
