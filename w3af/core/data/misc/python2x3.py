#!/usr/bin/env python

"""Provides code and data to facilitate writing python code that runs on 2.x and 3.x, including pypy"""

# I'm afraid pylint won't like this one...

import sys


def python_major():
    """Return an integer corresponding to the major version # of the python interpreter we're running on"""
    # This originally used the platform module, but platform fails on IronPython; sys.version seems to work
    # on everything I've tried
    result = sys.version_info[0]
    return result

if python_major() == 2:
    empty_bytes = ''
    null_byte = '\0'
    bytes_type = str

    def intlist_to_binary(intlist):
        """Convert a list of integers to a binary string type"""
        return ''.join(chr(byte) for byte in intlist)

    def string_to_binary(string):
        """Convert a text string to a binary string type"""
        return string

    def binary_to_intlist(binary):
        """Convert a binary string to a list of integers"""
        return [ord(character) for character in binary]

    def binary_to_string(binary):
        """Convert a binary string to a text string"""
        return binary
elif python_major() == 3:
    empty_bytes = ''.encode('utf-8')
    null_byte = bytes([0])
    bytes_type = bytes

    def intlist_to_binary(intlist):
        """Convert a list of integers to a binary string type"""
        return bytes(intlist)

    def string_to_binary(string):
        """Convert a text string (or binary string type) to a binary string type"""
        if isinstance(string, str):
            return string.encode('latin-1')
        else:
            return string

    def binary_to_intlist(binary):
        """Convert a binary string to a list of integers"""
        return binary

    def binary_to_string(binary):
        """Convert a binary string to a text string"""
        return binary.decode('latin-1')
else:
    sys.stderr.write(
        '%s: Python < 2 or > 3 not (yet) supported\n' % sys.argv[0])
    sys.exit(1)
