"""
cli.py

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
import yaml
import argparse

from argparse import ArgumentTypeError


# Global default values
DEFAULTS = {'USERNAME': 'admin',
            'HOST': '127.0.0.1',
            'PORT': 5000,
            'DISABLE_SSL': False}


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

    parser.add_argument('--no-ssl',
                        dest="disable_ssl",
                        action="store_true",
                        help="Disable SSL support")

    parser.add_argument('-c',
                        default=False,
                        dest='config_file',
                        type=argparse.FileType('r'),
                        help='Path to a config file in YAML format. At minimum,'
                             ' either this OR the "-p" (password) option MUST'
                             ' be provided.')

    opts = parser.add_argument_group('server options',
                                     'Server options can be specified here or'
                                     ' as part of a YAML configuration file'
                                     ' using the "-c" command line argument.')

    opts.add_argument('-p',
                      required=False,
                      default=False,
                      dest='password',
                      help='SHA512-hashed password for HTTP basic'
                           ' authentication. Linux or Mac users can generate'
                           ' the hash running:\n'
                           ' echo -n "password" | sha512sum')

    opts.add_argument('-u',
                      required=False,
                      dest='username',
                      default=False,
                      help='Username required for basic auth. If not '
                           'specified, this will be set to "admin".')

    opts.add_argument('-v',
                      required=False,
                      default=False,
                      dest='verbose',
                      action='store_true',
                      help='Enables verbose output')

    args = parser.parse_args()

    try:
        args.host, args.port = getattr(args, 'host:port').split(':')
    except ValueError:
        raise argparse.ArgumentTypeError('Please specify a valid host and port'
                                         ' as HOST:PORT (eg "127.0.0.1:5000").')
    except AttributeError:
        # Expect AttributeError if host_port was not entered
        pass

    return args


def process_cmd_args_config(app):
    """
    Handle/merge the command line arguments and configuration file
    :return: A configured app and the result of argparse'ing the sys.argv
    """
    # Error handling is done in main(), don't handle exceptions here
    args = parse_arguments()

    if args.config_file:
        try:
            yaml_conf = yaml.safe_load(args.config_file)
        except:
            file.close(args.config_file)
            raise ArgumentTypeError('Error loading config file %s. Please check'
                                    ' it exists and is a valid YAML file.'
                                    % args.config_file.name)

        for k in yaml_conf:
            if type(yaml_conf[k]).__name__ not in ['str', 'int', 'bool']:
                pass
            elif k.lower() in vars(args) and vars(args)[k.lower()]:
                raise ArgumentTypeError('Error: you appear to have specified'
                                        ' options in the config file and on the'
                                        ' command line. Please resolve any'
                                        ' conflicting options and try again: %s'
                                        % k)
            else:
                # Flask contains a number of built-in server options that can
                # also be modified by setting them in the config YAML:
                # http://flask.pocoo.org/docs/latest/config/
                app.config[k.upper()] = yaml_conf[k]

        file.close(args.config_file)

    for i in vars(args):
        if type(vars(args)[i]).__name__ not in ('str', 'int', 'bool'):
            pass
        elif i in vars(args) and vars(args)[i]:
            app.config[i.upper()] = vars(args)[i]

    for k in DEFAULTS:
        if not k in app.config:
            app.config[k] = DEFAULTS[k]

    if 'PASSWORD' in app.config:
        try:
            # Check password has been specified and is a 512-bit hex string
            # (ie, that it looks like a SHA512 hash)
            int(app.config['PASSWORD'], 16) and len(app.config['PASSWORD']) == 128
        except:
            raise ArgumentTypeError('Error: Please specify a valid'
                                    ' SHA512-hashed plaintext as password,'
                                    ' either inside a config file with "-c" or'
                                    ' using the "-p" flag.')

    app.config['HOST'], app.config['PORT'] = parse_host_port(app.config['HOST'],
                                                             app.config['PORT'])

    if (app.config['HOST'] != '127.0.0.1' and
        app.config['HOST'] != 'localhost'):

        print('')
        if 'PASSWORD' not in app.config:
            print('WARNING! Running this API on a public IP might expose your'
                  ' system to vulnerabilities such as arbitrary file reads'
                  ' through file:// protocol specifications in target URLs and'
                  ' scan profiles.\n\n'
                  'We recommend enabling HTTP basic authentication by'
                  ' specifying a password on the command line (with'
                  ' "-p <SHA512 hash>") or in a configuration file.\n')

        if app.config['DISABLE_SSL']:
            print('WARNING! Traffic to this API is not encrypted and could be'
                  ' sniffed. Please consider using an SSL-enabled proxy such as'
                  ' nginx, or removing --no-ssl from the command line.\n')
        else:
            print('WARNING! Traffic to this API is encrypted using self-signed'
                  ' certificates.\n')

    return args