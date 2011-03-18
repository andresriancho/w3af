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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity
import core.data.kb.vuln as vuln

from core.data.fuzzer.fuzzer import createMutants, createRandAlNum
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import w3afException

from core.controllers.misc.temp_dir import get_temp_dir
from core.controllers.coreHelpers.fingerprint_404 import is_404

import os.path
import tempfile


class fileUpload(baseAuditPlugin):
    '''
    Uploads a file and then searches for the file inside all known directories.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    _template_dir = os.path.join('plugins', 'audit', 'fileUpload')
    # User configured
    _extensions = ['gif', 'html', 'bmp', 'jpg', 'png', 'txt']

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal vars
        self._file_list = []

    def audit(self, freq ):
        '''
        Searches for file upload vulns.
        
        @param freq: A fuzzableRequest
        '''
        # Start
        if freq.getMethod().upper() == 'POST' and len ( freq.getFileVariables() ) != 0:
            om.out.debug( 'fileUpload plugin is testing: ' + freq.getURL() )
            
            # I do all this to be able to perform the enumerate() below
            for file_parameter in freq.getFileVariables():
                self._file_list = self._get_files()
                # Only file handlers are passed to the createMutants functions
                file_handlers = [ i[0] for i in self._file_list ]
                mutants = createMutants( freq, file_handlers, fuzzableParamList=[file_parameter, ] )

                for i, mutant in enumerate(mutants):
                    mutant.uploaded_file_name = self._file_list[i][1]
       
                for mutant in mutants:
                    targs = (mutant,)
                    self._tm.startFunction(target=self._sendMutant, 
                                            args=targs, ownerObj=self)
                    
            self._tm.join( self )
            
    def _get_files( self ):
        '''
        If the extension is in the templates dir, open it and return the handler.
        If the extension aint in the templates dir, create a file with random content, open it and return the handler.
        @return: A list of open files.
        '''
        result = []

        # All of this work is done in the "/tmp" directory:

        for ext in self._extensions:
            
            template_filename = 'template.' + ext
            if template_filename in os.listdir( self._template_dir ):
                
                #
                # Copy to "/tmp"
                #
                # Open target
                temp_dir = get_temp_dir()
                low_level_fd, file_name = tempfile.mkstemp(prefix='w3af_', suffix='.' + ext, dir=temp_dir)
                file_handler = os.fdopen(low_level_fd, "w+b")
                # Read source
                template_content = file( os.path.join(self._template_dir, template_filename)).read()
                # Write content to target
                file_handler.write(template_content)
                file_handler.close()
                
                # Open the target again:
                try:
                    file_handler = file( file_name, 'r')
                except:
                    raise w3afException('Failed to open temp file: "' + file_name  + '".')
                else:
                    path, file_name = os.path.split(file_name)
                    result.append( (file_handler, file_name) )
                    
            else:
                # I dont have a template for this file extension!
                temp_dir = get_temp_dir()
                low_level_fd, file_name = tempfile.mkstemp(prefix='w3af_', suffix='.' + ext, dir=temp_dir)
                file_handler = os.fdopen(low_level_fd, "w+b")
                file_handler.write( createRandAlNum(32) )
                file_handler.close()
                path, file_name = os.path.split(file_name)
                result.append( (file(file_name), file_name) )
        
        return result
        
    def _analyzeResult(self, mutant, mutant_response):
        '''
        Analyze results of the _sendMutant method. 
        
        In this case, check if the file was uploaded to any of the known directories,
        or one of the "default" ones like "upload" or "files".
        '''
        
        with self._plugin_lock:
            if self._hasNoBug('fileUpload', 'fileUpload', 
                              mutant.getURL(), mutant.getVar()):        
                
                # Gen expr for directories where I can search for the uploaded file
                domain_path_list = set(urlParser.getDomainPath(i) for i in 
                                       kb.kb.getData('urls' , 'urlList'))
        
                # Try to find the file!
                for url in domain_path_list:
                    for path in self._generate_paths(url, mutant.uploaded_file_name):
        
                        get_response = self._urlOpener.GET(path, useCache=False)
                        if not is_404(get_response):
                            # This is necesary, if I dont do this, the session
                            # saver will break cause REAL file objects can't 
                            # be picked
                            mutant.setModValue('<file_object>')
                            v = vuln.vuln(mutant)
                            v.setPluginName(self.getName())
                            v.setId([mutant_response.id, get_response.id])
                            v.setSeverity(severity.HIGH)
                            v.setName('Insecure file upload')
                            v['fileDest'] = get_response.getURL()
                            v['fileVars'] = mutant.getFileVariables()
                            msg = ('A file upload to a directory inside the '
                            'webroot was found at: ' + mutant.foundAt())
                            v.setDesc(msg)
                            kb.kb.append(self, 'fileUpload', v)
                            return
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._tm.join( self )
        self.printUniq( kb.kb.getData( 'fileUpload', 'fileUpload' ), 'VAR' )
        
        # Clean up
        for tmp_file, tmp_file_name in self._file_list:
            tmp_file.close()
        
    def _generate_paths(self, url, uploaded_file_name):
        '''
        @parameter url: A URL where the uploaded_file_name could be
        @parameter uploaded_file_name: The name of the file that was uploaded to the server
        @return: A list of paths where the file could be.
        '''
        tmp = ['uploads', 'upload', 'file', 'user', 'files', 'downloads', 
               'download', 'up', 'down']

        for default_path in tmp:
            for path in urlParser.getDirectories(url):
                possible_loc = path + default_path + '/'  + uploaded_file_name
                yield possible_loc
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Extensions that w3af will try to upload through the form.'
        h1 = 'When finding a form with a file upload, this plugin will try to upload a set of files'
        h1 += ' with the extensions specified here.'
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
