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
import core.data.parsers.urlParser as urlParser
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import core.data.kb.info as info

class userDir(baseDiscoveryPlugin):
    '''
    Try to find user directories like "http://test/~user/" and identify the remote OS based on the remote users.
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
            
        # Internal variables
        self._run = True
        self._runOsIdent = True
        self._runAppIdent = True
        
        # User configured variables
        self._identifyOS = True
        self._identifyApplications = True
        
        # For testing
        self._doFastSearch = True
    
    def discover(self, fuzzableRequest ):
        '''
        Searches for user directories.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._run:
            raise w3afRunOnce()
            
        else:
            self._run = False
            self._fuzzableRequests = []
                
            url = urlParser.baseUrl( fuzzableRequest.getURL() )
            self._headers = {'Referer':url }
            self.is404 = kb.kb.getData( 'error404page', '404' )
            
            # Create a response body to compare with the others
            nonExistantUser = '~_w_3_a_f_/'
            testURL = urlParser.urlJoin( urlParser.baseUrl( fuzzableRequest.getURL() ),  nonExistantUser )
            try:
                responseBody = self._urlOpener.GET( testURL, useCache=True, headers=self._headers ).getBody()
            except:
                raise w3afException('userDir failed to create a non existant signature.')
            self._nonExistant = responseBody.replace( nonExistantUser, '')
            
            # Check the users to see if they exist
            url_user_list = self._createDirs( url )
            for url, user in url_user_list :
                om.out.debug('userDir is testing ' + url )
                targs = ( url, user )
                self._tm.startFunction( target=self._doRequest, args=targs, ownerObj=self )
            self._tm.join( self )
            
            # Only do this if I already know that users can be identified.
            if kb.kb.getData( 'userDir', 'users' ) != []:
                # AND only run once
                if self._runOsIdent:
                    self._runOsIdent = False
                    self._advancedIdentification( url, 'os' )
                
                if self._runAppIdent:
                    self._runAppIdent = False
                    self._advancedIdentification( url, 'apps' )
                    
                # Report findings of remote OS, applications, users, etc.
                self._reportFindings()
            
            return self._fuzzableRequests

    def _doRequest( self, mutant, user ):
        try:
            response = self._urlOpener.GET( mutant, useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        else:
            path = mutant.replace( urlParser.baseUrl( mutant ) , '' )
            responseBody = response.getBody().replace( path, '')
            if responseBody != self._nonExistant:
                # Avoid duplicates
                if user not in [ u['user'] for u in kb.kb.getData( 'userDir', 'users') ]:
                    i = info.info()
                    i.setName('User directory: ' + response.getURL() )
                    i.setId( response.id )
                    i.setDesc( 'A user directory was found at: ' + response.getURL() )
                    i['user'] = user
                    
                    kb.kb.append( self, 'users', i )
                    
                    frList = self._createFuzzableRequests( response )
                    self._fuzzableRequests.extend( frList )
                    
                return True
            else:
                return False

    def _advancedIdentification( self, url, ident ):
        '''
        @return: None, This method will save the results to the kb and print and informational message to the user.
        '''
        def getUsersByOS():
            '''
            @return: A list of tuples with ('OS', 'username-that-only-exists-in-OS')
            '''
            res = []
            res.append( ('Debian based distribution','Debian-exim') )
            res.append( ('Debian based distribution','debian-tor') )
            res.append( ('FreeBSD','kmem') )
            return res
        
        def getUsersByApp():
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
            res.append( ('Email filtering application using sendmail\'s milter interface','defang') )
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
            toTest = getUsersByOS()
        else:
            toTest = getUsersByApp()
        
        for dataRelatedToUser, user in toTest:
            url_user_list = self._createDirs( url, userList=[ user, ] )
            for uDir, user in url_user_list:
                if self._doRequest( uDir, user ):
                    i = info.info()
                    if ident == 'os':
                        i.setDesc( 'The remote OS can be identified as "' + dataRelatedToUser + '" based on the remote user "'+ user +'".' )
                        i['rOS'] = dataRelatedToUser
                        i.setName('Identified Operating System: ' + dataRelatedToUser )
                        kb.kb.append( self, 'os', i )
                    else:
                        i.setDesc( 'The remote server has "' + dataRelatedToUser + '" installed, w3af found this information based on the remote user "'+ user +'".' )
                        i['application'] = dataRelatedToUser
                        i.setName('Identified application: ' + dataRelatedToUser )
                        kb.kb.append( self, 'applications', i )
    
    def _reportFindings( self ):
        '''
        Print all the findings to the output manager.
        @return : None
        '''
        userList = [ u['user'] for u in kb.kb.getData( 'userDir', 'users') ]
        if userList:
            om.out.information('The following users were found on the remote operating system:')
            for u in userList:
                om.out.information('- ' + u )
        
        osList = [ u['rOS'] for u in kb.kb.getData( 'userDir', 'os') ]
        if osList:
            om.out.information('The remote operating system was identifyed as:')
            osList = list( set( osList ) )
            for u in osList:
                om.out.information('- ' + u )
        elif self._identifyOS:
            om.out.information('Failed to identify the remote OS based on the users available in the userDir plugin database.')
        osList = [ u['rOS'] for u in kb.kb.getData( 'userDir', 'os') ]
        
        appList = [ u['application'] for u in kb.kb.getData( 'userDir', 'applications') ]
        if appList:
            om.out.information('The remote server has the following applications installed:')
            appList = list( set( appList ) )
            for u in appList:
                om.out.information('- ' + u )
        elif self._identifyOS:
            om.out.information('Failed to identify any installed applications based on the users available in the userDir plugin database.')
    
    def _createDirs(self, url , userList = None ):
        '''
        Append the users to the URL.
        
        @param url: The original url
        @return: A list of URL's with the username appended.
        '''
        res = []
        
        if userList == None:
            userList = self._getUsers()
            
        for user in userList:
            res.append( (urlParser.urlJoin( url , '/'+user+'/' ) , user ) )
            res.append( (urlParser.urlJoin( url , '/~'+user+'/' ) , user ) )
        return res
    
    def _getUsers( self ):
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
            <Option name="identifyOS">\
                <default>'+str(self._identifyOS)+'</default>\
                <desc>Try to identify the remote operating system based on the remote users</desc>\
                <type>boolean</type>\
            </Option>\
            <Option name="identifyApplications">\
                <default>'+str(self._identifyApplications)+'</default>\
                <desc>Try to identify applications installed remotely using the available users</desc>\
                <type>boolean</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter optionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._identifyOS = optionsMap['identifyOS']
        self._identifyApplications = optionsMap['identifyApplications']
        self._fastSearch = optionsMap['fastSearch']
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        if self._doFastSearch:
            # This was left here for fast testing of the plugin.
            return []
        else:
            # This is the correct return value for this method.
            return ['discovery.fingerMSN', 'discovery.fingerGoogle', 'discovery.fingerPKS' ]
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will try to find user home directories based on the knowledge gained by other plugins.
        For example, if the target URL is:
            - http://test/
            
        And other plugins found this valid email accounts:
            - test@test.com
            - f00b4r@test.com
            
        This plugin will request:
            - http://test/~test/
            - http://test/test/
            - http://test/~f00b4r/
            - http://test/f00b4r/
        
        If the response is not a 404 error, then we have found a new URL. And confirmed the existance of a user
        in the remote system.
        '''
