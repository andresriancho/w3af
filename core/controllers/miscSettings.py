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

from core.controllers.configurable import configurable
import core.data.kb.config as cf

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.data.parsers.urlParser import url_object

# Raise errors
from core.controllers.w3afException import w3afException

from core.controllers.misc.get_local_ip import get_local_ip
from core.controllers.misc.get_net_iface import get_net_iface


class miscSettings(configurable):
    '''
    A class that acts as an interface for the user interfaces, so they can configure w3af 
    settings using getOptions and SetOptions.
    '''
    
    def __init__( self ):
        '''
        Set the defaults and save them to the config dict.
        '''
        #
        # User configured variables
        #
        if cf.cf.getData('autoDependencies') is None:
            # It's the first time I'm run
            cf.cf.save('fuzzableCookie', False )
            cf.cf.save('fuzzFileContent', True )
            cf.cf.save('fuzzFileName', False )
            cf.cf.save('fuzzURLParts', False )
            cf.cf.save('fuzzFCExt', 'txt' )
            cf.cf.save('fuzzFormComboValues', 'tmb')
            cf.cf.save('autoDependencies', True )
            cf.cf.save('maxDiscoveryTime', 120 )
            cf.cf.save('fuzzableHeaders', [] )
            cf.cf.save('msf_location', '/opt/metasploit3/bin/' )
            
            #
            #
            #
            ifname = get_net_iface()
            cf.cf.save('interface', ifname )
            
            #
            #   This doesn't send any packets, and gives you a nice default setting.
            #   In most cases, it is the "public" IP address, which will work perfectly
            #   in all plugins that need a reverse connection (rfiProxy)
            #
            local_address = get_local_ip()
            if not local_address:
                local_address = '127.0.0.1' #do'h!                
        
            cf.cf.save('localAddress', local_address)
            cf.cf.save('demo', False )
            cf.cf.save('nonTargets', [] )
            cf.cf.save('stop_on_first_exception', False )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()

        ######## Fuzzer parameters ########
        desc = 'Indicates if w3af plugins will use cookies as a fuzzable parameter'
        opt = option('fuzzCookie', cf.cf.getData('fuzzableCookie'), desc, 'boolean',
                     tabid='Fuzzer parameters')
        ol.add(opt)

        desc = 'Indicates if w3af plugins will send the fuzzed payload to the file forms'
        opt = option('fuzzFileContent', cf.cf.getData('fuzzFileContent'), desc, 'boolean',
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates if w3af plugins will send fuzzed filenames in order to find vulnerabilities'
        help = 'For example, if the discovered URL is http://test/filename.php, and fuzzFileName'
        help += ' is enabled, w3af will request among other things: http://test/file\'a\'a\'name.php'
        help += ' in order to find SQL injections. This type of vulns are getting more common every'
        help += ' day!'
        opt = option('fuzzFileName', cf.cf.getData('fuzzFileName'), desc, 'boolean', help=help, 
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates if w3af plugins will send fuzzed URL parts in order to find vulnerabilities'
        help = 'For example, if the discovered URL is http://test/foo/bar/123, and fuzzURLParts'
        help += ' is enabled, w3af will request among other things: '
        help += 'http://test/foo/bar/<script>alert(document.cookie)</script> in order to find XSS.'
        opt = option('fuzzURLParts', cf.cf.getData('fuzzURLParts'), desc, 'boolean', help=help, 
                     tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates the extension to use when fuzzing file content'
        opt = option('fuzzFCExt', cf.cf.getData('fuzzFCExt'), desc, 'string', tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'A list with all fuzzable header names'
        opt = option('fuzzableHeaders', cf.cf.getData('fuzzableHeaders'), desc, 'list',
                            tabid='Fuzzer parameters')
        ol.add(opt)
        
        desc = 'Indicates what HTML form combo values w3af plugins will use: all, tb, tmb, t, b'
        help = 'Indicates what HTML form combo values, e.g. select options values,  w3af plugins will'
        help += ' use: all (All values), tb (only top and bottom values), tmb (top, middle and bottom'
        help += ' values), t (top values), b (bottom values)'
        opt = option('fuzzFormComboValues', cf.cf.getData('fuzzFormComboValues'), desc, 'string',
                     help=help, tabid='Fuzzer parameters')
        ol.add(opt)
        
        ######## Core parameters ########
        desc = 'Automatic dependency enabling for plugins'
        help = 'If autoDependencies is enabled, and pluginA depends on pluginB that wasn\'t enabled,'
        help += ' then pluginB is automatically enabled.'
        opt = option('autoDependencies', cf.cf.getData('autoDependencies'), desc, 'boolean',
                    help=help, tabid='Core settings')
        ol.add(opt)
        
        desc = 'Stop scan after first unhandled exception'
        help =  'This feature is only useful for developers that want their scan'
        help += ' to stop on the first exception that is raised by a plugin.'
        help += 'Users should leave this as False in order to get better '
        help += 'exception handling from w3af\'s core.'
        opt = option('stop_on_first_exception', cf.cf.getData('stop_on_first_exception'), 
                     desc, 'boolean', help=help, tabid='Core settings')
        ol.add(opt)

        desc = 'Maximum discovery time (minutes)'
        help = 'Many users tend to enable numerous plugins without actually knowing what they are'
        help += ' and the potential time they will take to run. By using this parameter, users will'
        help += ' be able to set the maximum amount of time the discovery phase will run.'
        opt = option('maxDiscoveryTime', cf.cf.getData('maxDiscoveryTime'), desc, 'integer', 
                     help=help, tabid='Core settings')
        ol.add(opt)
                
        ######## Network parameters ########
        desc = 'Local interface name to use when sniffing, doing reverse connections, etc.'
        opt = option('interface', cf.cf.getData('interface'), desc, 'string', tabid='Network settings')
        ol.add(opt)
        
        desc = 'Local IP address to use when doing reverse connections'
        opt = option('localAddress', cf.cf.getData('localAddress'), desc, 'string',
                     tabid='Network settings')
        ol.add(opt)
                
        ######### Misc ###########
        desc = 'Enable this when you are doing a demo in a conference'
        help = 'Delays HTTP requests in sqlmap plugin.'
        opt = option('demo', cf.cf.getData('demo'), desc, 'boolean', tabid='Misc settings')
        ol.add(opt)
                
        desc = 'A comma separated list of URLs that w3af should completely ignore'
        help = 'Sometimes it\'s a good idea to ignore some URLs and test them manually'
        opt = option('nonTargets', cf.cf.getData('nonTargets'), desc, 'list', help=help, 
                     tabid='Misc settings')
        ol.add(opt)
                
        ######### Metasploit ###########
        desc = 'Full path of Metasploit framework binary directory (%s in most linux installs)' % cf.cf.getData('msf_location')
        opt = option('msf_location', cf.cf.getData('msf_location'), desc, 'string', tabid='Metasploit')
        ol.add(opt)
                
        return ol
    
    def getDesc( self ):
        return 'This section is used to configure misc settings that affect the core and all plugins.'
    
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        cf.cf.save('fuzzableCookie', optionsMap['fuzzCookie'].getValue() )
        cf.cf.save('fuzzFileContent', optionsMap['fuzzFileContent'].getValue() )
        cf.cf.save('fuzzFileName', optionsMap['fuzzFileName'].getValue() )
        cf.cf.save('fuzzURLParts', optionsMap['fuzzURLParts'].getValue() )
        cf.cf.save('fuzzFCExt', optionsMap['fuzzFCExt'].getValue() )
        cf.cf.save('fuzzFormComboValues', optionsMap['fuzzFormComboValues'].getValue() )
        cf.cf.save('autoDependencies', optionsMap['autoDependencies'].getValue() )
        cf.cf.save('maxDiscoveryTime', optionsMap['maxDiscoveryTime'].getValue() )
        
        cf.cf.save('fuzzableHeaders', optionsMap['fuzzableHeaders'].getValue() )
        cf.cf.save('interface', optionsMap['interface'].getValue() )
        cf.cf.save('localAddress', optionsMap['localAddress'].getValue() )
        cf.cf.save('demo', optionsMap['demo'].getValue()  )
        
        url_list = []
        for url_str in optionsMap['nonTargets'].getValue():
            url_list.append( url_object( url_str ) )
        cf.cf.save('nonTargets', url_list )
        
        cf.cf.save('msf_location', optionsMap['msf_location'].getValue() )
        cf.cf.save('stop_on_first_exception', 
                   optionsMap['stop_on_first_exception'].getValue() )
        
# This is an undercover call to __init__ :) , so I can set all default parameters.
miscSettings()
