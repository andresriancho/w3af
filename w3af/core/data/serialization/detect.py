"""
detect.py

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


INTERESTING_NODEJS_STRINGS = ['\n', '{', '(']
INTERESTING_JAVA_STRINGS = ['java.util',
                            'java/util',
                            'java/lang/',
                            'reflect.annotation',
                            'com.sun.org.',
                            'org.jboss.',
                            'org.apache.',
                            'java.rmi.',
                            'javax/',
                            'com/sun/']
INTERESTING_NET_STRINGS = ['mscorlib',
                           'System.Data',
                           'System.Collections',
                           'Int32',
                           'System.Windows',
                           '$type',
                           'MethodName',
                           'PublicKeyToken']


def is_pickled_data(data):
    """
    :param data: Some data that we see on the application
    :return: True if the data looks like a python pickle
    """
    # pickle is a \n separated format
    if data.count('\n') > 10:
        return True

    # which usually ends with these characters
    return data.endswith('\n.') or data.endswith('\ns.')


def is_java_serialized_data(data):
    """
    :param data: Some data that we see on the application
    :return: True if the data looks like a java serialized object
    """
    # All java serialized objects I've seen have non-printable chars
    has_binary = False

    for c in data:
        if c not in string.printable:
            has_binary = True
            break

    if not has_binary:
        return False

    for interesting_string in INTERESTING_JAVA_STRINGS:
        if interesting_string in data:
            return True

    return False


def is_nodejs_serialized_data(data):
    """
    :param data: Some data that we see on the application
    :return: True if the data looks like a nodejs serialized object
    """
    for interesting_string in INTERESTING_NODEJS_STRINGS:
        if interesting_string in data:
            return True

    return False


def is_net_serialized_data(data):
    """
    :param data: Some data that we see on the application
    :return: True if the data looks like a .NET serialized object
    """
    for interesting_string in INTERESTING_NET_STRINGS:
        if interesting_string in data:
            return True

    return False
