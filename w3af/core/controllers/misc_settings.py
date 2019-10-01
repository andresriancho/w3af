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
from vulndb import DBVuln

import w3af.core.data.kb.config as cf

from w3af.core.controllers.configurable import Configurable
from w3af.core.controllers.misc.get_local_ip import get_local_ip
from w3af.core.controllers.misc.get_net_iface import get_net_iface
from w3af.core.data.parsers.utils.form_id_matcher_list import FormIDMatcherList
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.db.variant_db import (PATH_MAX_VARIANTS,
                                          PARAMS_MAX_VARIANTS,
                                          MAX_EQUAL_FORM_VARIANTS)
from w3af.core.data.options.option_types import (URL_LIST, COMBO, BOOL, LIST,
                                                 STRING, INT, FORM_ID_LIST)

EXCLUDE = 'exclude'
INCLUDE = 'include'


class MiscSettings(Configurable):
    """
    A class that acts as an interface for the user interfaces, so they can
    configure w3af settings using get_options and SetOptions.
    """

    def __init__(self):
        """
        Set the defaults and save them to the config dict.
        """
        if not self.is_configured():
            # It's the first time I'm run
            self.set_default_values()

    def is_configured(self):
        return cf.cf.get('fuzz_cookies') is not None

    def set_default_values(self):
        """
        Load all the default settings
        :return: None
        """
        cf.cf.save('fuzz_cookies', False)
        cf.cf.save('fuzz_form_files', True)
        cf.cf.save('fuzzed_files_extension', 'gif')
        cf.cf.save('fuzz_url_filenames', False)
        cf.cf.save('fuzz_url_parts', False)
        cf.cf.save('fuzzable_headers', [])

        cf.cf.save('form_fuzzing_mode', 'tmb')

        cf.cf.save('path_max_variants', PATH_MAX_VARIANTS)
        cf.cf.save('params_max_variants', PARAMS_MAX_VARIANTS)
        cf.cf.save('max_equal_form_variants', MAX_EQUAL_FORM_VARIANTS)

        cf.cf.save('max_discovery_time', 120)
        cf.cf.save('max_scan_time', 240)

        cf.cf.save('msf_location', '/opt/metasploit3/bin/')

        #
        # The network interface configuration (for advanced exploits)
        #
        ifname = get_net_iface()
        cf.cf.save('interface', ifname)

        #
        # This doesn't send any packets, and gives you a nice default
        # setting. In most cases, it is the "public" IP address, which will
        # work perfectly in all plugins that need a reverse connection
        # (rfi_proxy)
        #
        local_address = get_local_ip()
        if not local_address:
            local_address = '127.0.0.1'  # do'h!

        cf.cf.save('local_ip_address', local_address)
        cf.cf.save('non_targets', [])
        cf.cf.save('stop_on_first_exception', False)

        # Form exclusion via IDs
        cf.cf.save('form_id_list', FormIDMatcherList('[]'))
        cf.cf.save('form_id_action', EXCLUDE)

        # Language to use when reading from vulndb
        cf.cf.save('vulndb_language', DBVuln.DEFAULT_LANG)

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        #
        # Fuzzer parameters
        #
        d = 'Indicates if w3af plugins will use cookies as a fuzzable parameter'
        opt = opt_factory('fuzz_cookies',
                          cf.cf.get('fuzz_cookies'),
                          d,
                          BOOL,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        d = ('Indicates if w3af plugins will send payloads in the content of'
             ' multipart/post form files.')
        h = ('If enabled, and multipart/post forms with files are found, w3af'
             'will fill those file inputs with pseudo-files containing the'
             'payloads required to identify vulnerabilities.')
        opt = opt_factory('fuzz_form_files',
                          cf.cf.get('fuzz_form_files'),
                          d,
                          BOOL,
                          tabid='Fuzzer parameters',
                          help=h)
        ol.add(opt)

        d = ('Indicates if w3af plugins will send fuzzed file names in order to'
             ' find vulnerabilities')
        h = ('For example, if the discovered URL is http://test/filename.php,'
             ' and fuzz_url_filenames is enabled, w3af will request among'
             ' other things: http://test/file\'a\'a\'name.php in order to'
             ' find SQL injections. This type of vulns are getting more '
             ' common every day!')
        opt = opt_factory('fuzz_url_filenames',
                          cf.cf.get('fuzz_url_filenames'),
                          d,
                          BOOL,
                          help=h,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        desc = ('Indicates if w3af plugins will send fuzzed URL parts in order'
                ' to find vulnerabilities')
        h = ('For example, if the discovered URL is http://test/foo/bar/123,'
             ' and fuzz_url_parts is enabled, w3af will request among other '
             ' things: http://test/bar/<script>alert(document.cookie)</script>'
             ' in order to find XSS.')
        opt = opt_factory('fuzz_url_parts',
                          cf.cf.get('fuzz_url_parts'),
                          desc,
                          BOOL,
                          help=h,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'Indicates the extension to use when fuzzing file content'
        opt = opt_factory('fuzzed_files_extension',
                          cf.cf.get('fuzzed_files_extension'),
                          desc,
                          STRING,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'A list with all fuzzable header names'
        opt = opt_factory('fuzzable_headers',
                          cf.cf.get('fuzzable_headers'),
                          desc,
                          LIST,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        d = ('Indicates what HTML form combo values w3af plugins will use:'
             ' all, tb, tmb, t, b')
        h = ('Indicates what HTML form combo values, e.g. select options values,'
             ' w3af plugins will use: all (All values), tb (only top and bottom'
             ' values), tmb (top, middle and bottom values), t (top values), b'
             ' (bottom values).')
        options = ['tmb', 'all', 'tb', 't', 'b']
        opt = opt_factory('form_fuzzing_mode',
                          options,
                          d,
                          COMBO,
                          help=h,
                          tabid='Fuzzer parameters')
        ol.add(opt)

        #
        # Core parameters
        #
        desc = 'Stop scan after first unhandled exception'
        h = ('This feature is only useful for developers that want their scan'
             ' to stop on the first exception that is raised by a plugin.'
             ' Users should leave this as False in order to get better'
             ' exception handling from w3af\'s core.')
        opt = opt_factory('stop_on_first_exception',
                          cf.cf.get('stop_on_first_exception'),
                          desc,
                          BOOL,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        desc = 'Maximum crawl time (minutes)'
        h = ('Many users tend to enable numerous plugins without actually'
             ' knowing what they are and the potential time they will take'
             ' to run. By using this parameter, users will be able to set'
             ' the maximum amount of time the crawl phase will run.')
        opt = opt_factory('max_discovery_time',
                          cf.cf.get('max_discovery_time'),
                          desc,
                          INT,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        desc = 'Maximum scan time (minutes)'
        h = ('Sets the maximum number of minutes for the scan to run. Use'
             ' zero to remove the limit.')
        opt = opt_factory('max_scan_time',
                          cf.cf.get('max_scan_time'),
                          desc,
                          INT,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        desc = 'Limit requests for each URL sub-path'
        h = ('Limit how many requests are performed for each URL sub-path'
             ' during crawling. For example, if the application links to'
             ' three products: /product/1 /product/2 and /product/3, and'
             ' this variable is set to two, only the first two URLs:'
             ' /product/1 and /product/2 will be crawled.')
        opt = opt_factory('path_max_variants',
                          cf.cf.get('path_max_variants'),
                          desc,
                          INT,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        desc = 'Limit requests for each URL and parameter set'
        h = ('Limit how many requests are performed for each URL and parameter'
             ' set. For example, if the application links to three products:'
             ' /product?id=1 , /product?id=2 and /product?id=3, and this'
             ' variable is set to two, only the first two URLs:'
             ' /product?id=1 and /product?id=2 will crawled.')
        opt = opt_factory('params_max_variants',
                          cf.cf.get('params_max_variants'),
                          desc,
                          INT,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        desc = 'Limit requests for similar forms'
        h = ('Limit the number of HTTP requests to be sent to similar forms'
             ' during crawling. For example, if the application has multiple'
             ' HTML forms with the same parameters and different URLs set in'
             ' actions then only the configured number of forms are crawled.')
        opt = opt_factory('max_equal_form_variants',
                          cf.cf.get('max_equal_form_variants'),
                          desc,
                          INT,
                          help=h,
                          tabid='Core settings')
        ol.add(opt)

        #
        # Network parameters
        #
        desc = ('Local interface name to use when sniffing, doing reverse'
                ' connections, etc.')
        opt = opt_factory('interface',
                          cf.cf.get('interface'),
                          desc,
                          STRING,
                          tabid='Network settings')
        ol.add(opt)

        desc = 'Local IP address to use when doing reverse connections'
        opt = opt_factory('local_ip_address',
                          cf.cf.get('local_ip_address'),
                          desc,
                          STRING,
                          tabid='Network settings')
        ol.add(opt)

        #
        # URL and form exclusions
        #
        desc = 'A comma separated list of URLs that w3af should ignore'
        h = 'No HTTP requests will be sent to these URLs'
        opt = opt_factory('non_targets',
                          cf.cf.get('non_targets'),
                          desc,
                          URL_LIST,
                          help=h,
                          tabid='Exclusions')
        ol.add(opt)

        desc = 'Filter forms to scan using form IDs'
        h = ('Form IDs allow the user to specify which forms will be either'
             ' included of excluded in the scan. The form IDs identified by'
             ' w3af will be written to the log (when verbose is set to true)'
             ' and can be used to define this setting for new scans.\n\n'
             'Find more about form IDs in the "Advanced use cases" section'
             'of the w3af documentation.')
        opt = opt_factory('form_id_list',
                          cf.cf.get('form_id_list'),
                          desc,
                          FORM_ID_LIST,
                          help=h,
                          tabid='Exclusions')
        ol.add(opt)

        desc = 'Define the form_id_list filter behaviour'
        h = ('Change this setting to "include" if only a very specific set of'
             ' forms needs to be scanned. If forms matching the form_id_list'
             ' parameters need to be excluded then set this value to "exclude".')

        form_id_actions = [EXCLUDE, INCLUDE]
        tmp_list = form_id_actions[:]
        tmp_list.remove(cf.cf.get('form_id_action'))
        tmp_list.insert(0, cf.cf.get('form_id_action'))

        opt = opt_factory('form_id_action',
                          tmp_list,
                          desc,
                          COMBO,
                          help=h,
                          tabid='Exclusions')
        ol.add(opt)

        #
        # Metasploit
        #
        desc = ('Full path of Metasploit framework binary directory (%s in '
                'most linux installs)' % cf.cf.get('msf_location'))
        opt = opt_factory('msf_location',
                          cf.cf.get('msf_location'),
                          desc,
                          STRING,
                          tabid='Metasploit')
        ol.add(opt)

        #
        # Language options
        #
        d = 'Set the language to use when reading from the vulnerability database'
        h = ('The vulnerability database stores descriptions, fix guidance, tags,'
             ' references and much more about each vulnerability the scanner can'
             ' identify. The database supports translations, so this information'
             ' can be in many languages. Use this setting to choose the language'
             ' in which the information will be displayed and stored in reports.')
        options = DBVuln.get_all_languages()
        opt = opt_factory('vulndb_language',
                          options,
                          d,
                          COMBO,
                          help=h,
                          tabid='Language')
        ol.add(opt)

        return ol

    def get_desc(self):
        return ('This section is used to configure misc settings that affect'
                ' the core and all plugins.')

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        to_save = ('fuzz_cookies',
                   'fuzz_form_files',
                   'fuzz_url_filenames',
                   'fuzz_url_parts',
                   'fuzzed_files_extension',
                   'form_fuzzing_mode',
                   'max_discovery_time',
                   'max_scan_time',
                   'fuzzable_headers',
                   'interface',
                   'local_ip_address',
                   'msf_location',
                   'stop_on_first_exception',
                   'non_targets',
                   'form_id_action',
                   'form_id_list',
                   'path_max_variants',
                   'params_max_variants',
                   'max_equal_form_variants',
                   'vulndb_language')

        for name in to_save:
            cf.cf.save(name, options_list[name].get_value())


# This is an undercover call to __init__ :) , so I can set all default
# parameters. TODO: FIXME: This is awful programming.
MiscSettings()
