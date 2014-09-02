"""
BasePwdProfilingPlugin.py

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
from w3af.core.controllers.exceptions import BaseFrameworkException


class BasePwdProfilingPlugin(object):
    """
    This is the base plugin for all password profiling plugins.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        pass

    def get_words(self, response):
        """
        Get words from the body.
        THIS PLUGIN MUST BE IMPLEMENTED BY ALL PLUGINS.

        :param response: In most common cases, an html. Could be almost anything
        :return: Dict of strings:repetitions
        """
        raise BaseFrameworkException('The method get_words must be implemented'
                                     ' by all password profiling plugins.')
