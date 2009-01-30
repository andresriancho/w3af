# -*- Mode: Python; py-indent-offset: 4 -*-
# pygobject - Python bindings for the GObject library
# Copyright (C) 2006  Johannes Hoelzl
#
#   gobject/option.py: GOption command line parser
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

"""GOption command line parser

Extends optparse to use the GOptionGroup, GOptionEntry and GOptionContext
objects. So it is possible to use the gtk, gnome_program and gstreamer command
line groups and contexts.

Use this interface instead of the raw wrappers of GOptionContext and
GOptionGroup in gobject.
"""

import sys
import optparse
from optparse import OptParseError, OptionError, OptionValueError, \
                     BadOptionError, OptionConflictError
import _gobject as gobject

__all__ = [
    "OptParseError",
    "OptionError",
    "OptionValueError",
    "BadOptionError",
    "OptionConflictError"
    "Option",
    "OptionGroup",
    "OptionParser",
    "make_option",
]

class Option(optparse.Option):
    """Represents a command line option

    To use the extended possibilities of the GOption API Option
    (and make_option) are extended with new types and attributes.

    Types:
        filename   The supplied arguments are read as filename, GOption
                   parses this type in with the GLib filename encoding.

    Attributes:
        optional_arg  This does not need a arguement, but it can be supplied.
        hidden        The help list does not show this option
        in_main       This option apears in the main group, this should only
                      be used for backwards compatibility.

    Use Option.REMAINING as option name to get all positional arguments.

    NOTE: Every argument to an option is passed as utf-8 coded string, the only
          exception are options which use the 'filename' type, its arguments
          are passed as strings in the GLib filename encoding.

    For further help, see optparse.Option.
    """
    TYPES = optparse.Option.TYPES + (
        'filename',
    )

    ATTRS = optparse.Option.ATTRS + [
        'hidden',
        'in_main',
        'optional_arg',
    ]

    REMAINING = '--' + gobject.OPTION_REMAINING

    def __init__(self, *args, **kwargs):
        optparse.Option.__init__(self, *args, **kwargs)
        if not self._long_opts:
            raise ValueError("%s at least one long option name.")

        if len(self._long_opts) < len(self._short_opts):
            raise ValueError(
                "%s at least more long option names than short option names.")

        if not self.help:
            raise ValueError("%s needs a help message.", self._long_opts[0])


    def _set_opt_string(self, opts):
        if self.REMAINING in opts:
            self._long_opts.append(self.REMAINING)
        optparse.Option._set_opt_string(self, opts)
        if len(self._short_opts) > len(self._long_opts):
            raise OptionError("goption.Option needs more long option names "
                              "than short option names")

    def _to_goptionentries(self):
        flags = 0

        if self.hidden:
            self.flags |= gobject.OPTION_FLAG_HIDDEN

        if self.in_main:
            self.flags |= gobject.OPTION_FLAG_IN_MAIN

        if self.takes_value():
            if self.optional_arg:
                flags |= gobject.OPTION_FLAG_OPTIONAL_ARG
        else:
            flags |= gobject.OPTION_FLAG_NO_ARG

        if self.type == 'filename':
            flags |= gobject.OPTION_FLAG_FILENAME

        for (long_name, short_name) in zip(self._long_opts, self._short_opts):
            yield (long_name[2:], short_name[1], flags, self.help, self.metavar)

        for long_name in self._long_opts[len(self._short_opts):]:
            yield (long_name[2:], '\0', flags, self.help, self.metavar)

class OptionGroup(optparse.OptionGroup):
    """A group of command line options.

    Arguements:
       name:             The groups name, used to create the
                         --help-{name} option
       description:      Shown as title of the groups help view
       help_description: Shown as help to the --help-{name} option
       option_list:      The options used in this group, must be option.Option()
       defaults:         A dicitionary of default values
       translation_domain: Sets the translation domain for gettext().

    NOTE: This OptionGroup does not exactly map the optparse.OptionGroup
          interface. There is no parser object to supply, but it is possible
          to set default values and option_lists. Also the default values and
          values are not shared with the OptionParser.

    To pass a OptionGroup into a function which expects a GOptionGroup (e.g.
    gnome_program_init() ). OptionGroup.get_option_group() can be used.

    For further help, see optparse.OptionGroup.
    """
    def __init__(self, name, description, help_description="",
                 option_list=None, defaults=None,
                 translation_domain=None):
        optparse.OptionContainer.__init__(self, Option, 'error', description)
        self.name = name
        self.parser = None
        self.help_description = help_description
        if defaults:
            self.defaults = defaults

        self.values = None

        self.translation_domain = translation_domain

        if option_list:
            for option in option_list:
                self.add_option(option)

    def _create_option_list(self):
        self.option_list = []
        self._create_option_mappings()

    def _to_goptiongroup(self, parser):
        def callback(option_name, option_value, group):
            if option_name.startswith('--'):
                opt = self._long_opt[option_name]
            else:
                opt = self._short_opt[option_name]

            try:
                opt.process(option_name, option_value, self.values, parser)
            except OptionValueError, error:
            	gerror = gobject.GError(str(error))
            	gerror.domain = gobject.OPTION_ERROR
            	gerror.code = gobject.OPTION_ERROR_BAD_VALUE
            	gerror.message = str(error)
            	raise gerror

        group = gobject.OptionGroup(self.name, self.description,
                                    self.help_description, callback)
        if self.translation_domain:
            group.set_translation_domain(self.translation_domain)

        entries = []
        for option in self.option_list:
            entries.extend(option._to_goptionentries())
        group.add_entries(entries)

        return group

    def get_option_group(self, parser = None):
        """ Returns the corresponding GOptionGroup object.

        Can be used as parameter for gnome_program_init(), gtk_init().
        """
        self.set_values_to_defaults()
        return self._to_goptiongroup(parser)

    def set_values_to_defaults(self):
        for option in self.option_list:
            default = self.defaults.get(option.dest)
            if isinstance(default, basestring):
                opt_str = option.get_opt_string()
                self.defaults[option.dest] = option.check_value(
                    opt_str, default)
        self.values = optparse.Values(self.defaults)

class OptionParser(optparse.OptionParser):
    """Command line parser with GOption support.

    NOTE: The OptionParser interface is not the exactly the same as the
          optparse.OptionParser interface. Especially the usage parameter
          is only used to show the metavar of the arguements.

    Attribues:
        help_enabled:           The --help, --help-all and --help-{group}
                                options are enabled (default).
        ignore_unknown_options: Do not throw a exception when a option is not
                                knwon, the option will be in the result list.

    OptionParser.add_option_group() does not only accept OptionGroup instances
    but also gobject.OptionGroup, which is returned by gtk_get_option_group().

    Only gobject.option.OptionGroup and gobject.option.Option instances should
    be passed as groups and options.

    For further help, see optparse.OptionParser.
    """

    def __init__(self, *args, **kwargs):
        if 'option_class' not in kwargs:
            kwargs['option_class'] = Option
        self.help_enabled = kwargs.pop('help_enabled', True)
        self.ignore_unknown_options = kwargs.pop('ignore_unknown_options',
                                                 False)
        optparse.OptionParser.__init__(self, add_help_option=False,
                                       *args, **kwargs)

    def set_usage(self, usage):
        if usage is None:
            self.usage = ''
        elif usage.startswith("%prog"):
            self.usage = usage[len("%prog"):]
        else:
            self.usage = usage

    def _to_goptioncontext(self, values):
        if self.description:
            parameter_string = self.usage + " - " + self.description
        else:
            parameter_string = self.usage
        context = gobject.OptionContext(parameter_string)
        context.set_help_enabled(self.help_enabled)
        context.set_ignore_unknown_options(self.ignore_unknown_options)

        for option_group in self.option_groups:
            if isinstance(option_group, gobject.OptionGroup):
                g_group = option_group
            else:
                g_group = option_group.get_option_group(self)
            context.add_group(g_group)

        def callback(option_name, option_value, group):
            if option_name.startswith('--'):
                opt = self._long_opt[option_name]
            else:
                opt = self._short_opt[option_name]
            opt.process(option_name, option_value, values, self)

        main_group = gobject.OptionGroup(None, None, None, callback)
        main_entries = []
        for option in self.option_list:
            main_entries.extend(option._to_goptionentries())
        main_group.add_entries(main_entries)
        context.set_main_group(main_group)

        return context

    def add_option_group(self, *args, **kwargs):
        if isinstance(args[0], basestring):
            optparse.OptionParser.add_option_group(self,
                OptionGroup(self, *args, **kwargs))
            return
        elif len(args) == 1 and not kwargs:
            if isinstance(args[0], OptionGroup):
                if not args[0].parser:
                    args[0].parser = self
                if args[0].parser is not self:
                    raise ValueError("invalid OptionGroup (wrong parser)")
            if isinstance(args[0], gobject.OptionGroup):
                self.option_groups.append(args[0])
                return
        optparse.OptionParser.add_option_group(self, *args, **kwargs)

    def _get_all_options(self):
        options = self.option_list[:]
        for group in self.option_groups:
            if isinstance(group, optparse.OptionGroup):
                options.extend(group.option_list)
        return options

    def _process_args(self, largs, rargs, values):
        context = self._to_goptioncontext(values)
        largs.extend(context.parse([sys.argv[0]] + rargs))

    def parse_args(self, args=None, values=None):
        try:
            return optparse.OptionParser.parse_args(self, args, values)
        except gobject.GError, error:
            if error.domain != gobject.OPTION_ERROR:
            	raise
            if error.code == gobject.OPTION_ERROR_BAD_VALUE:
                raise OptionValueError(error.message)
            elif error.code == gobject.OPTION_ERROR_UNKNOWN_OPTION:
    	        raise BadOptionError(error.message)
            elif error.code == gobject.OPTION_ERROR_FAILED:
                raise OptParseError(error.message)
            else:
                raise

make_option = Option
