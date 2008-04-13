'''
webDiff.py

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

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
import core.data.kb.knowledgeBase as kb
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.w3afException import w3afException
from core.controllers.w3afException import w3afRunOnce
import os
import core.data.parsers.urlParser as urlParser
from os.path import isfile
from core.data.getResponseType import *
import os.path

class webDiff(baseDiscoveryPlugin):
    '''
    Compare a local directory with a remote URL path.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )  
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        # Internal variables
        self._run = True
        self._first = True
        self._fuzzableRequests = []
        self._notEq = []
        self._notEqContent = []
        self._eq = []
        self._eqContent = []
        
        # Configuration
        self._banUrl = ['asp','jsp','php']
        self._content = True
        self._localDir = ''
        self._remotePath = ''
        
    def discover(self, fuzzableRequest ):
        '''
        GET's local files one by one until done.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._run:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            om.out.debug( 'webDiff plugin is testing: ' + fuzzableRequest.getURL() )
            self._run = False
            self.is404 = kb.kb.getData( 'error404page', '404' )
                    
            if self._localDir != '' and self._remotePath != '':
                self._verifyHeadEnabled( fuzzableRequest.getURL() )
                os.path.walk( self._localDir, self._compareDir, None )
                self._generateReport()
                return self._fuzzableRequests
            else:
                raise w3afException('webDiff plugins: You have to configure the local and remote directory to compare.')
        return []
    
    def _generateReport( self ):
        '''
        Generates a report based on:
            - self._notEq
            - self._notEqContent
            - self._eq
            - self._eqContent
        '''
        if len( self._eq ):
            om.out.information('The following files exist in the local directory and in the remote server:')
            for file in self._eq:
                om.out.information('- '+ file)
        
        if len( self._eqContent ):
            om.out.information('The following files exist in the local directory and in the remote server and their contents match:')
            for file in self._eqContent:
                om.out.information('- '+ file)

        if len( self._notEq ):
            om.out.information('The following files exist in the local directory and NOT in the remote server:')
            for file in self._notEq:
                om.out.information('- '+ file)
        
        if len( self._notEqContent ):
            om.out.information('The following files exist in the local directory and in the remote server but their contents dont match:')
            for file in self._notEqContent:
                om.out.information('- '+ file)
                
        om.out.information('Match files: ' + str(len(self._eq)) + ' of ' + str( len(self._eq) + len(self._notEq) ) )
        om.out.information('Match contents: ' + str(len(self._eqContent)) + ' of ' + str( len(self._eqContent) + len(self._notEqContent) ) )

    def _compareDir( self, arg, dir, flist ):
        '''
        This function is the callback function called from os.path.walk, from the python
        help function:
        
        walk(top, func, arg)
            Directory tree walk with callback function.
        
            For each directory in the directory tree rooted at top (including top
            itself, but excluding '.' and '..'), call func(arg, dirname, fnames).
            dirname is the name of the directory, and fnames a list of the names of
            the files and subdirectories in dirname (excluding '.' and '..').  func
            may modify the fnames list in-place (e.g. via del or slice assignment),
            and walk will only recurse into the subdirectories whose names remain in
            fnames; this can be used to implement a filter, or to impose a specific
            order of visiting.  No semantics are defined for, or required of, arg,
            beyond that arg is always passed to func.  It can be used, e.g., to pass
            a filename pattern, or a mutable object designed to accumulate
            statistics.  Passing None for arg is common.

        '''
        if self._first:
            self._startPath = dir
            self._first = False
        
        dir2 = dir.replace( self._startPath,'' )
        path = self._remotePath
        if dir2 != '':
            path += dir2 + os.path.sep
        else:
            path += dir2
        
        for fname in flist:
            if isfile( dir + os.path.sep + fname ):
                url = urlParser.urlJoin( path, fname )
                response = self._easyGet( url )
            
                if not self.is404( response ):
                    if isTextOrHtml( response.getHeaders() ):
                        self._fuzzableRequests.extend( self._createFuzzableRequests( response ) )
                    self._checkContent( response, dir + os.path.sep + fname )
                    self._eq.append( url )
                else:
                    self._notEq.append( url )
        
    def _checkContent( self, response, file ):
        '''
        Check if the contents match.
        '''
        if self._content:
            if file.count('.'):
                extension = os.path.splitext( file )[1].replace('.', '')
                
                if extension not in self._banUrl:
                    try:
                        fd = open( file, 'r' )
                    except:
                        om.out.debug('Failed to open file: ' + file)
                    else:
                        if fd.read() == response.getBody():
                            self._eqContent.append( response.getURL() )
                        else:
                            self._notEqContent.append( response.getURL() )
                            
                        fd.close()
        
    def _easyGet( self, url ):
        '''
        An easy way to get a URL using HEAD or GET depending on available methods.
        '''
        response = None
        try:
            if self._headEnabled() and not self._content:
                response = self._urlOpener.HEAD( url, useCache=True )
            else:
                response = self._urlOpener.GET( url, useCache=True )
        except KeyboardInterrupt,e:
            raise e
        else:
            return response
    
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'When comparing, also compare the content of files.'
        o1 = option('content', str(self._content), d1, 'boolean')
        
        d2 = 'The local directory used in the comparison.'
        o2 = option('localDir', str(self._localDir), d2, 'string')

        d3 = 'The remote directory used in the comparison.'
        o3 = option('remotePath', str(self._remotePath), d3, 'string')

        d4 = 'When comparing content of two files, ignore files with this extensions.'
        o4 = option('banUrl', ','.join(self._banUrl), d4, 'list')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        ol.add(o4)
        return ol

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._content = optionsMap['content']
        self._banUrl = optionsMap['banUrl']
        self._remotePath = urlParser.getDomainPath( optionsMap['remotePath'] )
        self._localDir = optionsMap['localDir']

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return [ 'discovery.allowedMethods' ]
            
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

    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to do a diff of two directories, a local and a remote one. The idea is to 
        mimic the functionality implemented by the linux command "diff" when invoced with two
        directories.
        
        Four configurable parameter exist:
            - localDir
            - remotePath
            - banUrl
            - content
            
        This plugin will read the file list inside "localDir", and for each file it will request the same filename
        from the "remotePath", matches and failures are recorded and saved. The content of both files is
        checked only if "content" is setted to True and the file extension aint in the "banUrl" list.
        
        The "banUrl" list should be used to ban script extensions like ASP, PHP, etc.
        '''
