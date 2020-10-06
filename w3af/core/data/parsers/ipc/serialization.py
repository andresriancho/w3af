"""
serialization.py

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
import os
import cPickle
import tempfile

import msgpack


from w3af.core.data.parsers.doc.sgml import Tag
from w3af.core.controllers.misc.temp_dir import get_temp_dir


class FileSerializer:
    def __init__(self, file_directory=None):
        self.file_directory = file_directory or get_temp_dir()
        # binding module level function for clearer interface
        self.remove_if_exists = remove_if_exists

    def save_http_response(self, http_response):
        """
        Write an HTTPResponse instance to a temp file using msgpack

        :param HTTPResponse http_response: The HTTP response
        :return str: The id which will make it possible to read the data again
        (it's the name of the file, but it does not matter at higher abstractions)
        """
        data_to_save = http_response.to_dict()
        http_response_id = self._dump_data_to_file(data_to_save, 'w3af-http-')
        return http_response_id

    def load_http_response(self, http_response_id):
        from w3af.core.data.url.HTTPResponse import HTTPResponse
        data = self._load_data_from_file(http_response_id)
        return HTTPResponse.from_dict(data)

    def save_tags(self, tag_list):
        """
        Write an Tag list to a temp file using msgpack

        :param tag_list: The Tag list
        :return: The name of the file
        """
        data = [t.to_dict() for t in tag_list]
        tags_id = self._dump_data_to_file(data, filename_prefix='w3af-tags-')
        return tags_id

    def load_tags(self, tags_id):
        data = self._load_data_from_file(tags_id)
        result = [Tag.from_dict(t) for t in data]
        return result

    def _load_data_from_file(self, filename, should_remove_file=True):
        try:
            data = msgpack.load(file(filename))
        finally:
            if should_remove_file:
                self.remove_if_exists(filename)
        return data

    def _dump_data_to_file(self, data, filename_prefix=''):
        """
        Tight coupled to tempfile and msgpack

        :param any data: data which will be saved to disk
        :return str: filename
        """
        temporary_file = tempfile.NamedTemporaryFile(
            prefix=filename_prefix,
            suffix='.pebble',
            delete=False,
            dir=self.file_directory,
        )
        msgpack.dump(data, temporary_file, use_bin_type=True)
        temporary_file.close()
        return temporary_file.name


def remove_if_exists(filename):
    """
    Remove the file if it exists

    :param filename: The filename to remove
    :return: True if file did exist
    """
    try:
        os.remove(filename)
        return True
    except OSError:
        return False


def get_temp_file(_type):
    """
    :return: A named temporary file which will not be removed on close
    """
    temp = tempfile.NamedTemporaryFile(prefix='w3af-%s-' % _type,
                                       suffix='.pebble',
                                       delete=False,
                                       dir=get_temp_dir())
    return temp


def write_object_to_temp_file(obj):
    """
    Write an object to a temp file using cPickle to serialize

    :param obj: The object
    :return: The name of the file
    """
    temp = get_temp_file('parser')
    cPickle.dump(obj, temp, cPickle.HIGHEST_PROTOCOL)
    temp.close()
    return temp.name


def load_object_from_temp_file(filename, remove=True):
    """
    Load an object from a temp file

    :param filename: The filename where the cPickle serialized object lives
    :param remove: Remove the file after reading
    :return: The object instance
    """
    try:
        result = cPickle.load(file(filename, 'rb'))
    except cPickle.PicklingError:
        if remove:
            remove_if_exists(filename)
        raise
    else:
        if remove:
            remove_if_exists(filename)
        return result
