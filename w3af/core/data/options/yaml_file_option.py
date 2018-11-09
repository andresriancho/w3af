"""
yaml_file_option.py

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

import yaml

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.options.baseoption import BaseOption
from w3af.core.data.options.input_file_option import InputFileOption
from w3af.core.data.options.option_types import YAML_INPUT_FILE

ROOT_PATH_VAR = '%ROOT_PATH%'


class YamlFileOption(BaseOption):

    _type = YAML_INPUT_FILE

    def set_value(self, value):
        """
        :param value: The value parameter is set by the user interface, which
        for example sends 'spec/openapi.yaml' or '%ROOT_PATH%/values.yml'.

        If required we replace the %ROOT_PATH% with the right value for this
        platform.
        """
        validated_value = self.validate(value)

        self._value = InputFileOption.get_relative_path(validated_value)

    def validate(self, value):
        """
        Check if a file has a valid Yaml data.
        The method throws BaseFrameworkException if something goes wrong.

        :param value: User input, which might look like:
                        * spec/openapi.yaml
                        * %ROOT_PATH%/values.yml
        :return: Validated path to show to the user.
        """
        filename = value.replace(ROOT_PATH_VAR, ROOT_PATH)

        try:
            with open(filename, 'r') as content:
                yaml_data = yaml.load(content)
                if yaml_data is None:
                    msg = 'No Yaml loaded from %s.'
                    raise BaseFrameworkException(msg % value)
        except IOError, e:
            msg = 'Could not read file %s, error: %s.'
            raise BaseFrameworkException(msg % (value, e))
        except yaml.YAMLError, e:
            msg = 'Could not parse YAML: %s.'
            raise BaseFrameworkException(msg % e)
        except Exception, e:
            msg = 'Unexpected exception, error: %s.'
            raise BaseFrameworkException(msg % e)

        # Everything looks fine.
        return filename

    def get_value_for_profile(self, self_contained=False):
        """
        This method is called before saving the option value to the profile file

        :return: A string representation of the path, with the ROOT_PATH
                 replaced with %ROOT_PATH%. Then when we load a value in
                 set_value we're going to replace the %ROOT_PATH% with ROOT_PATH
        """
        abs_path = os.path.abspath(self._value)
        return abs_path.replace(ROOT_PATH, ROOT_PATH_VAR)
