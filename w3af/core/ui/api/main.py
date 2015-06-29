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
import yaml

from w3af.core.ui.api import app
from w3af.core.controllers.dependency_check.dependency_check import dependency_check

# Global default values
defaults = {'USERNAME':'admin',
            'HOST': '127.0.0.1',
            'PORT': 5000}

def parse_host_port(host, port):

    try:
        port = int(port)
    except ValueError:
        raise argparse.ArgumentTypeError('Invalid port number (1-65535)')

    if port > 65535 or port < 0:
        raise argparse.ArgumentTypeError('Invalid port number (1-65535)')

    if not host:
        raise argparse.ArgumentTypeError('Empty bind IP address')

    return host, int(port)


def parse_arguments():
    """
    Parses the command line arguments
    :return: The parse result from argparse
    """
    parser = argparse.ArgumentParser(description='REST API for w3af',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('host:port', action='store',
                        help='Specify address where the REST API will listen'
                             ' for HTTP requests. If not specified 127.0.0.1:'
                             '5000 will be used.',
                        default=False,
                        nargs='?')

    parser.add_argument('-c',
                        default=False,
                        dest='config_file',
                        help='Path to a config file in YAML format. At minimum,'
                             ' either this OR the "-p" (password) option MUST'
                             ' be provided.')

    opts = parser.add_argument_group('server options',
                                     'Server options can be specified here or'
                                     ' as part of a YAML configuration file'
                                     ' (see above).\n'
                                     'If no configuration file is used, the'
                                     ' "-p" (password) option MUST be specified.')

    opts.add_argument('-p',
                        required=False,
                        default=False,
                        dest='password',
                        help='SHA512-hashed password for HTTP basic'
                             ' authentication. Linux or Mac users can generate'
                             ' this by running:\n' 
                             ' echo -n "password" | sha512sum')

    opts.add_argument('-u',
                        required=False,
                        dest='username',
                        default=False, 
                        help='Username required for basic auth. If not '
                             'specified, this will be set to "admin".')

    parser.add_argument('-v',
                        required=False,
                        default=False,
                        dest='verbose',
                        action='store_true',
                        help='Enables verbose output')

    args = parser.parse_args()

    try:
      args.host, args.port = getattr(args,'host:port').split(':')
    except ValueError:
      raise argparse.ArgumentTypeError('Please specify a valid host and port as'
                                       ' HOST:PORT (eg "127.0.0.1:5000").')
    except AttributeError:
      pass # Expect AttributeError if host_port was not entered
    
    return args


def main():
    """
    Entry point for the REST API
    :return: Zero if everything went well
    """
    # Check if I have all needed dependencies
    dependency_check()

    args = parse_arguments()
    if args.config_file:
      try:
        with open(args.config_file) as f:
          yaml_conf = yaml.safe_load(f)
      except:
        print('Error loading config file %s. Please check it exists and is'
              ' a valid YAML file.' % args.config_file)
        return 1

      for k.lower() in yaml_conf:
        if k in vars(args) and vars(args)[k]:
          print('Error: you appear to have specified options in the config'
                ' file and on the command line. Please resolve any conflicting'
                ' options and try again: %s' % k)
          return 1

      # Flask contains a number of built-in server options that can also be
      # modified by setting them in the config YAML:
      # http://flask.pocoo.org/docs/latest/config/

        app.config[k.upper()] = yaml_conf[k]
     
    for i in vars(args):
      if i in vars(args) and vars(args)[i]:
        app.config[i.upper()] = vars(args)[i]

    try:
      # Check password has been specified and is a 512-bit hex string
      # (ie, that it looks like a SHA512 hash)
      int(app.config['PASSWORD'], 16) and len(app.config['PASSWORD']) == 128
    except:
      print('Error: Please specify a valid SHA512-hashed plaintext as password,'
            ' either inside a config file with "-c" or using the "-p" flag.')
      return 1
    
    for k in defaults:
      if not k in app.config:
        app.config[k] = defaults[k]

    app.config['HOST'], app.config['PORT'] = parse_host_port(app.config['HOST'],
                                                             app.config['PORT'])

    try:
        app.run(host=app.config['HOST'], port=app.config['PORT'],
                debug=args.verbose, use_reloader=False)
    except socket.error, se:
        print('Failed to start REST API server: %s' % se.strerror)
        return 1

    return 0
