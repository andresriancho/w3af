'''
pathDisclosure.py

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

import core.data.parsers.htmlParser as htmlParser
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList
from core.controllers.basePlugin.baseGrepPlugin import baseGrepPlugin
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
import urllib
import re
from core.data.getResponseType import *
import core.data.constants.severity as severity

class pathDisclosure(baseGrepPlugin):
    '''
    Grep every page for traces of path disclosure problems.
      
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseGrepPlugin.__init__(self)
        self._urlList = []

    def _testResponse(self, request, response):
        
        if response.is_text_or_html():
            # Decode the realurl
            realurl = urlParser.urlDecode( response.getURL() )
            
            htmlString = response.getBody()
            for pathDisclosureString in self._getPathDisclosureStrings():
                matches = re.findall( pathDisclosureString + '.*?[:|\'|"|<|\n|\r|\t]', htmlString  )
                for match in matches:
                    match = match[:-1]
                    
                    # The if is to avoid false positives
                    if len(match) < 80 and not self._wasSent( request, pathDisclosureString )\
                    and not self._attrValue( match, htmlString ):
                        
                        v = vuln.vuln()
                        v.setURL( realurl )
                        v.setId( response.id )
                        v.setDesc( 'The URL: "' + v.getURL() + '" has a path disclosure problem: "' + match  + '".')
                        v.setSeverity(severity.LOW)
                        v.setName( 'Path disclosure vulnerability' )
                        v['path'] = match
                        kb.kb.append( self, 'pathDisclosure', v )
        
        self._updateKBPathList( response.getURL() )
    
    def _attrValue(self, pathDisclosureString, responseBody ):
        '''
        This method was created to remove some false positives.
        
        @return: True if pathDisclosureString is the value of an attribute inside a tag.
        
        Examples:
            pathDisclosureString = '/home/image.png'
            responseBody = '....<img src="/home/image.png">...'
            return: True
            
            pathDisclosureString = '/home/image.png'
            responseBody = '...<b>Error while processing /home/image.png</b>...'
            return: False
        '''
        regex_res = re.findall('<.+?(["|\']'+pathDisclosureString+'["|\']).*?>', responseBody)
        count_res = responseBody.count( pathDisclosureString )
        
        if count_res > len(regex_res):
            return False
        else:
            return True
    
    def _updateKBPathList( self, url ):
        '''
        If a path disclosure was found, I can create a list of full paths to all URLs ever visited.
        This method updates that list.
        '''
        self._urlList.append( url )
        
        pathDiscVulns = kb.kb.getData( 'pathDisclosure', 'pathDisclosure' ) 
        if len( pathDiscVulns ) == 0:
            # I cant calculate the list !
            pass
        else:
            # Note that this list is recalculated every time a new page is accesed
            # this is goood :P
            urlList = kb.kb.getData( 'urls', 'urlList' )
            match = False
            for pathDiscVuln in pathDiscVulns:
                for url in urlList:
                    pathAndFile = urlParser.getPath( url )
                    
                    if pathDiscVuln['path'].endswith( pathAndFile ):
                        match = True
                        
                        if urlParser.baseUrl( urlList[0] ) not in urlList:
                            urlList.append( urlParser.baseUrl( urlList[0] ) )
                        
                        webroot = pathDiscVuln['path'].replace( pathAndFile, '' )
                        tmp = []
                        for url in urlList:
                            tmp.append( webroot + urlParser.getPath( url ) )
                        
                        tmp.extend( kb.kb.getData( 'pathDisclosure', 'listFiles') )
                        paths = list( set( tmp ) )
                        kb.kb.save( self, 'listFiles', tmp )
                        
                        # Now I create the path list based on the file list
                        # I have to be extra carefull, cause :
                        # - I cant use os.path.dirname [cause i', working with a remote server]
                        # - Windows and linux paths are diff :P
                        pathSep = '/'
                        if webroot[0]!='/':
                            pathSep = '\\'
                        paths = []
                        for file in tmp:
                            # I need to get the path
                            path = pathSep.join( file.split( pathSep )[:-1] ) + pathSep
                            paths.append( (webroot,path) )
                            
                        paths.extend( kb.kb.getData( 'pathDisclosure', 'listPaths') )
                        paths = list( set( paths ) )
                        kb.kb.save( self, 'listPaths', paths ) 
            
            if not match:
                kb.kb.save( self, 'listFiles', [] ) 
                kb.kb.save( self, 'listPaths', [] ) 
        
    def setOptions( self, OptionList ):
        pass
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        inform = []
        for v in kb.kb.getData( 'pathDisclosure', 'pathDisclosure' ):
            inform.append( v )
        
        tmp = {}
        ids = {}
        for v in inform:
            if v.getURL() in tmp.keys():
                tmp[ v.getURL() ].append( v['path'] )
            else:
                tmp[ v.getURL() ] = [ v['path'], ]
                                
            if v['path'] in ids.keys():
                ids[ v['path'] ].append( v.getId() )
            else:
                ids[ v['path'] ] = [ v.getId(), ]
        
        # Avoid duplicates
        for url in tmp.keys():
            tmp[ url ] = list( set( tmp[ url ] ) )
        
        for url in tmp.keys():
            om.out.information( 'The URL: ' + url + ' has the following path disclosure problems:' )
            for path in tmp[ url ]:
                toPrint = '- ' + path + ' . Found in request id\'s: '
                toPrint += str( list( set( ids[ path ] ) ) )
                om.out.information( toPrint )

    def _getPathDisclosureStrings(self):
        '''
        Return a list of regular expressions to be tested.
        '''
        
        path_disclosure_strings = []
        path_disclosure_strings.append(r"[A-Z]:\\") 
        path_disclosure_strings.append("/root/")
        path_disclosure_strings.append("/var/")
        path_disclosure_strings.append("/htdocs/")
        path_disclosure_strings.append("/usr/")
        path_disclosure_strings.append("/home/")
        path_disclosure_strings.append("/etc/")
        path_disclosure_strings.append("/bin/")
        path_disclosure_strings.append("/lib/")
        path_disclosure_strings.append("/opt/")
        path_disclosure_strings.append("/sbin/")
        path_disclosure_strings.append("/sys/")
        path_disclosure_strings.append("/mnt/")
        path_disclosure_strings.append("/tmp/")
        return path_disclosure_strings

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
        This plugin greps every page for traces of path disclosure problems.
        '''
