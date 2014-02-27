"""
get_file_list.py

Copyright 2006 Andres Riancho

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
import os


def get_file_list(directory, extension='.py'):
    """
    :return: A list of the files that are present in @directory and match
             @extension. The files returned won't have an extension.

    >>> from w3af import ROOT_PATH
    >>> fname_list = get_file_list(os.path.join(ROOT_PATH, 'plugins','audit'))
    >>> 'sqli' in fname_list
    True

    """
    filename_list = []

    for f in os.listdir(directory):
        fname, ext = os.path.splitext(f)
        if ext == extension and fname != '__init__':
            filename_list.append(fname)

    filename_list.sort()
    return filename_list
