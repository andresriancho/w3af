"""
preferences.py

Copyright 2010 Andres Riancho

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
from __future__ import with_statement

import os

from ConfigParser import RawConfigParser

from w3af.core.controllers.misc.home_dir import get_home_dir
from w3af.core.controllers.exceptions import BaseFrameworkException


class Preferences(object):
    """Class for grouping option lists.

    It also support saving into files.
    """
    def __init__(self, label=None):
        self.sections = {}
        self.options = {}
        if label:
            self.filename = os.path.join(get_home_dir(), label + '.cfg')

    def add_section(self, section='default', label=None, options_list=None):
        """Add a section named section to the instance."""
        self.sections[section] = label
        self.options[section] = options_list

    def has_section(self, section):
        """
        Indicates whether the named section is present in the configuration.
        """
        return section in self.sections

    def get_options(self, section):
        """Returns a list of options available in the specified section."""
        return self.options[section]

    def has_option(self, section, option):
        """If the given section exists, and contains the given option, return
        True; otherwise return False."""
        if section in self.options and option in self.options[section]:
            return True
        else:
            return False

    def get(self, section, option):
        """Get an option value for the named section."""
        if self.has_option(section, option):
            return self.options[section][option]

    def get_value(self, section, option):
        """Get an option value for the named section."""
        if self.has_option(section, option):
            return self.options[section][option].get_value()

    def set(self, section, option):
        """
        If the given section exists, set the given option to the specified
        value; otherwise raise NoSectionError.
        """
        if self.has_section(section):
            self.options[section][option.get_name()] = option

    def set_value(self, section, option, value):
        """
        If the given section exists, set the given option to the specified
        value; otherwise raise NoSectionError.
        """
        if self.has_section(section):
            self.options[section][option].set_value(value)

    def remove_option(self, section, option):
        """Remove the specified option from the specified section.
        If the section does not exist, raise NoSectionError."""
        if section in self.sections:
            del self.sections[section][option]

    def remove_section(self, section):
        """Remove the specified section from the configuration.
        If the section in fact existed, return True. Otherwise return False."""
        if section in self.sections:
            del self.sections[section]
            del self.options[section]
            return True
        else:
            return False

    def load_values(self):
        """
        Read values of options from file.
        """
        config = RawConfigParser()
        config.read(self.filename)
        sections = config.sections()

        for section in sections:

            if self.has_section(section):
                options = config.options(section)

                for option in options:
                    if self.has_option(section, option):
                        try:
                            self.set_value(section, option,
                                           config.get(section, option))
                        except BaseFrameworkException:
                            # In some cases the user touches the file by hand
                            # and then the framework will fail to validate
                            #
                            # https://github.com/andresriancho/w3af/issues/1816
                            pass

    def save(self):
        """Save values of options to file."""
        config = RawConfigParser()
        for section in self.sections:
            config.add_section(section)
            for option in self.options[section]:
                config.set(section, option.get_name(), option.get_value_str())

        with open(self.filename, 'w') as configfile:
            config.write(configfile)
