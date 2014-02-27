"""
utils.py

Copyright 2011 Andres Riancho

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


def is_black_image(img_inst):
    """:return: True if the image is completely black"""
    img_width, img_height = img_inst.size

    for x in xrange(img_width):
        for y in xrange(img_height):
            # 0 means black color
            if img_inst.getpixel((x, y)) != 0:
                return False

    return True
