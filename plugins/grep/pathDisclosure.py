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
        
        if isTextOrHtml(response.getHeaders()):
            # Decode the realurl
            realurl = urlParser.urlDecode( response.getURL() )
            
            htmlString = response.getBody()
            for pathDisclosureString in self._getPathDisclosureStrings():
                matches = re.findall( pathDisclosureString + '.*?[:|\'|"|<|\n|\r|\t]', htmlString  )
                for match in matches:
                    match = match[:-1]
                    
                    # The if is to avoid false positives
                    if len(pathDisclosureString) < 80 and not self._wasSent( request, pathDisclosureString ):
                        
                        v = vuln.vuln()
                        v.setURL( realurl )
                        v.setId( response.id )
                        v.setDesc( 'The URL : ' + v.getURL() + ' has a path disclosure problem. This is it: "' + match  + '". ')
                        v.setSeverity(severity.LOW)
                        v.setName( 'Path disclosure vulnerability' )
                        v['path'] = match
                        kb.kb.append( self, 'pathDisclosure', v )
        
        self._updateKBPathList( response.getURL() )
                        
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

            
    def _wasSent( self, request, pathDisclosureString ):
        '''
        Checks if the pathDisclosureString was sent in the request.
        '''
        url = urllib.unquote( request.getURI() )

        sentData = ''
        if request.getMethod().upper() == 'POST':
            sentData = request.getData()
            # This fixes bug #2012748
            if sentData != None:
                sentData = urllib.unquote( sentData )
            else:
                sentData = ''
        
        # This fixes bug #1990018
        # False positive with http://localhost/home/f00.html and
        # /home/user/
        path = urlParser.getPath(url)
        if pathDisclosureString[0:5] in path:
            return True

        if url.count( pathDisclosureString ) or sentData.count( pathDisclosureString ):
            return True

        # I didn't sent the pathDisclosureString in any way
        return False
        
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
        
        dirIndexStr = []
        dirIndexStr.append(r"[A-Z]:\\") 
        dirIndexStr.append("/root/")
        dirIndexStr.append("/var/")
        dirIndexStr.append("/htdocs/")
        dirIndexStr.append("/usr/")
        dirIndexStr.append("/home/")
        dirIndexStr.append("/etc/")
        dirIndexStr.append("/bin/")
        dirIndexStr.append("/lib/")
        dirIndexStr.append("/opt/")
        dirIndexStr.append("/sbin/")
        dirIndexStr.append("/sys/")
        dirIndexStr.append("/mnt/")
        dirIndexStr.append("/tmp/")
        return dirIndexStr

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
