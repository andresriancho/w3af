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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

from core.data.bloomfilter.pybloom import ScalableBloomFilter
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.data.fuzzer.fuzzer import createRandAlNum


class urlFuzzer(baseDiscoveryPlugin):
    '''
    Try to find backups, and other related files.
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        self._first_time = True
        self._fuzzImages = False
        self._headers = {}
        self._already_reported = ScalableBloomFilter()
        
    def discover(self, fuzzableRequest ):
        '''
        Searches for new Url's using fuzzing.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._fuzzable_requests = []
            
        url = fuzzableRequest.getURL()
        self._headers = {'Referer':url }
        
        if self._first_time:
            self._verify_head_enabled( url )
            self._first_time = False
        
        # First we need to delete fragments and query strings from URL.
        url = urlParser.uri2url( url )

        # And we mark this one as a "do not return" URL, because the core already
        # found it using another technique.
        self._already_reported.add( url )
        
        self._verify_head_enabled( url )
        if self._head_enabled():
            response = self._urlOpener.HEAD( url, useCache=True, headers=self._headers )
        else:
            response = self._urlOpener.GET(url, useCache=True, headers=self._headers)

        if response.is_text_or_html() or self._fuzzImages:
            mutants = self._mutate( url )
            om.out.debug('urlFuzzer is testing ' + url )
            for mutant in mutants :
                targs = ( url, mutant )
                self._tm.startFunction( target=self._do_request, args=targs, ownerObj=self )
            self._tm.join( self )
        
        return self._fuzzable_requests

    def _do_request( self, url, mutant ):
        '''
        Perform a simple GET to see if the result is an error or not, and then
        run the actual fuzzing.
        '''
        try:
            response = self._urlOpener.GET( mutant, useCache=True, headers=self._headers )
        except KeyboardInterrupt,e:
            raise e
        else:
            if not is_404( response ) and response.getCode() not in [403, 401]:
                if not self._return_without_eval( mutant ):
                    #
                    #   Return it to the core...
                    #
                    fr_list = self._createFuzzableRequests( response )
                    self._fuzzable_requests.extend( fr_list )
                    
                    #
                    #   Save it to the kb (if new)!
                    #
                    if response.getURL() not in self._already_reported and not response.getURL().endswith('/'):
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('Potentially interesting file')
                        i.setURL( response.getURL() )
                        i.setId( response.id )
                        i.setDesc( 'A potentially interesting file was found at: "'+ response.getURL() +'".' )
                        kb.kb.append( self, 'files', i )
                        om.out.information( i.getDesc() )
                        
                        #   Report only once
                        self._already_reported.add( response.getURL() )
                    
    
    def _return_without_eval( self, uri ):
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
        except w3afException,e:
            msg = 'An exception was raised while requesting "'+url+'" , the error message is: '
            msg += str(e)
            om.out.error( msg )
        else:
            if not is_404( response ):
                return True
        return False

    def _mutate(self, url):
        '''
        Mutate this URL !
        @param url: The original url
        @return: A list of bad looking mutant URL's.
        '''
        mutants = []
        mutants = self._mutate_by_appending( url )
        mutants.extend( self._mutate_path( url ) )
        mutants.extend( self._mutate_file_type( url ) )
        mutants.extend( self._mutate_domain_name( url ) )
        mutants = list( set( mutants ) )
        return mutants
    
    def _mutate_domain_name( self, url ):
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
            for extension in self._get_backup_extensions():
                res.append( domainPath + filename + '.' + extension )
                ### TODO: review this code !!
        return res
        
    def _mutate_by_appending( self, url ):
        '''
        Adds something to the end of the url (mutate the file being requested)
        
        @return: A list of mutants.
        '''
        mutants = []
        if not url.endswith('/') and url.count('/') >= 3:
            #
            #   Only get here on these cases:
            #       - http://host.tld/abc
            #       - http://host.tld/abc/def.html
            #
            #   And not on these:
            #       - http://host.tld
            #       - http://host.tld/abc/
            #
            for to_append in self._get_to_append():
                mutants.append ( url + to_append )
        return mutants
    
    def _mutate_file_type( self, url ):
        '''
        Mutates a URL by changing its filetype, example :
        url = http://g.ar/foo.php
        result = http://g.ar/foo.zip , http://g.ar/foo.tgz , etc...
        
        @return: A mutant list.
        '''
        mutants = []
        
        extension = urlParser.getExtension( url )
        if extension:
            
            if url.rfind('.') > url.rfind('/'):
                url = url[ : url.rfind('.')+1 ]
                filetypes = self._get_file_types()
                for filetype in filetypes:
                    mutants.append ( url + filetype )
                    
        return mutants

    def _mutate_path( self, url ):
        '''
        Mutate the path instead of the file.
        
        @return: A list of mutants.
        '''
        mutants = []
        if url.count('/') > 3:
            url = url[: url.rfind('/') ]
            toAppendList = self._get_to_append()
            for toAppend in toAppendList:
                mutants.append ( url + toAppend )
            
            if not url.endswith('/'):
                url += '/'
            mutants.append( url )
            
        return mutants
    
    def _get_backup_extensions( self ):
        fileTypes = []
        fileTypes.append ( 'tar.gz' )
        fileTypes.append ( '7z' )
        fileTypes.append ( 'gz' )
        fileTypes.append ( 'cab' )
        fileTypes.append ( 'tgz' )
        fileTypes.append ( 'gzip' )
        fileTypes.append ( 'bzip2' )
        fileTypes.append ( 'zip' )
        fileTypes.append ( 'rar' )
        return fileTypes

    
    def _get_file_types( self ):
        '''
        @return: A list with filetypes commonly used in web apps.
        '''
        fileTypes = []
        fileTypes.extend( self._get_backup_extensions() )
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
        
    def _get_to_append( self ):
        '''
        
        @return: A list of strings to append to the URL.
        '''
        appendables = []
        appendables.append ( '~' )
        appendables.append ( '.tar.gz' )
        appendables.append ( '.gz' )
        appendables.append ( '.7z' )
        appendables.append ( '.cab' )
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
        appendables.append ( '.bkp' )
        appendables.append ( '.back' )
        appendables.append ( '.backup' )
        appendables.append ( '.backup1' )       
        appendables.append ( '.old' )
        appendables.append ( '.old1' )
        appendables.append ( '.$$$' )       # mariano
        return appendables
        
    
    def _verify_head_enabled(self, url ):
        '''
        Verifies if the requested URL permits a HEAD request.
        This was saved inside the KB by the plugin allowedMethods
        
        @return : Sets self._head to the correct value, nothing is returned.
        '''
        if 'HEAD' in kb.kb.getData( 'allowedMethods' , 'methods' ):
            self._head = True
        else:
            self._head = False
        
    def _head_enabled(self):
        return self._head
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Apply URL fuzzing to all URLs, including images, videos, zip, etc.'
        h1 = 'Don\'t change this unless you read the plugin code.'
        o1 = option('fuzzImages', self._fuzzImages, d1, 'boolean', help=h1)
        
        ol = optionList()
        ol.add(o1)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._fuzzImages = optionsMap['fuzzImages'].getValue()
    
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
        
        If the response is different from the 404 page (whatever it may be, automatic detection is 
        performed), then we have found a new URL. This plugin searches for backup files, source code
        , and other common extensions.
        
        One configurable parameter exist:
            - fuzzImages
        '''
