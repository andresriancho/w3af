"""
console_message.py

Copyright 2019 Andres Riancho

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
import pprint


class ConsoleMessage(object):
    __slots__ = ('type', 'message', 'args')

    def __init__(self, _type, args):
        self.type = _type
        self.args = args
        self.message = self.get_message(args)

    def get_message(self, args):
        """
        When console.log('hello world') is called, the event args looks like:

            [{"type":"string","value":"hello world"}]

        This method extracts the value only if the args list has one item
        and the type is a string.

        :param args: The arguments passed to console.log
        :return: The message (if any) as a string
        """
        if not len(args) == 1:
            return None

        arg = args[0]

        _type = arg.get('type', None)
        if _type != 'string':
            return None

        value = arg.get('value', None)
        if value is None:
            return None

        return value

    def __str__(self):
        data = self.message if self.message is not None else '\n%s' % pprint.pformat(self.args, indent=4)
        return '<ConsoleMessage(%s): "%s">' % (self.type, data)

    __repr__ = __str__
