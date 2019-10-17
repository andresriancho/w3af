#!/usr/bin/env python

"""
Copyright (c) 2006-2017 sqlmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import sys

sys.dont_write_bytecode = True

# this has to be the first non-standard import
__import__("lib.utils.versioncheck")

import logging
import optparse
import warnings

warnings.filterwarnings(
    action="ignore",
    message=".*was already imported",
    category=UserWarning)
warnings.filterwarnings(action="ignore", category=DeprecationWarning)

from sqlmap import modulePath
from lib.core.common import setPaths
from lib.core.data import logger
from lib.core.settings import RESTAPI_DEFAULT_ADAPTER
from lib.core.settings import RESTAPI_DEFAULT_ADDRESS
from lib.core.settings import RESTAPI_DEFAULT_PORT
from lib.utils.api import client
from lib.utils.api import server


def main():
    """
    REST-JSON API main function
    """

    # Set default logging level to debug
    logger.setLevel(logging.DEBUG)

    # Initialize paths
    setPaths(modulePath())

    # Parse command line options
    apiparser = optparse.OptionParser()
    apiparser.add_option(
        "-s",
        "--server",
        help="Act as a REST-JSON API server",
        default=RESTAPI_DEFAULT_PORT,
        action="store_true")
    apiparser.add_option(
        "-c",
        "--client",
        help="Act as a REST-JSON API client",
        default=RESTAPI_DEFAULT_PORT,
        action="store_true")
    apiparser.add_option(
        "-H",
        "--host",
        help="Host of the REST-JSON API server (default \"%s\")" %
        RESTAPI_DEFAULT_ADDRESS,
        default=RESTAPI_DEFAULT_ADDRESS,
        action="store")
    apiparser.add_option(
        "-p",
        "--port",
        help="Port of the the REST-JSON API server (default %d)" %
        RESTAPI_DEFAULT_PORT,
        default=RESTAPI_DEFAULT_PORT,
        type="int",
        action="store")
    apiparser.add_option(
        "--adapter",
        help="Server (bottle) adapter to use (default \"%s\")" %
        RESTAPI_DEFAULT_ADAPTER,
        default=RESTAPI_DEFAULT_ADAPTER,
        action="store")
    apiparser.add_option(
        "--username",
        help="Basic authentication username (optional)",
        action="store")
    apiparser.add_option(
        "--password",
        help="Basic authentication password (optional)",
        action="store")
    (args, _) = apiparser.parse_args()

    # Start the client or the server
    if args.server is True:
        server(
            args.host,
            args.port,
            adapter=args.adapter,
            username=args.username,
            password=args.password)
    elif args.client is True:
        client(
            args.host,
            args.port,
            username=args.username,
            password=args.password)
    else:
        apiparser.print_help()


if __name__ == "__main__":
    main()
