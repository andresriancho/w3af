"""
generate_404_filename.py

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

from w3af.core.data.fuzzer.utils import rand_alnum


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
    split_filename = filename.rsplit(u'.', 1)
    if len(split_filename) == 2:
        orig_filename, extension = split_filename
    else:
        extension = None
        orig_filename = split_filename[0]

    #
    #   This handles the case of files which don't have a name,
    #   such as .env.
    #
    if not orig_filename:
        return u'%s.%s' % (rand_alnum(5), extension)

    def grouper(iterable, n, fillvalue=None):
        """
        Collect data into fixed-length chunks or blocks
        """
        # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
        args = [iter(iterable)] * n
        return itertools.izip_longest(fillvalue=fillvalue, *args)

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
