"""
output_plugin.py

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
import inspect

import w3af.core.data.constants.severity as severity
from w3af.core.controllers.plugins.plugin import Plugin


class OutputPlugin(Plugin):
    """
    This is the base class for data output, all output plugins should inherit
    from it and implement the following methods :
        1. debug( message, verbose )
        2. information( message, verbose )
        3. error( message, verbose )
        4. vulnerability( message, verbose )

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    STRING_CLEAN = [('\0', '\\0'),
                    ('\t', '\\t'),
                    ('\n', '\\n'),
                    ('\r', '\\r')]

    def __init__(self):
        Plugin.__init__(self)

        # If for some reason the output plugin takes a lot of time to run
        # and the output manager calls flush() for a second time while we're
        # still running the first call, just ignore.
        self.is_running_flush = False

    def get_type(self):
        return 'output'

    def debug(self, message, new_line=True):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.

        :return: No value is returned.
        """
        raise NotImplementedError

    def information(self, message, new_line=True):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action for information messages.

        :return: No value is returned.
        """
        raise NotImplementedError

    def error(self, message, new_line=True):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action for error messages.

        :return: No value is returned.
        """
        raise NotImplementedError

    def vulnerability(self, message, new_line=True, severity=severity.MEDIUM):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action for vulnerability messages.

        :return: No value is returned.
        """
        raise NotImplementedError

    def console(self, message, new_line=True):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action for console messages.

        :return: No value is returned.
        """
        raise NotImplementedError

    def log_http(self, request, response):
        """
        This method is called from the output manager object. The OM object was
        called from a plugin or from the framework. This method should take an
        action to log HTTP requests and responses.

        :return: No value is returned.
        """
        pass

    def log_crash(self, crash_message):
        """
        The ExceptionHandler receives all unhandled exceptions generated during
        a scan, and calls log_crash() with the crash report (also saved to
        /tmp/w3af-crash files) so that output plugins can write them in the
        appropriate format.

        :return: No value is returned.
        """
        pass

    def log_enabled_plugins(self, enabled_plugins_dict, plugin_options_dict):
        """
        This method logs to the output plugins the enabled plugins and their
        configuration.

        :param enabled_plugins_dict: As returned by
                                     w3afCore.get_all_enabled_plugins() looks
                                     similar to:

                                    {'audit':[],'grep':[],'bruteforce':[],
                                     'crawl':[],...}

        :param plugin_options_dict: As defined in the w3afCore, looks similar to

                                    {'audit':{},'grep':{},'bruteforce':{},
                                     'crawl':{},...}
        """
        pass

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be
        run before the current one.
        """
        return []

    def flush(self):
        """
        Write vulnerabilities and any other important information to the output
        file/socket.

        This method is called once every OutputManager.FLUSH_TIMEOUT by the
        OutputManager and is useful to give feedback to the user before the
        scan ends.

        :see: https://github.com/andresriancho/w3af/issues/6726
        :return: None
        """
        pass

    def _clean_string(self, string_to_clean):
        """
        :param string_to_clean: A string that should be cleaned before using
                                it in a message object.
        """
        # https://github.com/andresriancho/w3af/issues/3586
        if string_to_clean is None:
            return ''

        for char, replace in self.STRING_CLEAN:
            string_to_clean = string_to_clean.replace(char, replace)

        return string_to_clean

    def get_caller(self, which_stack_item=4):
        """
        What I'm going to do is:
            - inspect the stack and try to find a reference to a plugin
            - if a plugin is the caller, then i'll return something like audit.xss
            - if no plugin is in the caller stack, i'll return the stack item
              specified by which_stack_item

        Maybe you are asking yourself why which_stack_item == 4, well, this is
        why:
            I know that get_caller method will be in the stack
            I also know that the method that calls get_caller will be in stack
            I also know that the om.out.XYZ method will be in the stack
            That's 3... so... number 4 is the one that really called me.

        :return: The caller of the om.out.XYZ method; this is used to make
                 output more readable.

        >>> bop = OutputPlugin()
        >>> bop.get_caller()
        'doctest'

        """
        try:
            the_stack = inspect.stack()

            for item in the_stack:
                if item[1].startswith('plugins/'):
                    # Now I have the caller item from the stack, I want to do
                    # some things with it...
                    res = item[1].replace('plugins/', '')
                    res = res.replace('/', '.')
                    return res.replace('.py', '')
            else:
                # From the unknown caller, I just need the name of the function
                item = the_stack[which_stack_item]
                res = item[1].split('/')[-1:][0]
                return res.replace('.py', '')

        except Exception:
            return 'unknown-caller'

    def _create_plugin_info(self, plugin_type, plugins_list, plugins_options):
        """
        :return: A string with the information about enabled plugins and their
                 options.

        :param plugin_type: audit, crawl, etc.
        :param plugins_list: A list of the names of the plugins of
                                 plugin_type that are enabled.
        :param plugins_options: The options for the plugins
        """
        response = ''

        # Only work if something is enabled
        if plugins_list:
            response = 'plugins\n'
            response += '    ' + plugin_type + ' ' + ', '.join(plugins_list) + '\n'

            for plugin_name in plugins_list:
                if plugin_name in plugins_options:
                    response += '    ' + plugin_type + ' config ' + plugin_name + '\n'

                    for plugin_option in plugins_options[plugin_name]:
                        name = str(plugin_option.get_name())
                        value = str(plugin_option.get_value())
                        response += '        set ' + name + ' ' + value + '\n'

                    response += '        back\n'

            response += '    back\n'

        # The response
        return response
