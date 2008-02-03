'''
mailer.py

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

import core.data.parsers.dpCache as dpCache
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
from core.controllers.w3afException import *
import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.formFiller import smartFill
import core.data.request.httpPostDataRequest as httpPostDataRequest
from core.data.request.httpQsRequest import httpQsRequest
from core.data.parsers.dpCache import dpc as dpc
import core.data.kb.info as info
from core.controllers.threads.threadManager import threadManagerObj as tm
import re
import socket
import copy
import md5
import smtpd, os, time, asyncore
import smtplib
import time

class mailer(baseDiscoveryPlugin, smtpd.SMTPServer):
    '''
    Start a smtpd, sends forms that have an email field in it, and waits to see if a mail arrives.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._smtpIsRunning = False
        self._errorStarting = False
        self._mailUser = 1
        self._sentForms = {}
        self._newFuzzableRequests = []  # Only modified by the mail handler
        self._receivedMessages = 0
        
        # Grep the email for IP addresses
        self._classA = re.compile('(10\.\d?\d?\d?\.\d?\d?\d?\.\d?\d?\d?)')
        self._classB = re.compile('(172\.[1-3]\d?\d?\.\d?\d?\d?\.\d?\d?\d?)')
        self._classC = re.compile('(192\.168\.\d?\d?\d?\.\d?\d?\d?)')
        
        # User configured parameters
        self._mailDomain = ''
        self._listenAddress = ''
        try:
            self._mailDomain = socket.gethostbyname(socket.gethostname())
            self._listenAddress = socket.gethostbyname(socket.gethostname())
        except Exception, e:
            om.out.debug('Failed to get the local IP address. Exception error: ' + str(e) )
            
        self._inputNames = ['mail', 'email', 'correo', 'e-mail', 'contact', 'contacto']
        
    def discover(self, fuzzableRequest ):
        '''
        Starts smtpd, fill forms, wait for emails, analyze emails.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        om.out.debug( 'mailer plugin is testing: ' + fuzzableRequest.getURL() )
        
        if not self._smtpIsRunning and not self._errorStarting:
            try:
                self._startSMTPd()
                self._testMailReception()
            except socket.error, e:
                self._errorStarting = True
                
                if 'permission' in e[1].lower():
                    om.out.error('Exception caught while starting SMTPd, error message: ' + str(e[1]) )
                    om.out.error('Hint: You have to be root to bind on port 25.' )
                else:
                    om.out.error('Exception caught while starting SMTPd, error message: ' + str(e[1]) )
                # I dont want to run anymore
                raise w3afRunOnce()
            
            except w3afException, w3:
                self._errorStarting = True
                raise w3
                
            except Exception, e:
                self._errorStarting = True
                
                om.out.error('Unhandled exception caught while starting SMTPd, error message: ' + str(e) )
                # I dont want to run anymore
                raise w3afRunOnce()
            else:
                self._smtpIsRunning = True
            
            
        # Clean the results to avoid duplicates
        self._newFuzzableRequests
        
        # Start
        if self._smtpIsRunning:
            if self._isFormWithEmail( fuzzableRequest ):
                frCopy = fuzzableRequest.copy()
                frCopy = self._fillEmail( frCopy )
                try:
                    response = self._sendMutant( frCopy, analyze=False )
                except KeyboardInterrupt,e:
                    raise e
        
        return self._newFuzzableRequests
    
    def _testMailReception( self ):
        '''
        Test the configured settings to see if the user did things right.
        '''
        fromaddr = 'test@w3af.sf.net'
        toaddrs  = 'test@' + self._mailDomain
        msg = 'test message'
        
        # send the mail
        server = smtplib.SMTP('localhost', 25255)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        
        # Let the mail arrive...
        time.sleep(2)
        
        # Check what happend
        if self._receivedMessages == 0:
            om.out.error('Mailer plugin failed to receive a test message; please verify that you have:')
            om.out.error('- MX record of the mailDomain pointing to this host')
            om.out.error('- firewall rules that allow traffic on port 25')
            raise w3afException('Failed to configure the mailer plugin, check MX record and firewall configuration.')
        else:
            om.out.debug('Mailer plugin successfully configured and initialized.')

    
    def _startSMTPd( self ):
        if self._mailDomain == '127.0.0.1' or self._mailDomain == '' or self._listenAddress == '':
            raise w3afException('You should manually configure the mail domain. Automatic detection of your IP address failed.')
        
        smtpd.SMTPServer.__init__(self, (self._listenAddress,25), None)
        om.out.information('Mailer plugin successfully started an SMTPd on socket: ' + self._listenAddress +':25')
        try:
            tm.startFunction( asyncore.loop , (), restrict=False, ownerObj=self )
        except Exception, e:
            self.close()

    def process_message(self, peer, mailfrom, rcpttos, data):
        '''
        This method processes messages sent to my email server, analyzes headers and gets new URLs.
        '''
        self._receivedMessages += 1
        
        om.out.debug('Received an email from the web server.')
        om.out.debug('[mail info] peer:' + str(peer) )
        om.out.debug('[mail info] mailfrom:' + str(mailfrom) )
        om.out.debug('[mail info] rcpttos:' + repr(rcpttos) )
        om.out.debug('[mail info] data:' + data )
        
        # Save the source email address to the kb
        i = info.info()
        i.setName('Mailing address')
        i.setDesc( 'The email address: ' + mailfrom + ' is used by the application to send emails.' )
        i['mail'] = mailfrom
        i['user'] = mailfrom.split('@')[0]
        kb.kb.append( self, 'mails', i )
        
        # Analyze the mail headers to find private IP addresses
        res = self._classA.findall( data )
        res.extend( self._classB.findall( data ) )
        res.extend( self._classC.findall( data ) )
        for ipAddress in res:
            i = info.info()
            i.setDesc( 'The private IP address "'+ ipAddress +'" was found in an email sent by the web application.' )
            i['IP'] = ipAddress
            kb.kb.append( self, 'ipAddress', i )
        
        # Find URLs in the email
        docuParser = dpc.getDocumentParserFor( httpRes.getBody(), httpRes.getURL() )
        for ru in docuParser.getReferences():
            QSObject = urlParser.getQueryString( ru )
            qsr = httpQsRequest()
            qsr.setURI( ru )
            qsr.setDc( QSObject )
            self._newFuzzableRequests.append( qsr )

    def _fillEmail( self, fuzzableRequest ):
        # smartFill the Dc.
        dc = fuzzableRequest.getDc()
        for parameter in dc:
            dc[ parameter ] = smartFill( parameter )
        fuzzableRequest.setDc( dc )
        
        # Now I fill the email field with a specially crafted email addy
        mailAddy = md5.new( str(self._mailUser) ).hexdigest() + '@' + self._mailDomain
        self._mailUser += 1
        self._sentForms[ mailAddy ] = fuzzableRequest
        
        dc = fuzzableRequest.getDc()
        for parameter in dc:
            if self._isMailInput( parameter ):
                dc[ parameter ] = mailAddy
                
        fuzzableRequest.setDc( dc )
        return fuzzableRequest
            
    def _isFormWithEmail( self, fuzzableRequest ):
        # Check if it's a form
        if not isinstance( fuzzableRequest, httpPostDataRequest.httpPostDataRequest ):
            return False
        else:
            # Check if an email input is present
            for inputName in fuzzableRequest.getDc():
                if self._isMailInput( inputName ):
                    return True
            return False
    
    def _isMailInput( self, inputName ):
        inputName = inputName.lower()
        for registeredIname in self._inputNames:
            if inputName in registeredIname or registeredIname in inputName:
                return True
        return False
    
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
            <Option name="mailDomain">\
                <default>'+str(self._mailDomain)+'</default>\
                <desc>Use this domain when filling forms that contain an "email" form input.</desc>\
                <help>When this plugin fill up a form, it will do it like: someString@[mailDomain]</help>\
                <type>string</type>\
            </Option>\
            <Option name="listenAddress">\
                <default>'+str(self._listenAddress)+'</default>\
                <desc>The smtp daemon will listen in this IP addres.</desc>\
                <type>string</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._mailDomain = optionsMap['mailDomain']
        self._listenAddress = optionsMap['listenAddress']
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ ]
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find new URLs by filling up forms that have an email input, receiving the email,
        and then analyzing the email. This plugin also tries to identify the private IP address of the remote
        web server using SMTP header analysis.
    
        Two configurable parameter exist:
            - mailDomain
            - listenAddress
        
        When this plugin fills up a form, it will do it like: someString@[mailDomain]
        The listenAddress parameter is the IP address used by the SMTPd to receive emails.
        '''
