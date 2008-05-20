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

class miscSettings(configurable):
    '''
    A class that acts as an interface for the user interfaces, so they can configure w3af settings using getOptionsXML and SetOptions.
    '''
    
    def __init__( self ):
        # User configured variables
        if cf.cf.getData('showProgressBar') == None:
            # It's the first time I'm runned
            cf.cf.save('fuzzableCookie', False )
            cf.cf.save('fuzzFileContent', True )
            cf.cf.save('fuzzFileName', False )
            cf.cf.save('fuzzFCExt', 'txt' )
            cf.cf.save('autoDependencies', True )
            cf.cf.save('maxDepth', 10 )
            cf.cf.save('maxThreads', 0 )
            cf.cf.save('fuzzableHeaders', [] )
            cf.cf.save('maxDiscoveryLoops', 500 )
            cf.cf.save('interface', 'eth0' )
            cf.cf.save('localAddress', '127.0.0.1' )
            cf.cf.save('demo', False )
            cf.cf.save('showProgressBar', True )
            cf.cf.save('nonTargets', [] )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ######## Fuzzer parameters ########
        d1 = 'Indicates if w3af plugins will use cookies as a fuzzable parameter'
        o1 = option('fuzzCookie', cf.cf.getData('fuzzableCookie'), d1, 'boolean', tabid='Fuzzer parameters')

        d2 = 'Indicates if w3af plugins will send the fuzzed payload to the file forms'
        o2 = option('fuzzFileContent', cf.cf.getData('fuzzFileContent'), d2, 'boolean', tabid='Fuzzer parameters')
        
        d3 = 'Indicates if w3af plugins will send fuzzed filenames in order to find vulnerabilities'
        h3 = 'For example, if the discovered URL is http://test/filename.php, and fuzzFileName is enabled, w3af will request among other things: http://test/file\'a\'a\'name.php in order to find SQL injections. This type of vulns are getting more common every day!'
        o3 = option('fuzzFileName', cf.cf.getData('fuzzFileName'), d3, 'boolean', help=h3, tabid='Fuzzer parameters')
        
        d4 = 'Indicates the extension to use when fuzzing file content'
        o4 = option('fuzzFCExt', cf.cf.getData('fuzzFCExt'), d4, 'string', tabid='Fuzzer parameters')

        d5 = 'A list with all fuzzable header names'
        o5 = option('fuzzableHeaders', cf.cf.getData('fuzzableHeaders'), d5, 'list', tabid='Fuzzer parameters')
        
        ######## Core parameters ########
        d6 = 'Automatic dependency enabling for plugins'
        h6 = 'If autoDependencies is enabled, and pluginA depends on pluginB that wasn\'t enabled, then pluginB is automatically enabled.'
        o6 = option('autoDependencies', cf.cf.getData('autoDependencies'), d6, 'boolean', help=h6, tabid='Core settings')

        d7 = 'Maximum depth of the discovery phase'
        h7 = 'For example, if set to 10, the webSpider plugin will only follow 10 link levels while spidering the site. This applies to the whole discovery phase; not only to the webSpider.'
        o7 = option('maxDepth', cf.cf.getData('maxDepth'), d7, 'integer', help=h7, tabid='Core settings')
        
        d8 = 'Maximum number of threads that the w3af process will spawn'
        o8 = option('maxThreads', cf.cf.getData('maxThreads'), d8, 'integer', tabid='Core settings')
        
        d9 = 'Maximum number of times the discovery function is called'
        o9 = option('maxDiscoveryLoops', cf.cf.getData('maxDiscoveryLoops'), d9, 'integer', tabid='Core settings')
        
        ######## Network parameters ########
        d10 = 'Local interface name to use when sniffing, doing reverse connections, etc.'
        o10 = option('interface', cf.cf.getData('interface'), d10, 'string', tabid='Network settings')

        d11 = 'Local IP address to use when doing reverse connections'
        o11 = option('localAddress', cf.cf.getData('localAddress'), d11, 'string', tabid='Core settings')
        
        ######### Misc ###########
        d12 = 'Enable this when you are doing a demo in a conference'
        o12 = option('demo', cf.cf.getData('demo'), d12, 'boolean', tabid='Misc settings')
        
        d13 = 'Enables or disables the progress bar that is shown by audit plugins'
        o13 = option('showProgressBar', cf.cf.getData('showProgressBar'), d13, 'boolean', tabid='Misc settings')
        
        d14 = 'A comma separated list of URLs that w3af should completely ignore'
        h14 = 'Sometimes it\'s a good idea to ignore some URLs and test them manually'
        o14 = option('nonTarget', cf.cf.getData('nonTarget'), d14, 'list', tabid='Misc settings')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        ol.add(o5)
        ol.add(o6)
        ol.add(o7)
        ol.add(o8)
        ol.add(o9)
        ol.add(o10)
        ol.add(o11)
        ol.add(o12)
        ol.add(o13)
        ol.add(o14)
        return ol
    
    def getDesc( self ):
        return 'This section is used to configure misc settings that affect the core and all plugins.'
    
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        cf.cf.save('fuzzableCookie', optionsMap['fuzzCookie'].getValue() )
        cf.cf.save('fuzzFileContent', optionsMap['fuzzFileContent'].getValue() )
        cf.cf.save('fuzzFileName', optionsMap['fuzzFileName'].getValue() )
        cf.cf.save('fuzzFCExt', optionsMap['fuzzFCExt'].getValue() )
        cf.cf.save('autoDependencies', optionsMap['autoDependencies'].getValue() )
        cf.cf.save('maxDepth', optionsMap['maxDepth'].getValue() )
        cf.cf.save('maxThreads', optionsMap['maxThreads'].getValue() )
        cf.cf.save('fuzzableHeaders', optionsMap['fuzzableHeaders'].getValue() )
        cf.cf.save('maxDiscoveryLoops', optionsMap['maxDiscoveryLoops'].getValue() )
        cf.cf.save('interface', optionsMap['interface'].getValue() )
        cf.cf.save('localAddress', optionsMap['localAddress'].getValue() )
        cf.cf.save('demo', optionsMap['demo'].getValue()  )
        cf.cf.save('showProgressBar', optionsMap['showProgressBar'].getValue()  )
        cf.cf.save('nonTargets', optionsMap['nonTarget'].getValue() )
        
# This is an undercover call to __init__ :) , so I can set all default parameters.
miscSettings()
