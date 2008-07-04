'''
fileUpload.py

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

from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
import os
import os.path
import shutil
import core.data.constants.severity as severity

class fileUpload(baseAuditPlugin):
    '''
    Uploads a file and then searches for the file inside all known directories.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        self.is404 = None
        
        # Internal vars
        self._templateDir = 'plugins' + os.path.sep + 'audit'+ os.path.sep + 'fileUpload'
        self._fnameList = []
        self._fileList = []
        
        # User configured
        self._extensions = ['gif','html']

    def _fuzzRequests(self, freq ):
        '''
        Searches for file upload vulns.
        
        @param freq: A fuzzableRequest
        '''
        # Init...
        if self.is404 == None:
            self.is404 = kb.kb.getData( 'error404page', '404' )
        
        # Start
        if freq.getMethod().upper() == 'POST':
            if len ( freq.getFileVariables() ) != 0:
                om.out.debug( 'fileUpload plugin is testing: ' + freq.getURL() )
                
                self._fileList = self._getFiles()
                mutants = createMutants( freq , self._fileList )
            
                for mutant in mutants:
                    if self._hasNoBug( 'fileUpload' , 'fileUpload' , mutant.getURL() , mutant.getVar() ) and\
                    mutant.getVar() in freq.getFileVariables():
                        # Only spawn a thread if the mutant has a modified variable
                        # that has no reported bugs in the kb
                        targs = (mutant,)
                        self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
            
    def _getFiles( self ):
        '''
        If the extension is in the templates dir, open it and return the handler.
        If the extension aint in the templates dir, create a file with random content, open it and return the handler.
        @return: A list of open files.
        '''
        result = []

        # Create a tmp directory
        dir = '.tmp' + os.path.sep
        try:
            if not os.path.exists( dir ):
                os.mkdir( dir )
        except:
            raise w3afException('Could not create '+ dir + ' directory.')

        for ext in self._extensions:
            filename = 'template.' + ext
            if filename in os.listdir( self._templateDir ):
                tmpFilename = createRandAlNum( 8 ) + '.' + ext
                shutil.copy( os.path.join( self._templateDir, filename ), os.path.join( dir , tmpFilename ) )
                try:
                    fd = file( os.path.join( dir , tmpFilename ) , 'r')
                except:
                    raise w3afException('Failed to open temp file: ' + tmpFilename )
                else:
                    result.append( fd )
                    self._fnameList.append( tmpFilename )
                    
            else:
                # I dont have a template for this file extension!
                fname = createRandAlNum( 8 ) + ext
                self._pathName = dir + fname
                try:
                    fd = file(  self._pathName , 'w' )
                    fd.write( self._pathName )
                except:
                    raise w3afException('Failed to create tmp file for upload.')
                else:
                    result.append( fd )
                    self._fnameList.append( fname )
        
        return result
        
    def _analyzeResult( self, mutant, response ):
        '''
        Analyze results of the _sendMutant method. In this case, check if the file was uploaded.
        '''
        for url in kb.kb.getData( 'urls' , 'urlList' ):
            for path in self._generatePaths( url ):
                response = self._urlOpener.GET( path, useCache=False )
                if not self.is404( response ):
                    # This is necesary, if I dont do this, the session saver will break cause
                    # REAL file objects can't be picked
                    mutant.setModValue( '<fileObject>' )
                    v = vuln.vuln( mutant )
                    v.setId( response.id )
                    v.setSeverity(severity.HIGH)
                    v.setName( 'Insecure file upload' )
                    v['fileDest'] = response.getURL()
                    v['fileVars'] = mutant.getFileVariables()
                    v.setDesc( 'A file upload to a directory inside the webroot was found at: ' + response.getURL() + ' . Using method: ' + v.getMethod() + '. The file was uploaded using this URL: '+ mutant.getURL() +' the data was: ' + str(mutant.getDc()) )
                    kb.kb.append( self, 'fileUpload', v )
                    return
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'fileUpload', 'fileUpload' ), 'VAR' )
        
        # Clean up
        for file in self._fileList:
            file.close()
            
        for file in self._fnameList:
            os.unlink( '.tmp'+ os.path.sep + file )     
        
    def _generatePaths( self, url ):
        tmp = []
        tmp.append('uploads')
        tmp.append('upload')
        tmp.append('file')
        tmp.append('user')
        tmp.append('files')
        tmp.append('downloads')
        tmp.append('download')
        tmp.append('up')
        tmp.append('down')
        
        res = []
        for r in tmp:
            for dir in urlParser.getDirectories( url ):
                for fname in self._fnameList:
                    r2 = dir + r + '/'  + fname
                    res.append( r2 )
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Extensions that w3af will try to upload'
        h1 = 'When finding a form with a file upload, this plugin will try to upload a set of files with the extensions specified here.'
        o1 = option('extensions', self._extensions, d1, 'list', help=h1)

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
        self._extensions = optionsMap['extensions'].getValue()

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
        This plugin will try to expoit insecure file upload forms.
        
        One configurable parameter exists:
            - extensions
        
        The extensions parameter is a comma separated list of extensions that this plugin will try to upload. Many web applications
        verify the extension of the file being uploaded, if special extensions are required, they can be added here.
    
        Some web applications check the contents of the files being uploaded to see if they are really what their extension
        is telling. To bypass this check, this plugin uses file templates located at "plugins/audit/fileUpload/", this templates
        are valid files for each extension that have a section ( the comment field in a gif file for example ) that can be replaced
        by scripting code ( PHP, ASP, etc ).
        
        After uploading the file, this plugin will try to find it on common directories like "upload" and "files" on every know directory.
        If the file is found, a vulnerability exists. 
        '''
