"""
misc_settings.py

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
import w3af.core.data.kb.config as cf

from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.misc.get_local_ip import get_local_ip
from w3af.core.controllers.misc.get_net_iface import get_net_iface
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.parsers.url import URL
from w3af.core.data.options.option_types import URL_LIST


class MiscSettings(Configurable):
    """
    A class that acts as an interface for the user interfaces, so they can
    configure w3af settings using get_options and SetOptions.
    """

    def __init__(self):
        """
        Set the defaults and save them to the config dict.
        """
        #
        # User configured variables
        #
        if cf.cf.get('fuzz_cookies') is None:
            # It's the first time I'm run
            cf.cf.save('fuzz_cookies', False)
            cf.cf.save('fuzz_form_files', True)
            cf.cf.save('fuzzed_files_extension', 'gif')
            cf.cf.save('fuzz_url_filenames', False)
            cf.cf.save('fuzz_url_parts', False)
            cf.cf.save('fuzzable_headers', [])

            cf.cf.save('form_fuzzing_mode', 'tmb')

            cf.cf.save('max_discovery_time', 120)

            cf.cf.save('msf_location', '/opt/metasploit3/bin/')

            #
            #
            #
            ifname = get_net_iface()
            cf.cf.save('interface', ifname)

            #
            #   This doesn't send any packets, and gives you a nice default setting.
            #   In most cases, it is the "public" IP address, which will work perfectly
            #   in all plugins that need a reverse connection (rfi_proxy)
            #
            local_address = get_local_ip()
            if not local_address:
                local_address = '127.0.0.1'  # do'h!

            cf.cf.save('local_ip_address', local_address)
            cf.cf.save('non_targets', [])
            cf.cf.save('stop_on_first_exception', False)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        ######## Fuzzer parameters ########
        d = 'Indicates if w3af plugins will use cookies as a fuzzable parameter'
        opt = opt_factory('fuzz_cookies', cf.cf.get('fuzz_cookies'), d, 'boolean',
                          tabid='Fuzzer parameters')
        ol.add(opt)

        d = 'Indicates if w3af plugins will send the fuzzed payload to the file forms'
        opt = opt_factory('fuzz_form_files', cf.cf.get('fuzz_form_files'), d,
                          'boolean', tabid='Fuzzer parameters')
        ol.add(opt)

        d = 'Indicates if w3af plugins will send fuzzed filenames in order to'\
            ' find vulnerabilities'
        h = 'For example, if the discovered URL is http://test/filename.php,'\
            ' and fuzz_url_filenames is enabled, w3af will request among'\
            ' other things: http://test/file\'a\'a\'name.php in order to'\
            ' find SQL injections. This type of vulns are getting more '\
            ' common every day!'
        opt = opt_factory(
            'fuzz_url_filenames', cf.cf.get('fuzz_url_filenames'),
            d, 'boolean', help=h, tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'Indicates if w3af plugins will send fuzzed URL parts in order'\
               ' to find vulnerabilities'
        h = 'For example, if the discovered URL is http://test/foo/bar/123,'\
            ' and fuzz_url_parts is enabled, w3af will request among other '\
            ' things: http://test/bar/<script>alert(document.cookie)</script>'\
            ' in order to find XSS.'
        opt = opt_factory('fuzz_url_parts', cf.cf.get('fuzz_url_parts'), desc,
                          'boolean', help=h, tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'Indicates the extension to use when fuzzing file content'
        opt = opt_factory('fuzzed_files_extension',
                          cf.cf.get('fuzzed_files_extension'), desc, 'string',
                          tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'A list with all fuzzable header names'
        opt = opt_factory(
            'fuzzable_headers', cf.cf.get('fuzzable_headers'), desc, 'list',
            tabid='Fuzzer parameters')
        ol.add(opt)

        d = 'Indicates what HTML form combo values w3af plugins will use:'\
            ' all, tb, tmb, t, b'
        h = 'Indicates what HTML form combo values, e.g. select options values,'\
            ' w3af plugins will use: all (All values), tb (only top and bottom '\
            ' values), tmb (top, middle and bottom values), t (top values), b'\
            ' (bottom values).'
        opt = opt_factory(
            'form_fuzzing_mode', cf.cf.get(
                'form_fuzzing_mode'), d, 'string',
            help=h, tabid='Fuzzer parameters')
        ol.add(opt)

        ######## Core parameters ########
        desc = 'Stop scan after first unhandled exception'
        h = 'This feature is only useful for developers that want their scan'\
            ' to stop on the first exception that is raised by a plugin.'\
            'Users should leave this as False in order to get better '\
            'exception handling from w3af\'s core.'
        opt = opt_factory('stop_on_first_exception',
                          cf.cf.get('stop_on_first_exception'),
                          desc, 'boolean', help=h, tabid='Core settings')
        ol.add(opt)

        desc = 'Maximum crawl time (minutes)'
        h = 'Many users tend to enable numerous plugins without actually'\
            ' knowing what they are and the potential time they will take'\
            ' to run. By using this parameter, users will be able to set'\
            ' the maximum amount of time the crawl phase will run.'
        opt = opt_factory('max_discovery_time', cf.cf.get('max_discovery_time'),
                          desc, 'integer', help=h, tabid='Core settings')
        ol.add(opt)

        ######## Network parameters ########
        desc = 'Local interface name to use when sniffing, doing reverse'\
               ' connections, etc.'
        opt = opt_factory('interface', cf.cf.get('interface'), desc,
                          'string', tabid='Network settings')
        ol.add(opt)

        desc = 'Local IP address to use when doing reverse connections'
        opt = opt_factory('local_ip_address', cf.cf.get('local_ip_address'),
                          desc, 'string', tabid='Network settings')
        ol.add(opt)

        ######### Misc ###########
        desc = 'A comma separated list of URLs that w3af should completely ignore'
        h = 'Sometimes it\'s a good idea to ignore some URLs and test them'\
            ' manually'
        opt = opt_factory('non_targets', cf.cf.get('non_targets'), desc,
                          URL_LIST, help=h, tabid='Misc settings')
        ol.add(opt)

        ######### Metasploit ###########
        desc = 'Full path of Metasploit framework binary directory (%s in '\
               'most linux installs)' % cf.cf.get('msf_location')
        opt = opt_factory('msf_location', cf.cf.get('msf_location'),
                          desc, 'string', tabid='Metasploit')
        ol.add(opt)

        return ol

    def get_desc(self):
        return 'This section is used to configure misc settings that affect'\
               ' the core and all plugins.'

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        to_save = ('fuzz_cookies', 'fuzz_form_files', 'fuzz_url_filenames',
                   'fuzz_url_parts', 'fuzzed_files_extension',
                   'form_fuzzing_mode', 'max_discovery_time',
                   'fuzzable_headers', 'interface', 'local_ip_address',
                   'msf_location', 'stop_on_first_exception',
                   'non_targets')
        for name in to_save:
            cf.cf.save(name, options_list[name].get_value())


# This is an undercover call to __init__ :) , so I can set all default parameters.
# TODO: FIXME: This is awful programming.
MiscSettings()
