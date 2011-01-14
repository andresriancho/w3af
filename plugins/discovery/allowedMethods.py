'''
allowedMethods.py

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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.bloomfilter.pybloom import ScalableBloomFilter

from core.controllers.w3afException import w3afRunOnce
import core.data.constants.httpConstants as httpConstants
from core.controllers.misc.groupbyMinKey import groupbyMinKey


class allowedMethods(baseDiscoveryPlugin):
    '''
    Enumerate the allowed methods of an URL.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)

        # Internal variables
        self._exec = True
        self._already_tested = ScalableBloomFilter()
        self._bad_codes = [ httpConstants.UNAUTHORIZED, httpConstants.NOT_IMPLEMENTED,
                                    httpConstants.METHOD_NOT_ALLOWED, httpConstants.FORBIDDEN]
        
        # Methods
        self._dav_methods = [ 'DELETE', 'PROPFIND', 'PROPPATCH', 'COPY', 'MOVE', 'LOCK', 
                                        'UNLOCK', 'MKCOL']
        self._common_methods = [ 'OPTIONS', 'GET', 'HEAD', 'POST', 'TRACE', 'PUT']
        self._uncommon_methods = ['*', 'SUBSCRIPTIONS', 'NOTIFY', 'DEBUG', 'TRACK', 'POLL', 'PIN', 
                                                    'INVOKE', 'SUBSCRIBE', 'UNSUBSCRIBE']
        
        # Methods taken from http://www.w3.org/Protocols/HTTP/Methods.html 
        self._proposed_methods = [ 'CHECKOUT', 'SHOWMETHOD', 'LINK', 'UNLINK', 'CHECKIN', 
                                                'TEXTSEARCH', 'SPACEJUMP', 'SEARCH', 'REPLY']
        self._extra_methods = [ 'CONNECT', 'RMDIR', 'MKDIR', 'REPORT', 'ACL', 'DELETE', 'INDEX', 
                                        'LABEL', 'INVALID']
        self._version_control = [ 'VERSION_CONTROL', 'CHECKIN', 'UNCHECKOUT', 'PATCH', 'MERGE', 
                                            'MKWORKSPACE', 'MKACTIVITY', 'BASELINE_CONTROL']       
        
        self._supported_methods = self._dav_methods  + self._common_methods + self._uncommon_methods
        self._supported_methods += self._proposed_methods + self._extra_methods
        self._supported_methods += self._version_control

 
        # User configured variables
        self._exec_one_time = True
        self._report_dav_only = True
        
    def discover(self, fuzzableRequest ):
        '''
        Uses several technics to try to find out what methods are allowed for an URL.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            # Run the plugin.
            if self._exec_one_time:
                self._exec = False
            
            domain_path = fuzzableRequest.getURL().getDomainPath()
            if domain_path not in self._already_tested:
                self._already_tested.add( domain_path )
                self._check_methods( domain_path )
        return []
    
    def _check_methods( self, url ):
        '''
        Find out what methods are allowed.
        @parameter url: Where to check.
        '''
        allowed_methods = []
        with_options = False
        id_list = []
        
        # First, try to check available methods using OPTIONS, if OPTIONS isn't 
        # enabled, do it manually
        res = self._urlOpener.OPTIONS( url )
        headers = res.getLowerCaseHeaders()
        for header_name in ['allow', 'public']:
            if header_name in headers:
                allowed_methods.extend( headers[header_name].split(',') )
                allowed_methods = [ x.strip() for x in allowed_methods ]
                with_options = True
                allowed_methods = list(set(allowed_methods))

        # Save the ID for later
        if with_options:
            id_list.append( res.id )

        else:
            #
            #   Before doing anything else, I'll send a request with a non-existant method
            #   If that request succeds, then all will...
            #
            try:
                non_exist_response = self._urlOpener.ARGENTINA( url )
                get_response = self._urlOpener.GET( url )
            except:
                pass
            else:
                if non_exist_response.getCode() not in self._bad_codes\
                and get_response.getBody() == non_exist_response.getBody():
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName( 'Non existent methods default to GET' )
                    i.setURL( url )
                    i.setId( [non_exist_response.getId(), get_response.getId()] )
                    msg = 'The remote Web server has a custom configuration, in which any non'
                    msg += ' existent methods that are invoked are defaulted to GET instead of'
                    msg += ' returning a "Not Implemented" response.'
                    i.setDesc( msg )
                    kb.kb.append( self , 'custom-configuration' , i )
                    #
                    #   It makes no sense to continue working, all methods will appear as enabled
                    #   because of this custom configuration.
                    #
                    return []

            
            # 'DELETE' is not tested! I don't want to remove anything...
            # 'PUT' is not tested! I don't want to overwrite anything...
            methods_to_test = self._supported_methods[:]
            
            # remove dups, and dangerous methods.
            methods_to_test = list(set(methods_to_test))
            methods_to_test.remove('DELETE')
            methods_to_test.remove('PUT')

            for method in methods_to_test:
                method_functor = getattr( self._urlOpener, method )
                try:
                    response = apply( method_functor, (url,) , {} )
                    code = response.getCode()
                except:
                    pass
                else:
                    if code not in self._bad_codes:
                        allowed_methods.append( method )
        
        # Added this to make the output a little more readable.
        allowed_methods.sort()
        
        # Check for DAV
        if len( set( allowed_methods ).intersection( self._dav_methods ) ) != 0:
            # dav is enabled!
            # Save the results in the KB so that other plugins can use this information
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Allowed methods for ' + url )
            i.setURL( url )
            i.setId( id_list )
            i['methods'] = allowed_methods
            msg = 'The URL "' + url + '" has the following allowed methods, which'
            msg += ' include DAV methods: ' + ', '.join(allowed_methods)
            i.setDesc( msg )
            kb.kb.append( self , 'dav-methods' , i )
        else:
            # Save the results in the KB so that other plugins can use this information
            # Do not remove these information, other plugins REALLY use it !
            i = info.info()
            i.setPluginName(self.getName())
            i.setName('Allowed methods for ' + url )
            i.setURL( url )
            i.setId( id_list )
            i['methods'] = allowed_methods
            msg = 'The URL "' + url + '" has the following allowed methods:'
            msg += ' ' + ', '.join(allowed_methods)
            i.setDesc( msg )
            kb.kb.append( self , 'methods' , i )
            
        return []
    
    def end( self ):
        '''
        Print the results.
        '''
        # First I get the data from the kb
        all_info_obj = kb.kb.getData( 'allowedMethods', 'methods' )
        dav_info_obj = kb.kb.getData( 'allowedMethods', 'dav-methods' )
        
        # Now I transform it to something I can use with groupbyMinKey
        allMethods = []
        for i in all_info_obj:
            allMethods.append( (i.getURL() , i['methods']) )
        
        davMethods = []
        
        for i in dav_info_obj:
            davMethods.append( (i.getURL() , i['methods']) )

        # Now I work the data...
        to_show, method_type = davMethods, ' DAV'
        if not self._report_dav_only:
            to_show, method_type = allMethods, ''
       

        # Make it hashable
        tmp = []
        for url, methodList in to_show:
            tmp.append( (url, ', '.join( methodList ) ) )
        
        result_dict, itemIndex = groupbyMinKey( tmp )
            
        for k in result_dict:
            if itemIndex == 0:
                # Grouped by URLs
                msg = 'The URL: "%s" has the following' + method_type + ' methods enabled:'
                om.out.information(msg % k)
            else:
                # Grouped by Methods
                msg = 'The methods: ' + k + ' are enabled on the following URLs:'
                om.out.information(msg)
            
            for i in result_dict[k]:
                om.out.information('- ' + i )
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Execute plugin only one time'
        h1 = 'Generally the methods allowed for a URL are \
          configured system wide, so executing this plugin only one \
          time is the faster choice. The safest choice is to run it against every URL.'
        o1 = option('execOneTime', self._exec_one_time, d1, 'boolean', help=h1)
        
        d2 = 'Only report findings if uncommon methods are found'
        o2 = option('reportDavOnly', self._report_dav_only, d2, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._exec_one_time = optionsMap['execOneTime'].getValue()
        self._report_dav_only = optionsMap['reportDavOnly'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return []

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds what HTTP methods are enabled for a URI.
        
        Two configurable parameters exist:
            - execOneTime
            - reportDavOnly
        
        If "execOneTime" is set to True, then only the methods in the webroot are enumerated.
        If "reportDavOnly" is set to True, this plugin will only report the enabled method list if DAV methods
        have been found.
        
        The plugin will try to use the OPTIONS method to enumerate all available methods, if that fails, a manual
        enumeration is done, when doing a manual enumerationy.
        '''
