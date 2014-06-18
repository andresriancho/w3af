"""
string_representation.py

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


class StringRepresentation(object):
    """
    Generates an image representation of any string. Very useful for comparing
    two or more strings in a split second. This representation can be used to
    generate an image, show in a GTK DrawingArea, etc.
    """

    def __init__(self, instr, width=60, height=40):
        """
        :param instr: The input string to represent.
        """
        self.parsed_instr = {}
        self.gen_representation(instr, width, height)

    def gen_representation(self, instr, width, height):
        """
        :param width: The width of the string to generate
        :param height: The width of the string to generate
        """
        linecount = lambda ln: sum(map(ord, (char for char in ln)))
        split = instr.split('\n')
        length = max(len(split), width)
        step, extra = divmod(length, width)

        sumlinecounts = lambda st, en: \
            sum(linecount(ln) for ln in split[st:en])

        for i, j in enumerate(xrange(0, length - extra, step)):
            accum = sumlinecounts(j, j + step)
            self.parsed_instr[i] = accum % height

        if extra:
            self.parsed_instr[i] = \
                (accum + sumlinecounts(j + step, None)) % height

    def get_representation(self):
        return self.parsed_instr
