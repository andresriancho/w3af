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
import random
import string
import itertools

import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.misc.decorators import retry
from w3af.core.controllers.exceptions import HTTPRequestException, FourOhFourDetectionException
from w3af.core.controllers.core_helpers.not_found.response import FourOhFourResponse


def should_flip(index, seed):
    rnd = random.Random()
    rnd.seed(index + seed)

    # 3 out of 5 get flip
    return rnd.randint(1, 100) % 5 in (0, 1, 2)


def generate_404_without_filename():
    return rand_alnum(5)


def generate_404_without_name(extension):
    return u'%s.%s' % (rand_alnum(5), extension)


def generate_404_for_short_filename(filename, extension):
    mod_filename = u'%s%s' % (rand_alnum(4), filename)
    return append_extension_if_exists(mod_filename, extension)


def generate_404_by_rot3(filename, extension, seed=1):
    plus_three_filename = [c for c in filename]
    mod_filename = ''.join(plus_three_filename)

    letters = string.letters
    digits = string.digits

    letters_len = len(letters)
    digits_len = len(digits)

    for i, c in enumerate(plus_three_filename):

        if not should_flip(i, seed):
            plus_three_filename[i] = c
            continue

        letter_index = letters.find(c)
        if letter_index != -1:
            new_index = (letter_index + 3) % letters_len
            plus_three_filename[i] = letters[new_index]
        else:
            digit_index = digits.find(c)
            if digit_index != -1:
                new_index = (digit_index + 3) % digits_len
                plus_three_filename[i] = digits[new_index]
            else:
                plus_three_filename[i] = c

        mod_filename = ''.join(plus_three_filename)
        if mod_filename != filename:
            break

    return append_extension_if_exists(mod_filename, extension)


def generate_404_by_flipping_bytes(filename, extension, seed=1):
    mod_filename = ''

    for i, (x, y) in enumerate(grouper(filename, 2)):

        # Handle the last iteration
        if y is None:
            mod_filename += x
            break

        # Allow the caller to control (in a random way) which chars will
        # be flip
        if not should_flip(i, seed):
            mod_filename += x + y
            continue

        # Flip the chars (based on should_flip)
        if x.isdigit() and y.isdigit():
            mod_filename += y + x
            continue

        if x in string.letters and y in string.letters:
            mod_filename += y + x
            continue

        #
        # Don't flip chars in cases where the types do not match, examples:
        #
        #   * (a, 1)
        #   * (1, a)
        #   * (a, @)
        #   * (1, @)
        #   * (1, %)
        #
        mod_filename += x + y

    return append_extension_if_exists(mod_filename, extension)


def generate_404_by_shuffle(filename, extension, seed):
    random.seed(seed)

    filename = [c for c in filename]

    random.shuffle(filename)
    mod_filename = ''.join(filename)

    return append_extension_if_exists(mod_filename, extension)


def append_extension_if_exists(filename, extension):
    final_result = filename

    if extension is not None:
        final_result += u'.%s' % extension

    return final_result


def split_filename(filename):
    split = filename.rsplit(u'.', 1)

    if len(split) == 2:
        orig_filename, extension = split
    else:
        extension = None
        orig_filename = split[0]

    return orig_filename, extension


def generate_404_filename(filename, seed=1):
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
    :param seed: The seed to control how the random files are changed
    :return: A mutated filename
    """
    if not filename:
        return generate_404_without_filename()

    orig_filename, extension = split_filename(filename)

    #
    # This handles the case of files which don't have a name,
    # such as .env.
    #
    if not orig_filename:
        return generate_404_without_name(extension)

    #
    # This handles the case of files which have really short names
    # such as "a.html" or "ac.rb". When trying to modify those short
    # names it is likely that we'll end up with either the same one
    # or another one that also exists in the path
    #
    if len(orig_filename) in (1, 2):
        return generate_404_for_short_filename(orig_filename, extension)

    #
    # Flip some bytes to generate a new filename
    #
    mod_filename = generate_404_by_flipping_bytes(orig_filename,
                                                  extension,
                                                  seed=seed)

    if mod_filename != filename:
        return mod_filename

    #
    # In some scenarios the char flipping algorithm above does not change the
    # filename at all, for example: "a-b-c" is not flipped because (a, -) and
    # (b, -) are not in the same letter set.
    #
    # Something else that might happen is that the should_flip() function
    # returns false for the cases where the chars are in the same letter set
    #
    # This part of the function does a "rot-3" (not rot-13) for the least number
    # of letters to force the change
    #
    mod_filename = generate_404_by_rot3(orig_filename, extension, seed=seed)
    if mod_filename != filename:
        return mod_filename

    #
    # We get here when nothing works, just return something random that has
    # the same chars as the original one
    #
    return generate_404_by_shuffle(orig_filename, extension, seed=seed)


def grouper(iterable, n, fillvalue=None):
    """
    Collect data into fixed-length chunks or blocks
    """
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


def send_request_generate_404(uri_opener, http_response, debugging_id, exclude=None):
    exclude = [] if exclude is None else exclude

    #
    # Make sure to generate a URL which is not in exclude!
    #
    url_404 = None

    for seed in xrange(25):
        url_404 = get_url_for_404_request(http_response, seed=seed)
        if url_404.url_string not in exclude:
            break

    response_404 = send_404(uri_opener, url_404, debugging_id=debugging_id)
    return FourOhFourResponse.from_http_response(response_404)


def get_url_for_404_request(http_response, seed=1):
    """
    :param http_response: The HTTP response to modify
    :param seed: The random number generator initialization seed to use when
                 generating the filenames
    :return: A new URL with randomly generated filename or path that will
             trigger a 404.
    """
    response_url = http_response.get_url()
    path = response_url.get_path()
    filename = response_url.get_file_name()

    if path == '/' or filename:
        relative_url = generate_404_filename(filename, seed=seed)
        url_404 = response_url.copy()
        url_404.set_file_name(relative_url)

    else:
        relative_url = '../%s/' % rand_alnum(8, seed=seed)
        url_404 = response_url.url_join(relative_url)

    return url_404


@retry(tries=2, delay=0.5, backoff=2)
def send_404(uri_opener, url_404, debugging_id=None):
    """
    Sends a GET request to url404.

    :return: The HTTP response body.
    """
    try:
        # Note that the cache is used for this request because url_404 was
        # generated using a predictable algorithm, by caching the 404 responses
        # we might be speeding up other calls to is_404
        response = uri_opener.GET(url_404,
                                  cache=True,
                                  grep=False,
                                  debugging_id=debugging_id)
    except HTTPRequestException, hre:
        message = 'Exception found while detecting 404: "%s" (did:%s)'
        args = (hre, debugging_id)
        om.out.debug(message % args)
        raise FourOhFourDetectionException(message % args)
    else:
        msg = 'Received response for 404 URL %s (id:%s, did:%s, len:%s)'
        args = (url_404, response.id, debugging_id, len(response.body))
        om.out.debug(msg % args)

    return response
