'''
miscSettings.py

Copyright 2006 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''
import core.data.kb.config as cf

from core.controllers.configurable import configurable
from core.controllers.misc.get_local_ip import get_local_ip
from core.controllers.misc.get_net_iface import get_net_iface
from core.data.options.opt_factory import opt_factory
from core.data.options.option_list import OptionList
from core.data.parsers.url import URL


class miscSettings(configurable):
    '''
    A class that acts as an interface for the user interfaces, so they can
    configure w3af settings using get_options and SetOptions.
    '''
    
    def __init__( self ):
        '''
        Set the defaults and save them to the config dict.
        '''
        #
        # User configured variables
        #
        if cf.cf.get('fuzzableCookie') is None:
            # It's the first time I'm run
            cf.cf.save('fuzzableCookie', False )
            cf.cf.save('fuzzFileContent', True )
            cf.cf.save('fuzzFileName', False )
            cf.cf.save('fuzzURLParts', False )
            cf.cf.save('fuzzFCExt', 'txt' )
            cf.cf.save('fuzzFormComboValues', 'tmb')
            cf.cf.save('maxDiscoveryTime', 120 )
            cf.cf.save('fuzzable_headers', [] )
            cf.cf.save('msf_location', '/opt/metasploit3/bin/' )
            
            #
            #
            #
            ifname = get_net_iface()
            cf.cf.save('interface', ifname )
            
            #
            #   This doesn't send any packets, and gives you a nice default setting.
            #   In most cases, it is the "public" IP address, which will work perfectly
            #   in all plugins that need a reverse connection (rfi_proxy)
            #
            local_address = get_local_ip()
            if not local_address:
                local_address = '127.0.0.1' #do'h!                
        
            cf.cf.save('localAddress', local_address)
            cf.cf.save('demo', False )
            cf.cf.save('nonTargets', [] )
            cf.cf.save('stop_on_first_exception', False )
    
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()

        ######## Fuzzer parameters ########
        desc = 'Indicates if w3af plugins will use cookies as a fuzzable parameter'
        opt = opt_factory('fuzzCookie', cf.cf.get('fuzzableCookie'), desc, 'boolean',
                     tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'Indicates if w3af plugins will send the fuzzed payload to the file forms'
        opt = opt_factory('fuzzFileContent', cf.cf.get('fuzzFileContent'), desc, 'boolean',
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates if w3af plugins will send fuzzed filenames in order to find vulnerabilities'
        help = 'For example, if the discovered URL is http://test/filename.php, and fuzzFileName'
        help += ' is enabled, w3af will request among other things: http://test/file\'a\'a\'name.php'
        help += ' in order to find SQL injections. This type of vulns are getting more common every'
        help += ' day!'
        opt = opt_factory('fuzzFileName', cf.cf.get('fuzzFileName'), desc, 'boolean', help=help, 
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates if w3af plugins will send fuzzed URL parts in order to find vulnerabilities'
        help = 'For example, if the discovered URL is http://test/foo/bar/123, and fuzzURLParts'
        help += ' is enabled, w3af will request among other things: '
        help += 'http://test/foo/bar/<script>alert(document.cookie)</script> in order to find XSS.'
        opt = opt_factory('fuzzURLParts', cf.cf.get('fuzzURLParts'), desc, 'boolean', help=help, 
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates the extension to use when fuzzing file content'
        opt = opt_factory('fuzzFCExt', cf.cf.get('fuzzFCExt'), desc, 'string', tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'A list with all fuzzable header names'
        opt = opt_factory('fuzzable_headers', cf.cf.get('fuzzable_headers'), desc, 'list',
                            tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates what HTML form combo values w3af plugins will use: all, tb, tmb, t, b'
        help = 'Indicates what HTML form combo values, e.g. select options values,  w3af plugins will'
        help += ' use: all (All values), tb (only top and bottom values), tmb (top, middle and bottom'
        help += ' values), t (top values), b (bottom values)'
        opt = opt_factory('fuzzFormComboValues', cf.cf.get('fuzzFormComboValues'), desc, 'string',
                     help=help, tabid='Fuzzer parameters')
        ol.add(opt)
        
        ######## Core parameters ########
        desc = 'Stop scan after first unhandled exception'
        help =  'This feature is only useful for developers that want their scan'
        help += ' to stop on the first exception that is raised by a plugin.'
        help += 'Users should leave this as False in order to get better '
        help += 'exception handling from w3af\'s core.'
        opt = opt_factory('stop_on_first_exception', cf.cf.get('stop_on_first_exception'), 
                     desc, 'boolean', help=help, tabid='Core settings')
        ol.add(opt)

        desc = 'Maximum crawl time (minutes)'
        help = 'Many users tend to enable numerous plugins without actually knowing what they are'
        help += ' and the potential time they will take to run. By using this parameter, users will'
        help += ' be able to set the maximum amount of time the crawl phase will run.'
        opt = opt_factory('maxDiscoveryTime', cf.cf.get('maxDiscoveryTime'), desc, 'integer', 
                     help=help, tabid='Core settings')
        ol.add(opt)
                
        ######## Network parameters ########
        desc = 'Local interface name to use when sniffing, doing reverse connections, etc.'
        opt = opt_factory('interface', cf.cf.get('interface'), desc, 'string', tabid='Network settings')
        ol.add(opt)
        
        desc = 'Local IP address to use when doing reverse connections'
        opt = opt_factory('localAddress', cf.cf.get('localAddress'), desc, 'string',
                     tabid='Network settings')
        ol.add(opt)
                
        ######### Misc ###########
        desc = 'Enable this when you are doing a demo in a conference'
        help = 'Delays HTTP requests in sqlmap plugin.'
        opt = opt_factory('demo', cf.cf.get('demo'), desc, 'boolean', tabid='Misc settings')
        ol.add(opt)
                
        desc = 'A comma separated list of URLs that w3af should completely ignore'
        help = 'Sometimes it\'s a good idea to ignore some URLs and test them manually'
        opt = opt_factory('nonTargets', cf.cf.get('nonTargets'), desc, 'list', help=help, 
                     tabid='Misc settings')
        ol.add(opt)
                
        ######### Metasploit ###########
        desc = 'Full path of Metasploit framework binary directory (%s in most linux installs)' % cf.cf.get('msf_location')
        opt = opt_factory('msf_location', cf.cf.get('msf_location'), desc, 'string', tabid='Metasploit')
        ol.add(opt)
                
        return ol
    
    def get_desc( self ):
        return 'This section is used to configure misc settings that affect the core and all plugins.'
    
    def set_options( self, options_list ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter options_list: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        cf.cf.save('fuzzableCookie', options_list['fuzzCookie'].get_value() )
        cf.cf.save('fuzzFileContent', options_list['fuzzFileContent'].get_value() )
        cf.cf.save('fuzzFileName', options_list['fuzzFileName'].get_value() )
        cf.cf.save('fuzzURLParts', options_list['fuzzURLParts'].get_value() )
        cf.cf.save('fuzzFCExt', options_list['fuzzFCExt'].get_value() )
        cf.cf.save('fuzzFormComboValues', options_list['fuzzFormComboValues'].get_value() )
        cf.cf.save('maxDiscoveryTime', options_list['maxDiscoveryTime'].get_value() )
        
        cf.cf.save('fuzzable_headers', options_list['fuzzable_headers'].get_value() )
        cf.cf.save('interface', options_list['interface'].get_value() )
        cf.cf.save('localAddress', options_list['localAddress'].get_value() )
        cf.cf.save('demo', options_list['demo'].get_value()  )
        
        url_list = []
        for url_str in options_list['nonTargets'].get_value():
            url_list.append( URL( url_str ) )
        cf.cf.save('nonTargets', url_list )
        
        cf.cf.save('msf_location', options_list['msf_location'].get_value() )
        cf.cf.save('stop_on_first_exception', 
                   options_list['stop_on_first_exception'].get_value() )
        
# This is an undercover call to __init__ :) , so I can set all default parameters.
miscSettings()
