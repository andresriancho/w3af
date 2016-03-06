"""
utils.py

Copyright 2016 Andres Riancho

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

from w3af.core.data.context.constants import CONTEXT_DETECTOR
from w3af.core.data.fuzzer.utils import rand_alnum


def place_boundary(payload, bound=None):
    if not bound:
        bound = rand_alnum(4).lower()
        left_bound = '%sl' % bound
        right_bound = '%sr' % bound
    else:
        left_bound, right_bound = bound

    return '%s%s%s' % (left_bound, payload, right_bound)


def get_boundary(payload):
    return payload[:5], payload[-5:]


def encode_payloads(boundary, data):
    l_bound, r_bound = boundary
    chunks = data.split(l_bound)
    result = [chunks.pop(0)]
    for chunk in chunks:
        in_chunks = chunk.split(r_bound, 1)
        if len(in_chunks) != 2:
            # Probably payload was filtered on server-side, i.e.:
            #   left<right -> strip_tags(...) -> left
            # So just skip this chunk
            result.append(chunk)
        else:
            payload, rest_body = in_chunks
            payload = ('%s%s%s' % (l_bound, payload, r_bound)) \
                .encode('utf-8') \
                .encode('hex')
            result.append('%s%s%s%s' % (
                CONTEXT_DETECTOR, payload, CONTEXT_DETECTOR, rest_body))

    return ''.join(result)


def decode_payloads(data):
    chunks = data.split(CONTEXT_DETECTOR)
    if not len(chunks) % 2:
        raise ContextCodecException('Malformed data,'
                                    'context boundaries must be paired.')

    payloads = []
    context_content = []
    for i, chunk in enumerate(chunks):
        if i % 2:
            payload = chunk \
                .decode('hex') \
                .decode('utf-8')
            payloads.append(payload)
            context_content.append(payload)
        else:
            context_content.append(chunk)

    return set(payloads), ''.join(context_content)


class ContextCodecException(Exception):
    pass
