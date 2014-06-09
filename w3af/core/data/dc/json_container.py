"""
json.py

Copyright 2014 Andres Riancho

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
import json

from w3af.core.data.dc.token import DataToken
from w3af.core.data.dc.kv_container import KeyValueContainer
from w3af.core.data.constants.encodings import UTF8


ERR_MSG = 'Unsupported data "%s" for json container.'


class JSONContainer(KeyValueContainer):
    """
    This class represents a data container for json.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, json_post_data, encoding=UTF8):
        """
        :param json_post_data: The XMLRPC call as string
        """
        KeyValueContainer.__init__(self, init_val=[], encoding=encoding)

        if not isinstance(json_post_data, basestring):
            raise TypeError(ERR_MSG % json_post_data)

        if not JSONContainer.is_json(json_post_data):
            raise ValueError(ERR_MSG % json_post_data[:50])

        self.parse_json(json_post_data)

    @staticmethod
    def is_json(post_data):
        try:
            json.loads(post_data)
        except:
            return False
        else:
            return True

    def parse_json(self, json_post_data):
        """
        Parses the json post data and stores all the information required to
        fuzz it as attributes.

        :param json_post_data: The JSON as a string
        :raises: ValueError if the json_post_data is not valid XML or XML-RPC
        """
        try:
            self._json = json.loads(json_post_data)
        except:
            raise ValueError(ERR_MSG % json_post_data[:50])

    @classmethod
    def from_postdata(cls, post_data):
        return cls(post_data)

    def __str__(self):
        """
        :return: string representation by writing back to JSON string
        """
        return json.dumps(self._json)

    def iter_tokens(self):
        """
        DataToken instances unbound to any data container are (mostly)
        useless. Most likely you should use iter_bound_tokens

        :yield: DataToken instances to help in the fuzzing process of this
                DataContainer.
        """
        for k, v in self.items():
            for ele in v:
                yield DataToken(k, ele)

    def iter_bound_tokens(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/580
        :see: Mostly used in Mutant._create_mutants_worker
        :yield: Tuples with:
                    - A copy of self
                    - A token set to the right location in the copy of self
        """
        for k, v in self.items():
            for idx, ele in enumerate(v):
                token = DataToken(k, ele)

                dcc = copy.deepcopy(self)
                dcc[k][idx] = token
                dcc.token = token

                yield dcc, token

    def iter_setters(self):
        """
        :yield: Tuples containing:
                    * The key as a string
                    * The value as a string
                    * The setter to modify the value
        """
        for k, v in self.items():
            for idx, ele in enumerate(v):
                yield k, ele, partial(v.__setitem__, idx)

    def set_token(self, key_name, index_num):
        """
        Sets the token in the DataContainer to point to the variable specified
        in *args. Usually args will be one of:
            * ('id',) - When the data container doesn't support repeated params
            * ('id', 3) - When it does

        :raises: An exception when the DataContainer does NOT contain the
                 specified path in *args to find the variable
        :return: The token if we were able to set it in the DataContainer
        """
        for k, v in self.items():
            for idx, ele in enumerate(v):

                if key_name == k and idx == index_num:
                    token = DataToken(k, ele)

                    self[k][idx] = token
                    self.token = token

                    return token

        raise RuntimeError('Invalid token path %s/%s' % (key_name, index_num))

    def get_short_printable_repr(self):
        """
        :return: A string with a short printable representation of self
        """
        if len(str(self)) <= self.MAX_PRINTABLE:
            return str(self)

        if self.get_token() is not None:
            # I want to show the token variable and value in the output
            for k, v in self.items():
                for ele in v:
                    if isinstance(ele, DataToken):
                        dt_str = '%s=%s' % (ele.get_name(), ele.get_value())
                        return '...%s...' % dt_str[:self.MAX_PRINTABLE]
        else:
            # I'll simply show the first N parameter and values until the
            # MAX_PRINTABLE is achieved
            return str(self)[:self.MAX_PRINTABLE]