"""
generate_404.py

Copyright 2018 Andres Riancho

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
import string
import itertools

import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.exceptions import HTTPRequestException, FourOhFourDetectionException
from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse


def generate_404_filename(filename):
    """
    Some web applications are really picky about the URL format, or have
    different 404 handling for the URL format. So we're going to apply these
    rules for generating a filename that doesn't exist:

        * Flip the characters of the same type (digit, letter), ignoring
        the file extension (if any):
            'ab-23'      ==> 'ba-32'
            'abc-12'     ==> 'bac-12'
            'ab-23.html' ==> 'ba-32.html'

        * If after the character flipping the filename is equal to the
        original one, +2 to each char:
            'a1a2'      ==> 'c3c4"
            'a1a2.html' ==> 'c3c4.html"

        * There is an edge case which was reported in [0] which affects
        files like '.ssh' or '.env'. These files (at least from w3af's
        perspective) don't have a name and have an extension. When we
        find a file like this we'll just randomize the filename and
        keep the extension.

    [0] https://github.com/andresriancho/w3af/issues/17092

    :param filename: The original filename
    :return: A mutated filename
    """
    if not filename:
        return rand_alnum(5)

    split_filename = filename.rsplit(u'.', 1)
    if len(split_filename) == 2:
        orig_filename, extension = split_filename
    else:
        extension = None
        orig_filename = split_filename[0]

    #
    # This handles the case of files which don't have a name,
    # such as .env.
    #
    if not orig_filename:
        return u'%s.%s' % (rand_alnum(5), extension)

    #
    # This handles the case of files which have really short names
    # such as "a.html" or "ac.rb". When trying to modify those short
    # names it is likely that we'll end up with either the same one
    # or another one that also exists in the path
    #
    if len(orig_filename) in (1, 2):
        orig_filename = u'%s%s' % (rand_alnum(4), orig_filename)

    mod_filename = ''

    for x, y in grouper(orig_filename, 2):

        # Handle the last iteration
        if y is None:
            mod_filename += x
            break

        if x.isdigit() and y.isdigit():
            mod_filename += y + x
        elif x in string.letters and y in string.letters:
            mod_filename += y + x
        else:
            # Don't flip chars
            mod_filename += x + y

    if mod_filename == orig_filename:
        # Damn!
        plus_three_filename = u''
        letters = string.letters
        digits = string.digits
        lletters = len(letters)
        ldigits = len(digits)

        for c in mod_filename:
            indexl = letters.find(c)
            if indexl != -1:
                new_index = (indexl + 3) % lletters
                plus_three_filename += letters[new_index]
            else:
                indexd = digits.find(c)
                if indexd != -1:
                    new_index = (indexd + 3) % ldigits
                    plus_three_filename += digits[new_index]
                else:
                    plus_three_filename += c

        mod_filename = plus_three_filename

    final_result = mod_filename
    if extension is not None:
        final_result += u'.%s' % extension

    return final_result


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def send_request_generate_404(uri_opener, http_response, debugging_id):
    url_404 = get_url_for_404_request(http_response)
    response_404 = send_404(uri_opener, url_404, debugging_id=debugging_id)
    return FourOhFourResponse(response_404)


def get_url_for_404_request(http_response):
    """
    :param http_response: The HTTP response to modify
    :return: A new URL with randomly generated filename or path that will
             trigger a 404.
    """
    response_url = http_response.get_url()
    path = response_url.get_path()
    filename = response_url.get_file_name()

    if path == '/' or filename:
        relative_url = generate_404_filename(filename)
        url_404 = response_url.copy()
        url_404.set_file_name(relative_url)

    else:
        relative_url = '../%s/' % rand_alnum(8)
        url_404 = response_url.url_join(relative_url)

    return url_404


@retry(tries=2, delay=0.5, backoff=2)
def send_404(uri_opener, url404, debugging_id=None):
    """
    Sends a GET request to url404.

    :return: The HTTP response body.
    """
    # I don't use the cache, because the URLs are random and the only thing
    # that cache does is to fill up disk space
    try:
        response = uri_opener.GET(url404,
                                  cache=False,
                                  grep=False,
                                  debugging_id=debugging_id)
    except HTTPRequestException, hre:
        message = 'Exception found while detecting 404: "%s" (did:%s)'
        args = (hre, debugging_id)
        om.out.debug(message % args)
        raise FourOhFourDetectionException(message % args)
    else:
        msg = 'Generated forced 404 for %s (id:%s, did:%s, len:%s)'
        args = (url404, response.id, debugging_id, len(response.body))
        om.out.debug(msg % args)

    return response
