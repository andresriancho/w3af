"""
http_messages.py

Copyright 2012 Andres Riancho

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

W3C_REASONS = {
    100: ['continue', ],
    101: ['switching protocols', ],

    200: ['ok', ],
    201: ['created', ],
    202: ['accepted', ],
    203: ['non-authoritative information', ],
    204: ['no content', ],
    205: ['reset content', ],
    206: ['partial content', ],

    300: ['multiple choices', ],
    301: ['moved permanently', ],
    302: ['found', ],
    303: ['see other', ],
    304: ['not modified', ],
    305: ['use proxy', ],
    306: ['(unused)', ],
    307: ['temporary redirect', ],

    400: ['bad request', ],
    401: ['unauthorized', 'authorization required'],
    402: ['payment required', ],
    403: ['forbidden', ],
    404: ['not found', ],
    405: ['method not allowed', 'not allowed'],
    406: ['not acceptable', ],
    407: ['proxy authentication required', ],
    408: ['request timeout', ],
    409: ['conflict', ],
    410: ['gone', ],
    411: ['length required', ],
    412: ['precondition failed', ],
    413: ['request entity too large', ],
    414: ['request-uri too long', ],
    415: ['unsupported media type', ],
    416: ['requested range not satisfiable', ],
    417: ['expectation failed', ],

    500: ['internal server error', ],
    501: ['not implemented', ],
    502: ['bad gateway', ],
    503: ['service unavailable', ],
    504: ['gateway timeout', ],
    505: ['http version not supported', ],
}
