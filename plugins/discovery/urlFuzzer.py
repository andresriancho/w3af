'''
urlFuzzer.py

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

import core.data.parsers.urlParser as urlParser
from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
from core.data.getResponseType import *
from core.controllers.w3afException import w3afException
from core.data.fuzzer.fuzzer import *

class urlFuzzer(baseDiscoveryPlugin):
    '''
    Try to find backups, and other related files.
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._firstTime = True
        self._fuzzImages = False
        self._headers = {}
        
    def discover(self, fuzzableRequest ):
        '''
        Searches for new Url's using fuzzing.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzableRequests = []
            
        url = fuzzableRequest.getURL()
        self._headers = {'Referer':url }
        
        if self._firstTime:
            self._verifyHeadEnabled( url )
            self._firstTime = False
            self.is404 = kb.kb.getData( 'error404page', '404' )
        
        # First we need to delete fragments and query strings from URL.
        url = urlParser.uri2url( url )

        self._verifyHeadEnabled( url )
        if self._headEnabled():
            response = self._urlOpener.HEAD( url, useCache=True, headers=self._headers )
        else:
            response = self._urlOpener.GET( url, useCache=True, headers=self._headers, getSize=True )

        if isTextOrHtml( response.getHeaders() ) or self._fuzzImages:
            mutants = self._mutate( url )
            om.out.debug('urlFuzzer is testing ' + url )
            for mutant in mutants :
                targs = ( url, mutant )
                self._tm.startFunction( target=self._doRequest, args=targs, ownerObj=self )
            self._tm.join( self )
        
        return self._fuzzableRequests

    def _doRequest( self, url, mutant ):
        try:
            response = self._urlOpener.GET( mutant, useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        else:
            if not self.is404( response ) and response.getCode() not in [403, 401]:
                if not self._returnWithoutEval( mutant ):
                    frList = self._createFuzzableRequests( response )
                    self._fuzzableRequests.extend( frList )
    
    def _returnWithoutEval( self, uri ):
        '''
        This method tries to lower the false positives. 
        '''     
        if urlParser.getDomainPath( uri ) == uri:
            return False
        
        url = urlParser.uri2url( uri )
        url += createRandAlNum( 7 )
        if urlParser.getQueryString( uri ):
            url = url + '?' + str( urlParser.getQueryString( uri ) )
            
        try:
            response = self._urlOpener.GET( url, useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        except Exception,e:
            om.out.error( 'Error when requesting: '+  url )
            om.out.error('Error: ' + str(e) )
        else:
            if not self.is404( response ):
                return True
        return False

    def _mutate(self, url):
        '''
        Mutate this URL !
        @param url: The original url
        @return: A list of bad looking mutant URL's.
        '''
        mutants = []
        mutants = self._mutateByAppending( url )
        mutants.extend( self._mutatePath( url ) )
        mutants.extend( self._mutateFileType( url ) )
        mutants.extend( self._mutateDomainName( url ) )
        mutants = list( set( mutants ) )
        return mutants
    
    def _mutateDomainName( self, url ):
        '''
        If the url is : "http://www.foobar.com/asd.txt" this method returns:
            - http://www.foobar.com/foobar.zip
            - http://www.foobar.com/foobar.rar
            - http://www.foobar.com/www.foobar.zip
            - http://www.foobar.com/www.foobar.rar
            - etc...
        
        @return: A list of mutants.
        '''
        domain = urlParser.getDomain( url )
        domainPath = urlParser.getDomainPath( url )
        
        splittedDomain = domain.split('.')
        res = []
        for i in xrange( len ( splittedDomain ) ):
            filename = '.'.join(splittedDomain[0: i+1])
            for extension in self._getBackupExtensions():
                res.append( domainPath + filename + '.' + extension )
                ### TODO: review this code !!
        return res
        
    def _mutateByAppending( self, url ):
        '''
        Adds something to the end of the url (mutate the file being requested)
        
        @return: A list of mutants.
        '''
        mutants = []
        if url[ len( url ) -1 ] != '/':
            toAppendList = self._getToAppend()
            for toAppend in toAppendList:
                mutants.append ( url + toAppend )
        return mutants
    
    def _mutateFileType( self, url ):
        '''
        Mutates a URL by changing its filetype, example :
        url = http://g.ar/foo.php
        result = http://g.ar/foo.zip , http://g.ar/foo.tgz , etc...
        
        @return: A mutant list.
        '''
        mutants = []
        if url.rfind('.') > url.rfind('/'):
            # Has a file specification
            # http://a.com/foo.asp
            #                           ^  This
            url = url[ : url.rfind('.')+1 ]
            filetypes = self._getFileTypes()
            for filetype in filetypes:
                mutants.append ( url + filetype )
        return mutants

    def _mutatePath( self, url ):
        '''
        Mutate the path instead of the file.
        
        @return: A list of mutants.
        '''
        mutants = []
        if url.count('/') > 3:
            url = url[: url.rfind('/') ]
            toAppendList = self._getToAppend()
            for toAppend in toAppendList:
                mutants.append ( url + toAppend )
            mutants.append( url )
            mutants.append( url + '/')
        return mutants
    
    def _getBackupExtensions( self ):
        fileTypes = []
        fileTypes.append ( 'tar.gz' )
        fileTypes.append ( 'gz' )
        fileTypes.append ( 'tgz' )
        fileTypes.append ( 'gzip' )
        fileTypes.append ( 'bzip2' )
        fileTypes.append ( 'zip' )
        fileTypes.append ( 'rar' )
        return fileTypes

    
    def _getFileTypes( self ):
        '''
        @return: A list with filetypes commonly used in web apps.
        '''
        fileTypes = []
        fileTypes.extend( self._getBackupExtensions() )
        fileTypes.append ( 'inc' )      
        fileTypes.append ( 'fla' )  # flash
        fileTypes.append ( 'jar' )
        fileTypes.append ( 'java' )
        fileTypes.append ( 'class' )
        fileTypes.append ( 'properties' )
        fileTypes.append ( 'bak' )
        fileTypes.append ( 'bak1' )
        fileTypes.append ( 'backup' )
        fileTypes.append ( 'backup1' )      
        fileTypes.append ( 'old' )
        fileTypes.append ( 'old1' )
        fileTypes.append ( 'c' )
        fileTypes.append ( 'cpp' )
        # .net source
        fileTypes.append ( 'cs' )
        fileTypes.append ( 'vb' )
        # php source
        fileTypes.append ( 'phps' )
        # webservice .disco files !
        fileTypes.append ( 'disco' )        
        return fileTypes
        
    def _getToAppend( self ):
        '''
        
        @return: A list of strings to append to the URL.
        '''
        appendables = []
        appendables.append ( '~' )
        appendables.append ( '.tar.gz' )
        appendables.append ( '.gz' )
        appendables.append ( '.tgz' )
        appendables.append ( '.gzip' )
        appendables.append ( '.bzip2' )
        appendables.append ( '.inc' )
        appendables.append ( '.zip' )
        appendables.append ( '.rar' )
        appendables.append ( '.jar' )
        appendables.append ( '.java' )
        appendables.append ( '.class' )
        appendables.append ( '.properties' )
        appendables.append ( '.bak' )
        appendables.append ( '.bak1' )
        appendables.append ( '.backup' )
        appendables.append ( '.backup1' )       
        appendables.append ( '.old' )
        appendables.append ( '.old1' )
        appendables.append ( '.$$$' )       # mariano
        return appendables
        
    
    def _verifyHeadEnabled(self, url ):
        '''
        Verifies if the requested URL permits a HEAD request.
        This was saved inside the KB by the plugin allowedMethods
        
        @return : Sets self._head to the correct value, nothing is returned.
        '''
        if 'HEAD' in kb.kb.getData( 'allowedMethods' , 'methods' ):
            self._head = True
        else:
            self._head = False
        
    def _headEnabled(self):
        return self._head
    
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
            <Option name="fuzzImages">\
                <default>'+str(self._fuzzImages)+'</default>\
                <desc>Apply URL fuzzing to all URLs, including images, videos, zip, etc.</desc>\
                <type>boolean</type>\
                <help>It\'s safe to leave this option as the default.</help>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzzImages = optionsMap['fuzzImages']
    
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.allowedMethods']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin will try to find new URL's based on the input. If the input is for example:
            - http://a/a.html
            
        The plugin will request:
            - http://a/a.html.tgz
            - http://a/a.tgz
            - http://a/a.zip
            ... etc
        
        If the response is not a 404 error, then we have found a new URL. This plugin searches for
        backup files, source code, and other common extensions.
        
        One configurable parameter exist:
            - fuzzImages
        '''
