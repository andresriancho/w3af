"""
input_file_option.py

Copyright 2008 Andres Riancho

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
import zlib
import base64
import tempfile

from w3af import ROOT_PATH
from w3af.core.controllers.misc.temp_dir import get_temp_dir
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.option_types import INPUT_FILE

ROOT_PATH_VAR = '%ROOT_PATH%'


class InputFileOption(BaseOption):

    _type = INPUT_FILE

    DATA_PREFIX = 'w3af-'
    DATA_SUFFIX = '-sc.dat'
    DATA_PROTO = 'base64://'

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends "w3af/plugins/audit/ssl_certificate/ca.pem" or
        "%ROOT_PATH%/plugins/audit/ssl_certificate/ca.pem".

        If required we replace the %ROOT_PATH% with the right value for this
        platform.

        Something else we support is the base64:// data handler, which allows
        us to have self-contained profiles as described in [0]. When a value
        like that is set, we decode+unzip, save the data to a temp file and
        set that file path as value.

        [0] https://github.com/andresriancho/w3af/issues/10949
        """
        if value == '':
            self._value = value
            return

        validated_value = self.validate(value)

        # I want to make the paths shorter, so we're going to make them
        # relative, at least in the case where they are inside the cwd
        current_dir = os.path.abspath(os.curdir)
        configured_value_dir = os.path.abspath(os.path.dirname(validated_value))

        if configured_value_dir.startswith(current_dir):
            self._value = os.path.relpath(validated_value)
        else:
            self._value = validated_value

    def get_value_for_profile(self, self_contained=False):
        """
        This method is called before saving the option value to the profile file

        Added when fixing:
            https://github.com/andresriancho/w3af/issues/402

        :return: A string representation of the path, with the ROOT_PATH
                 replaced with %ROOT_PATH%. Then when we load a value in
                 set_value we're going to replace the %ROOT_PATH% with ROOT_PATH

                 Something else we do here is to convert the temp file we
                 created during the base64:// data handler back to the base64://
                 string. This allows us to keep profiles which are
                 self-contained in that state.
        """
        #
        #   First we handle base64://
        #
        if self_contained or self.should_base64_encode_file(self._value):
            try:
                return self.encode_b64_data(self._value)
            except Exception, e:
                msg = ('An exception occurred while encoding "%s" for storing'
                       ' into the profile: "%s"')
                raise BaseFrameworkException(msg % (self._value, e))

        #
        #   Then the other options
        #
        abs_path = os.path.abspath(self._value)
        replaced_value = abs_path.replace(ROOT_PATH, ROOT_PATH_VAR)
        return replaced_value

    def validate(self, value):
        """
        Performs a ton of checks to make sure the user's input is valid, raising
        BaseFrameworkException if something fails.

        :param value: User input, which might look like:
                        * /home/foo/file
                        * %ROOT_PATH%/foo/file
                        * base64://...
        :return: The decoded value to show to the user
        """
        #
        #   First we handle the base64:// protocol since it's the most specific
        #   one we support
        #
        if self.is_base64_data(value):
            try:
                return self.create_tempfile(value)
            except zlib.error:
                msg = 'The self contained file raised a zlib decoding error'
                raise BaseFrameworkException(msg)
            except TypeError:
                msg = 'The self contained file raised a base64 decode error'
                raise BaseFrameworkException(msg)

        #
        #   And now the other supported formats
        #
        value = value.replace(ROOT_PATH_VAR, ROOT_PATH)

        directory = os.path.abspath(os.path.dirname(value))
        if not os.path.isdir(directory):
            msg = ('Invalid input file option value "%s", the directory does'
                   ' not exist.')
            raise BaseFrameworkException(msg % value)

        if not os.access(directory, os.R_OK):
            msg = ('Invalid input file option value "%s", the user does not'
                   ' have enough permissions to read from the specified'
                   ' directory.')
            raise BaseFrameworkException(msg % value)

        if not os.path.exists(value):
            msg = ('Invalid input file option value "%s", the specified file'
                   ' does not exist.')
            raise BaseFrameworkException(msg % value)

        if not os.access(value, os.R_OK):
            msg = ('Invalid input file option value "%s", the user does not'
                   ' have enough permissions to read the specified file.')
            raise BaseFrameworkException(msg % value)

        if not os.path.isfile(value):
            msg = ('Invalid input file option value "%s", the path does not'
                   ' point to a file.')
            raise BaseFrameworkException(msg % value)

        return value

    def is_base64_data(self, value):
        """
        :param value: The value we get from the user/profile
        :return: True if it's a base64:// data
        """
        return value.startswith(self.DATA_PROTO)

    def should_base64_encode_file(self, filename):
        """
        :param filename: The filename which we're saving
        :return: True if the filename matches the pattern used to decode
                 base64:// data
        """
        if filename.endswith(self.DATA_SUFFIX) and self.DATA_PREFIX in filename:
            return True

        return False

    def create_tempfile(self, encoded_data):
        _file = tempfile.NamedTemporaryFile(mode='w+b',
                                            suffix=self.DATA_SUFFIX,
                                            prefix=self.DATA_PREFIX,
                                            delete=False,
                                            dir=get_temp_dir())

        data = self.decode_b64_data(encoded_data)

        _file.write(data)
        _file.close()

        return _file.name

    def decode_b64_data(self, encoded_data):
        """
        Base64 decode, gunzip, return string.

        :param encoded_data: The data that (most likely) comes from a base64://
                             string stored in the profile. It MUST CONTAIN
                             the base64:// specification at the beginning.
        :return: The decoded data
        """
        encoded_data = encoded_data[len(self.DATA_PROTO):]
        encoded_data = base64.b64decode(encoded_data)
        return encoded_data.decode('zlib')

    def encode_b64_data(self, filename):
        """
        Gzip the file contents, base64 encode it, return as string.

        :param filename: The filename that holds the bytes to encode
        :return: Encoded data which can be decoded using decode_b64_data, this
                 output is usually stored in a profile.
        """
        data = base64.b64encode(file(filename).read().encode('zlib')).strip()
        return '%s%s' % (self.DATA_PROTO, data)

