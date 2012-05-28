'''
w3af_core_target.py

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
import time
import urllib2

from core.controllers.configurable import configurable
import core.data.kb.config as cf

from core.data.parsers.urlParser import url_object
from core.controllers.w3afException import w3afException

# options
from core.data.options.option import option
from core.data.options.comboOption import comboOption
from core.data.options.optionList import optionList

cf.cf.save('targets', [] )
cf.cf.save('targetDomains', [] )
cf.cf.save('baseURLs', [] )


class w3af_core_target(configurable):
    '''
    A class that acts as an interface for the user interfaces, so they can configure the target
    settings using getOptions and SetOptions.
    '''
    
    def __init__( self ):
        # Set defaults for user configured variables
        self.clear()
        
        # Some internal variables
        self._operatingSystems = ['unknown','unix','windows']
        self._programmingFrameworks = ['unknown', 'php','asp','asp.net','java','jsp','cfm','ruby','perl']

    def clear(self):
        cf.cf.save('targets', [] )
        cf.cf.save('targetOS', 'unknown' )
        cf.cf.save('targetFramework', 'unknown' )
        cf.cf.save('targetDomains', [] )
        cf.cf.save('baseURLs', [] )
        cf.cf.save('sessionName', 'defaultSession' + '-' + time.strftime('%Y-%b-%d_%H-%M-%S') )
                
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''        
        d1 = 'A comma separated list of URLs'
        o1 = option('target', ','.join(str(tar) for tar in 
                                       cf.cf.getData('targets')), d1, 'list')
        
        d2 = 'Target operating system ('+ '/'.join(self._operatingSystems) +')'
        h2 = 'This setting is here to enhance w3af performance.'
        # This list "hack" has to be done becase the default value is the one
        # in the first position on the list
        tmpList = self._operatingSystems[:]
        tmpList.remove( cf.cf.getData('targetOS') )
        tmpList.insert(0, cf.cf.getData('targetOS') )
        o2 = comboOption('targetOS', tmpList, d2, 'combo', help=h2)

        d3 = 'Target programming framework ('+ '/'.join(self._programmingFrameworks) +')'
        h3 = 'This setting is here to enhance w3af performance.'
        # This list "hack" has to be done becase the default value is the one
        # in the first position on the list
        tmpList = self._programmingFrameworks[:]
        tmpList.remove( cf.cf.getData('targetFramework') )
        tmpList.insert(0, cf.cf.getData('targetFramework') )
        o3 = comboOption('targetFramework', tmpList, d3, 'combo', help=h3)
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol
    
    def _verifyURL(self, target_url, fileTarget=True):
        '''
        Verify if the URL is valid and raise an exception if w3af doesn't
        support it.
        
        >>> ts = w3af_core_target()        
        >>> ts._verifyURL('ftp://www.google.com/')
        Traceback (most recent call last):
          ...
        w3afException: Invalid format for target URL "ftp://www.google.com/", you have to specify the protocol (http/https/file) and a domain or IP address. Examples: http://host.tld/ ; https://127.0.0.1/ .
        >>> ts._verifyURL('http://www.google.com/')
        >>> ts._verifyURL('http://www.google.com:39/') is None
        True
        
        @param target_url: The target URL object to check if its valid or not.
        @return: None. A w3afException is raised on error.
        '''
        try:
            target_url = url_object(target_url)
        except ValueError:
            is_invalid = True
        else:
            protocol = target_url.getProtocol()
            aFile = fileTarget and protocol == 'file' and \
                                                target_url.getDomain() or ''
            aHTTP = protocol in ('http', 'https') and \
                                                target_url.is_valid_domain()
            is_invalid = not (aFile or aHTTP)

        if is_invalid:
            msg = ('Invalid format for target URL "%s", you have to specify '
            'the protocol (http/https/file) and a domain or IP address. '
            'Examples: http://host.tld/ ; https://127.0.0.1/ .' % target_url)
            raise w3afException(msg)
    
    def setOptions(self, optionsMap):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        '''
        target_urls_strings = optionsMap['target'].getValue() or []

        for target_url_string in target_urls_strings:
            
            self._verifyURL(target_url_string)
            
            if target_url_string.count('file://'):
                try:
                    f = urllib2.urlopen(target_url_string)
                except:
                    raise w3afException(
                        'Cannot open target file: "%s"' % target_url_string)
                else:
                    for line in f:
                        target_in_file = line.strip()
                        self._verifyURL(target_in_file, fileTarget=False)
                        target_urls_strings.append(target_in_file)
                    f.close()
                target_urls_strings.remove( target_url_string )
        
        # Convert to objects
        target_url_objects = [url_object(u) for u in target_urls_strings]
        
        # Now we perform a check to see if the user has specified more than one target
        # domain, for example: "http://google.com, http://yahoo.com".
        domain_list = [target_url.getNetLocation() for target_url in target_url_objects]
        domain_list = list( set(domain_list) )
        if len( domain_list ) > 1:
            msg = 'You specified more than one target domain: ' + ','.join(domain_list)
            msg += ' . And w3af only supports one target domain at the time.'
            raise w3afException(msg)
        
        # Save in the config, the target URLs, this may be usefull for some plugins.
        cf.cf.save('targets', target_url_objects)
        cf.cf.save('targetDomains', [ i.getDomain() for i in target_url_objects ] )
        cf.cf.save('baseURLs', [ i.baseUrl() for i in target_url_objects ] )
        
        if target_url_objects:
            sessName = [ x.getNetLocation() for x in target_url_objects ]
            sessName = '-'.join(sessName)
        else:
            sessName = 'noTarget'

        cf.cf.save('sessionName', sessName + '-' + time.strftime('%Y-%b-%d_%H-%M-%S') )
        
        # Advanced target selection
        os = optionsMap['targetOS'].getValueStr()
        if os.lower() in self._operatingSystems:
            cf.cf.save('targetOS', os.lower() )
        else:
            raise w3afException('Unknown target operating system: ' + os)
        
        pf = optionsMap['targetFramework'].getValueStr()
        if pf.lower() in self._programmingFrameworks:
            cf.cf.save('targetFramework', pf.lower() )
        else:
            raise w3afException('Unknown target programming framework: ' + pf)

    def getName( self ):
        return 'targetSettings'
        
    def getDesc( self ):
        return 'Configure target URLs'
