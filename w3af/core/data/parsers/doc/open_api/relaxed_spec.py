# -*- coding: UTF-8 -*-
"""
relaxed_spec.py

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
from bravado_core.spec import Spec
from bravado_core import formatter
from bravado_core.formatter import SwaggerFormat


class RelaxedSpec(Spec):
    """
    Just chill bro!

    w3af needs to be flexible, bravado-core needs to follow the OpenAPI
    specification.

    This class modifies some parts of the bravado-core Spec class that we found
    to be too strict while scanning real-life APIs that may not follow *all*
    of the OpenAPI specification, but are still usable.
    """
    def get_format(self, format_name):
        """
        One of the first things I noticed was that developers create custom
        formats like:

            orderId:
              description: Order reference
              example: e475f288-4e9b-43ea-966c-d3912e7a25b2
              format: uuid      <-------- HERE
              type: string

        And because the format was not defined in the OpenAPI specification the
        parser would send a warning and not handle the parameter properly.

        This method tries to fix the issue by always returning a generic
        user defined format
        """
        #
        # First try to handle the case with the default (OpenAPI spec-defined)
        # formats that are already included and handled by bravado-core
        #
        default_format = formatter.DEFAULT_FORMATS.get(format_name)
        if default_format is not None:
            return default_format

        #
        # Now we have to create a generic format handler, because the remote
        # OpenAPI spec uses it and we want to fuzz it
        #
        generic_format = SwaggerFormat(
            # name of the format as used in the Swagger spec
            format=format_name,

            # Callable to convert a python object to a string
            to_wire=lambda input_string: input_string,

            # Callable to convert a string to a python object
            to_python=lambda input_string: input_string,

            # Callable to validate the input string
            validate=validate_generic,

            # Description
            description='Generic format for w3af fuzzer'
        )

        return generic_format


def validate_generic(input_string):
    """
    Always return true, we can't really validate a format that a developer
    defined in an arbitrary way.

    :param input_string: The string to validate
    :return: True
    """
    return True
