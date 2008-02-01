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
from core.controllers.misc.parseOptions import parseOptions

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
            
            cf.cf.save('404exceptions', []  )
            cf.cf.save('always404', [] )
            
        
    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="fuzzCookie">\
                <default>'+str(cf.cf.getData('fuzzableCookie'))+'</default>\
                <desc>Indicates if w3af plugins will use cookies as a fuzzable parameter</desc>\
                <type>boolean</type>\
                <tabid>Fuzzable parameters</tabid>\
            </Option>\
            <Option name="fuzzFileContent">\
                <default>'+str(cf.cf.getData('fuzzFileContent'))+'</default>\
                <desc>Indicates if w3af plugins will send the fuzzed payload to the file forms</desc>\
                <type>boolean</type>\
                <tabid>Fuzzable parameters</tabid>\
            </Option>\
            <Option name="fuzzFileName">\
                <default>'+str(cf.cf.getData('fuzzFileName'))+'</default>\
                <desc>Indicates if w3af plugins will send fuzzed filenames in order to find vulnerabilities</desc>\
                <help>For example, if the discovered URL is http://test/filename.php, and fuzzFileName is enabled, w3af will request among other\
                things: http://test/file\'a\'a\'name.php in order to find SQL injections. This type of vulns are getting more common every day!</help>\
                <type>boolean</type>\
                <tabid>Fuzzable parameters</tabid>\
            </Option>\
            <Option name="fuzzFCExt">\
                <default>'+str(cf.cf.getData('fuzzFCExt'))+'</default>\
                <desc>Indicates the extension to use when fuzzing file content</desc>\
                <type>string</type>\
                <tabid>Fuzzable parameters</tabid>\
            </Option>\
            <Option name="fuzzableHeaders">\
                <default>'+','.join(cf.cf.getData('fuzzableHeaders'))+'</default>\
                <desc>A list with all fuzzable header names</desc>\
                <type>list</type>\
                <tabid>Fuzzable parameters</tabid>\
            </Option>\
            <Option name="autoDependencies">\
                <default>'+str(cf.cf.getData('autoDependencies'))+'</default>\
                <desc>Automatic dependency enabling for plugins</desc>\
                <type>boolean</type>\
                <tabid>Core settings</tabid>\
            </Option>\
            <Option name="maxDepth">\
                <default>'+str(cf.cf.getData('maxDepth'))+'</default>\
                <desc>Maximum depth of the discovery phase</desc>\
                <help>For example, if set to 10, the webSpider plugin will only follow 10 links while spidering the site</help>\
                <type>integer</type>\
                <tabid>Core settings</tabid>\
            </Option>\
            <Option name="maxThreads">\
                <default>'+str(cf.cf.getData('maxThreads'))+'</default>\
                <desc>Maximum number of threads that the w3af process will spawn</desc>\
                <type>integer</type>\
                <tabid>Core settings</tabid>\
            </Option>\
            <Option name="maxDiscoveryLoops">\
                <default>'+str(cf.cf.getData('maxDiscoveryLoops'))+'</default>\
                <desc>Maximum number of times the discovery function is called</desc>\
                <type>integer</type>\
                <tabid>Core settings</tabid>\
            </Option>\
            <Option name="interface">\
                <default>'+str(cf.cf.getData('interface'))+'</default>\
                <desc>Local interface name to use when sniffing, doing reverse connections, etc</desc>\
                <type>string</type>\
                <tabid>Network settings</tabid>\
            </Option>\
            <Option name="localAddress">\
                <default>'+str(cf.cf.getData('localAddress'))+'</default>\
                <desc>Local IP address to use when doing reverse connections</desc>\
                <type>string</type>\
                <tabid>Network settings</tabid>\
            </Option>\
            <Option name="demo">\
                <default>'+str(cf.cf.getData('demo'))+'</default>\
                <desc>Enable this when you are doing a demo in a conference</desc>\
                <type>boolean</type>\
                <tabid>Misc settings</tabid>\
            </Option>\
            <Option name="showProgressBar">\
                <default>'+str(cf.cf.getData('showProgressBar'))+'</default>\
                <desc>Enables or disables the progress bar that is shown by audit plugins</desc>\
                <type>boolean</type>\
                <tabid>Misc settings</tabid>\
            </Option>\
            <Option name="nonTarget">\
                <default>'+','.join(cf.cf.getData('nonTargets'))+'</default>\
                <desc>A comma separated list of URLs that w3af should completely ignore</desc>\
                <help>Sometimes it\'s a good idea to ignore some URLs and test them manually</help>\
                <type>list</type>\
                <tabid>Misc settings</tabid>\
            </Option>\
            <Option name="404exceptions">\
                <default>'+','.join(cf.cf.getData('404exceptions'))+'</default>\
                <desc>A comma separated list that determines what URLs will NEVER be detected as 404 pages.</desc>\
                <type>list</type>\
                <tabid>404 settings</tabid>\
            </Option>\
            <Option name="always404">\
                <default>'+','.join(cf.cf.getData('always404'))+'</default>\
                <desc>A comma separated list that determines what URLs will ALWAYS be detected as 404 pages.</desc>\
                <type>list</type>\
                <tabid>404 settings</tabid>\
            </Option>\
        </OptionList>\
        '
    
    def getDesc( self ):
        return 'This section is used to configure misc settings that affect the core and all plugins.'
    
    def setOptions( self, OptionMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        f00, OptionMap = parseOptions( 'misc-settings', OptionMap )
        cf.cf.save('fuzzableCookie', OptionMap['fuzzCookie'] )
        cf.cf.save('fuzzFileContent', OptionMap['fuzzFileContent'] )
        cf.cf.save('fuzzFileName', OptionMap['fuzzFileName'] )
        cf.cf.save('fuzzFCExt', OptionMap['fuzzFCExt'] )
        cf.cf.save('autoDependencies', OptionMap['autoDependencies'] )
        cf.cf.save('maxDepth', OptionMap['maxDepth'] )
        cf.cf.save('maxThreads', OptionMap['maxThreads'] )
        cf.cf.save('fuzzableHeaders', OptionMap['fuzzableHeaders'] )
        cf.cf.save('maxDiscoveryLoops', OptionMap['maxDiscoveryLoops'] )
        cf.cf.save('interface', OptionMap['interface'] )
        cf.cf.save('localAddress', OptionMap['localAddress'] )
        cf.cf.save('demo', OptionMap['demo']  )
        cf.cf.save('showProgressBar', OptionMap['showProgressBar']  )
        cf.cf.save('nonTargets', OptionMap['nonTarget'] )
        cf.cf.save('404exceptions', OptionMap['404exceptions']  )
        cf.cf.save('always404', OptionMap['always404'] )
        
# This is an undercover call to __init__ :) , so I can set all default parameters.
miscSettings()
