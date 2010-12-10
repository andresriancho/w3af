'''
userDir.py

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
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import core.data.parsers.urlParser as urlParser

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.controllers.misc.levenshtein import relative_distance_lt


class userDir(baseDiscoveryPlugin):
    '''
    Try to find user directories like "http://test/~user/" and identify the remote OS based on the remote users.
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
            
        # Internal variables
        self._run = True
        self._run_OS_ident = True
        self._run_app_ident = True
        
        # User configured variables
        self._identify_OS = True
        self._identify_applications = True
        
        # For testing
        self._do_fast_search = False
    
    def discover(self, fuzzableRequest ):
        '''
        Searches for user directories.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                                    (among other things) the URL to test.
        '''
        if not self._run:
            raise w3afRunOnce()
            
        else:
            self._run = False
            self._fuzzable_requests = []
                
            base_url = urlParser.baseUrl( fuzzableRequest.getURL() )
            self._headers = {'Referer': base_url }
            
            # Create a response body to compare with the others
            non_existant_user = '~_w_3_a_f_/'
            test_URL = urlParser.urlJoin( base_url, non_existant_user )
            try:
                response = self._urlOpener.GET( test_URL, useCache=True, \
                                                                    headers=self._headers )
                response_body = response.getBody()                
            except:
                raise w3afException('userDir failed to create a non existant signature.')
                
            self._non_existant = response_body.replace( non_existant_user, '')
            
            # Check the users to see if they exist
            url_user_list = self._create_dirs( base_url )
            for url, user in url_user_list :
                om.out.debug('userDir is testing ' + url )
                
                #   Send the requests using threads:
                targs = ( url, user )
                self._tm.startFunction( target=self._do_request, args=targs, ownerObj=self )
                
            # Wait for all threads to finish
            self._tm.join( self )
            
            # Only do this if I already know that users can be identified.
            if kb.kb.getData( 'userDir', 'users' ) != []:
                # AND only run once
                if self._run_OS_ident:
                    self._run_OS_ident = False
                    self._advanced_identification( base_url, 'os' )
                
                if self._run_app_ident:
                    self._run_app_ident = False
                    self._advanced_identification( base_url, 'apps' )
                    
                # Report findings of remote OS, applications, users, etc.
                self._report_findings()
            
            return self._fuzzable_requests

    def _do_request( self, mutant, user ):
        '''
        Perform the request and compare.
        
        @return: True when the user was found.
        '''
        try:
            response = self._urlOpener.GET( mutant, useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        else:
            path = mutant.replace( urlParser.baseUrl( mutant ) , '' )
            response_body = response.getBody().replace( path, '')
            
            if relative_distance_lt(response_body, self._non_existant, 0.7):
                
                # Avoid duplicates
                if user not in [ u['user'] for u in kb.kb.getData( 'userDir', 'users') ]:
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('User directory: ' + response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'A user directory was found at: ' + response.getURL() )
                    i['user'] = user
                    
                    kb.kb.append( self, 'users', i )
                    
                    fuzzable_request_list = self._createFuzzableRequests( response )
                    self._fuzzable_requests.extend( fuzzable_request_list )
                    
                return True
            else:
                return False

    def _advanced_identification( self, url, ident ):
        '''
        @return: None, This method will save the results to the kb and print and
        informational message to the user.
        '''
        def get_users_by_OS():
            '''
            @return: A list of tuples with ('OS', 'username-that-only-exists-in-OS')
            '''
            res = []
            res.append( ('Debian based distribution','Debian-exim') )
            res.append( ('Debian based distribution','debian-tor') )
            res.append( ('FreeBSD','kmem') )
            return res
        
        def get_users_by_app():
            '''
            @return: A list of tuples with ('app-name', 'username-that-only-exists-if-app-is-installed')
            '''
            res = []
            # Mail
            res.append( ('Exim','Debian-exim') )
            res.append( ('Fetchmail','fetchmail') )
            res.append( ('Sendmail','smmsp') )
            res.append( ('Exim','eximuser') )

            # Security
            res.append( ('Snort','snort') )
            res.append( ('TOR (The Onion Router)','debian-tor') )
            res.append( ('Privoxy (generally installed with TOR)','privoxy') )
            res.append( ('logwatch','logwatch') )
            res.append( ('Email filtering application using sendmail\'s milter interface','defang'))
            res.append( ('OpenVPN Daemon','openvpn') )
            res.append( ('Nagios','nagios') )
            res.append( ('ntop','ntop') )
            res.append( ('Big Sister is a network and system monitor','bigsis') )
            res.append( ('Packet Fence (not the openbsd pf)','pf') )
            res.append( ('A port scan detection tool','iplog') )
            res.append( ('A tool to detect and log TCP port scans','scanlogd') )
            
            # X and related stuff
            res.append( ('Gnome','gdm') )
            res.append( ('Gnats Bug-Reporting System (admin)','gnats') )
            res.append( ('X Font server','xfs') )
            
            # Clients
            res.append( ('NTP Time Synchronization Client','_ntp') )
            res.append( ('NTP Time Synchronization Client','ntp') )

            # Common services
            res.append( ('Apache web server','www-data') )
            res.append( ('Apache web server','apache') )
            res.append( ('SSH','sshd') )
            res.append( ('Bind','named') )
            res.append( ('MySQL','mysql') )
            res.append( ('PostgreSQL','postgres') )
            res.append( ('FreeRadius','radiusd') )
            res.append( ('IRCD-Hybrid is an Internet Relay Chat server','ircd') )

            # Strange services
            res.append( ('heartbeat subsystem for High-Availability Linux','hacluster') )
            res.append( ('Tinysnmp','tinysnmp') )
            res.append( ('TinyDNS','tinydns') )
            res.append( ('Plone','plone') )
            res.append( ('Rbldnsd is a small authoritate-only DNS nameserver','rbldns') )
            res.append( ('Zope, the open source web application server','zope') )
            res.append( ('LDAPdns','ldapdns') )
            res.append( ('dnsbl','dnsbl') )
            res.append( ('pwhois','pwhois') )
            res.append( ('Interchange web application platform','interch') )
            res.append( ('A DHCP relay agent','dhcp-fwd') )
            res.append( ('Extensible Web+Application server written in Tcl','tclhttpd') )
            res.append( ('A simple personal server for the WorldForge project','cyphesis') )
            res.append( ('LDAP Update Monitor','lum') )

            # Web apps
            res.append( ('OpenCM','opencm') )
            res.append( ('The Open Ticket Request System','otrs') )
            
            # Anti virus
            res.append( ('Openfire','jive') )
            res.append( ('Kapersky antivirus SMTP Gateway','kavuser') )
            res.append( ('AMaViS A mail virus scanner','amavis') )
            return res
        
        if ident == 'os':
            toTest = get_users_by_OS()
        else:
            toTest = get_users_by_app()
        
        for data_related_to_user, user in toTest:
            url_user_list = self._create_dirs( url, userList=[ user, ] )
            for uDir, user in url_user_list:
                if self._do_request( uDir, user ):
                    i = info.info()
                    i.setPluginName(self.getName())
                    if ident == 'os':
                        msg = 'The remote OS can be identified as "' + data_related_to_user
                        msg += '" based on the remote user "'+ user +'".'
                        i.setDesc( msg )
                        i['rOS'] = data_related_to_user
                        i.setName('Identified Operating System: ' + data_related_to_user )
                        kb.kb.append( self, 'os', i )
                    else:
                        msg = 'The remote server has "' + data_related_to_user + '" installed, w3af'
                        msg += ' found this information based on the remote user "'+ user +'".'
                        i.setDesc( msg )
                        i['application'] = data_related_to_user
                        i.setName('Identified application: ' + data_related_to_user )
                        kb.kb.append( self, 'applications', i )
    
    def _report_findings( self ):
        '''
        Print all the findings to the output manager.
        @return : None
        '''
        userList = [ u['user'] for u in kb.kb.getData( 'userDir', 'users') ]
        if userList:
            om.out.information('The following users were found on the remote operating system:')
            for u in userList:
                om.out.information('- ' + u )
        
        OS_list = [ u['rOS'] for u in kb.kb.getData( 'userDir', 'os') ]
        if OS_list:
            om.out.information('The remote operating system was identifyed as:')
            OS_list = list( set( OS_list ) )
            for u in OS_list:
                om.out.information('- ' + u )
        elif self._identify_OS:
            msg = 'Failed to identify the remote OS based on the users available in'
            msg += ' the userDir plugin database.'
            om.out.information(msg)
        OS_list = [ u['rOS'] for u in kb.kb.getData( 'userDir', 'os') ]
        
        app_list = [ u['application'] for u in kb.kb.getData( 'userDir', 'applications') ]
        if app_list:
            om.out.information('The remote server has the following applications installed:')
            app_list = list( set( app_list ) )
            for u in app_list:
                om.out.information('- ' + u )
        elif self._identify_OS:
            msg = 'Failed to identify any installed applications based on the users'
            msg += ' available in the userDir plugin database.'
            om.out.information(msg)
    
    def _create_dirs(self, url , userList = None ):
        '''
        Append the users to the URL.
        
        @param url: The original url
        @return: A list of URL's with the username appended.
        '''
        res = []
        
        if userList is None:
            userList = self._get_users()
            
        for user in userList:
            res.append( (urlParser.urlJoin( url , '/'+user+'/' ) , user ) )
            res.append( (urlParser.urlJoin( url , '/~'+user+'/' ) , user ) )
        return res
    
    def _get_users( self ):
        '''
        @return: All usernames collected by other plugins.
        '''
        res = []
        
        infoList = kb.kb.getData( 'mails', 'mails' )
        
        for i in infoList:
            res.append( i['user'] )
        
        # Add some common users:
        res.extend( ['www-data', 'www', 'nobody', 'root' , 'admin' , 'test', 'ftp', 'backup'] )
            
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Try to identify the remote operating system based on the remote users'
        o1 = option('identifyOS', self._identify_OS, d1, 'boolean')
        
        d2 = 'Try to identify applications installed remotely using the available users'
        o2 = option('identifyApplications', self._identify_applications, d2, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._identify_OS = optionsMap['identifyOS'].getValue()
        self._identify_applications = optionsMap['identifyApplications'].getValue()
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        if self._do_fast_search:
            # This was left here for fast testing of the plugin.
            return []
        else:
            # This is the correct return value for this method.
            return ['discovery.fingerBing', 'discovery.fingerGoogle', 'discovery.fingerPKS' ]
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will try to find user home directories based on the knowledge gained by other
        plugins, and an internal knowledge base. For example, if the target URL is:
            - http://test/
            
        And other plugins found this valid email accounts:
            - test@test.com
            - f00b4r@test.com
            
        This plugin will request:
            - http://test/~test/
            - http://test/test/
            - http://test/~f00b4r/
            - http://test/f00b4r/
        
        If the response is not a 404 error, then we have found a new URL. And confirmed the
        existance of a user in the remote system. This plugin will also identify the remote operating
        system and installed applications based on the user names that are available.
        '''
