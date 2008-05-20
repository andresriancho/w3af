'''
frontpage.py

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

from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.kb.vuln as vuln
import core.data.parsers.urlParser as urlParser
import core.data.constants.severity as severity

class frontpage(baseAuditPlugin):
    '''
    Tries to upload a file using frontpage extensions (author.dll).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self.is404 = None
        self._alreadyTested = []
        self._stopOnFirst = True
        

    def _fuzzRequests(self, freq ):
        '''
        Searches for file upload vulns using a POST to author.dll.
        
        @param freq: A fuzzableRequest
        '''
        # Init...
        if self.is404 == None:
            self.is404 = kb.kb.getData( 'error404page', '404' )

        # Set some value
        domainPath = urlParser.getDomainPath( freq.getURL() )
        
        # Start
        if self._stopOnFirst and kb.kb.getData('frontpage', 'fileUpload'):
            # Nothing to do, I have found vuln(s) and I should stop on first
            om.out.debug('Not verifying if I can upload files to: "' + domainPath + '" using author.dll')
        else:
            # I haven't found any vulns yet, OR i'm trying to find every directory where I can write a file.
            if domainPath not in self._alreadyTested:
                om.out.debug( 'frontpage plugin is testing: ' + freq.getURL() )
                self._alreadyTested.append( domainPath )
                
                # Find a file that doesn't exist
                found404 = False
                for i in xrange(3):
                    randFile = createRandAlpha( 5 ) + '.html'
                    randPathFile= urlParser.urlJoin(domainPath,  randFile)
                    res = self._urlOpener.GET( randPathFile )
                    if self.is404( res ):
                        found404 = True
                        break
                
                if found404:
                    uploadId = self._uploadFile( domainPath,  randFile )
                    self._verifyUpload( domainPath,  randFile,  uploadId )
                else:
                    om.out.error('frontpage plugin failed to find a 404 page. This is mostly because of an error in 404 page detection.')
            
    def _uploadFile( self, domainPath,  randFile ):
        '''
        Upload the file using author.dll
        @parameter domainPath: http://localhost/f00/
        @parameter randFile: fj01afka.html
        '''
        filePath = urlParser.getPath(domainPath) + randFile
        
        content = "method=put document:4.0.2.4715&service_name=&document=[document_name="
        content += filePath
        content +=";meta_info=[]]&put_option=overwrite&comment=&keep_checked_out=false"
        
        targetURL = urlParser.urlJoin( domainPath, '_vti_bin/_vti_aut/author.dll' )

        try:
            res = self._urlOpener.POST( targetURL , data=content )
        except w3afException,  e:
            om.out.debug('Exception while uploading file using author.dll: ' + str(e))
        else:
            if res.getCode() in [200]:
                om.out.debug('frontpage plugin seems to have successfully uploaded a file to the remote server.')
                return res.id
        
        return None
            
    def _verifyUpload(self,  domainPath,  randFile,  id):
        targetURL = urlParser.urlJoin( domainPath, randFile )
        
        try:
            res = self._urlOpener.GET( targetURL )
        except w3afException,  e:
            om.out.debug('Exception while verifying if the file that was uploaded using author.dll was there: ' + str(e))
        else:
            # The file I upload has blank content
            # And it must be there
            if res.getBody() == '' and not self.is404( res ):
                v = vuln.vuln()
                v.setURL( targetURL )
                v.setId( id )
                v.setSeverity(severity.HIGH)
                v.setName( 'Insecure Frontpage extensions configuration' )
                v.setMethod( 'POST' )
                v.setDesc( 'An insecure configuration in the frontpage extensions allows unauthenticated users to upload files to the remote web server.' )
                om.out.vulnerability(v.getDesc(), severity=v.getSeverity())
                kb.kb.append( self, 'fileUpload', v )
            else:
                om.out.debug('The file that was uploaded using the POST method isn\'t there!')

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Stop on the first successfull file upload'
        h1 = 'The default value is usually a good idea, because if we can upload a file to a directory, the chances are that we can upload to every directory; and if this is the case, we would get a lot of vulnerabilities reported, that are really only one.'
        o1 = option('stopOnFirst', self._stopOnFirst, d1, 'string', help=h1)
        
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
        self._stopOnFirst = optionsMap['stopOnFirst'].getValue()

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
        This plugin will audits the frontpage extension configuration by trying to upload a file to the remote server using the author.dll program.
        '''
