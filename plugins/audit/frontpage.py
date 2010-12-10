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

import core.controllers.outputManager as om

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity
import core.data.kb.vuln as vuln

from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.data.bloomfilter.pybloom import ScalableBloomFilter

import core.data.parsers.urlParser as urlParser
from core.data.fuzzer.fuzzer import createRandAlpha
from core.controllers.w3afException import w3afException


class frontpage(baseAuditPlugin):
    '''
    Tries to upload a file using frontpage extensions (author.dll).
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = ScalableBloomFilter()
        self._stop_on_first = True

    def audit(self, freq ):
        '''
        Searches for file upload vulns using a POST to author.dll.
        
        @param freq: A fuzzableRequest
        '''
        # Set some value
        domain_path = urlParser.getDomainPath( freq.getURL() )
        
        # Start
        if self._stop_on_first and kb.kb.getData('frontpage', 'frontpage'):
            # Nothing to do, I have found vuln(s) and I should stop on first
            msg = 'Not verifying if I can upload files to: "' + domain_path + '" using author.dll'
            msg += '. Because I already found one vulnerability.'
            om.out.debug(msg)
        else:
            # I haven't found any vulns yet, OR i'm trying to find every
            # directory where I can write a file.
            if domain_path not in self._already_tested:
                om.out.debug( 'frontpage plugin is testing: ' + freq.getURL() )
                self._already_tested.add( domain_path )
                
                # Find a file that doesn't exist
                found404 = False
                for i in xrange(3):
                    randFile = createRandAlpha( 5 ) + '.html'
                    randPathFile = urlParser.urlJoin(domain_path,  randFile)
                    res = self._urlOpener.GET( randPathFile )
                    if is_404( res ):
                        found404 = True
                        break
                
                if found404:
                    upload_id = self._upload_file( domain_path,  randFile )
                    self._verify_upload( domain_path,  randFile,  upload_id )
                else:
                    msg = 'frontpage plugin failed to find a 404 page. This is mostly because of an'
                    msg += ' error in 404 page detection.'
                    om.out.error(msg)
            
    def _upload_file( self, domain_path,  randFile ):
        '''
        Upload the file using author.dll
        
        @parameter domain_path: http://localhost/f00/
        @parameter randFile: fj01afka.html
        '''
        file_path = urlParser.getPath(domain_path) + randFile
        
        # TODO: The frontpage version should be obtained from the information saved in the kb
        # by the discovery.frontpage_version plugin!
        # The 4.0.2.4715 version should be dynamic!
        # The information is already saved in the discovery plugin in the line:
        # i['version'] = version_match.group(1)
        content = "method=put document:4.0.2.4715&service_name=&document=[document_name="
        content += file_path
        content += ";meta_info=[]]&put_option=overwrite&comment=&keep_checked_out=false"
        content += '\n'
        # The content of the file I'm uploading is the file name reversed
        content += randFile[::-1]
        
        # TODO: The _vti_bin and _vti_aut directories should be PARSED from the _vti_inf file
        # inside the discovery.frontpage_version plugin, and then used here
        targetURL = urlParser.urlJoin( domain_path, '_vti_bin/_vti_aut/author.dll' )

        try:
            res = self._urlOpener.POST( targetURL , data=content )
        except w3afException,  e:
            om.out.debug('Exception while uploading file using author.dll: ' + str(e))
        else:
            if res.getCode() in [200]:
                msg = 'frontpage plugin seems to have successfully uploaded a file to'
                msg += ' the remote server.'
                om.out.debug(msg)
            return res.id
        
        return 200
            
    def _verify_upload(self,  domain_path,  randFile,  upload_id):
        '''
        Verify if the file was uploaded.
        
        @parameter domain_path: http://localhost/f00/
        @parameter randFile: The filename that was supposingly uploaded
        @parameter upload_id: The id of the POST request to author.dll
        '''        
        targetURL = urlParser.urlJoin( domain_path, randFile )
        
        try:
            res = self._urlOpener.GET( targetURL )
        except w3afException,  e:
            msg = 'Exception while verifying if the file that was uploaded using '
            msg += 'author.dll was there: ' + str(e)
            om.out.debug(msg)
        else:
            # The file I upload has blank content
            # And it must be there
            if res.getBody() == randFile[::-1] and not is_404( res ):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( targetURL )
                v.setId( [upload_id, res.id] )
                v.setSeverity(severity.HIGH)
                v.setName( 'Insecure Frontpage extensions configuration' )
                v.setMethod( 'POST' )
                msg = 'An insecure configuration in the frontpage extensions allows'
                msg += ' unauthenticated users to upload files to the remote web server.' 
                v.setDesc( msg )
                om.out.vulnerability(v.getDesc(), severity=v.getSeverity())
                kb.kb.append( self, 'frontpage', v )
            else:
                om.out.debug('The file that was uploaded using the POST method isn\'t there!')

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Stop on the first successfull file upload'
        h1 = 'The default value is usually a good idea, because if we can upload a file '
        h1 += 'to a directory, the chances are that we can upload to every directory;'
        h1 += ' and if this is the case, we would get a lot of vulnerabilities reported,'
        h1 += ' that are really only one.'
        o1 = option('stopOnFirst', self._stop_on_first, d1, 'boolean', help=h1)
        
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
        self._stop_on_first = optionsMap['stopOnFirst'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.frontpage_version']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin audits the frontpage extension configuration by trying to upload a file to the remote server
        using the author.dll script provided by FrontPage.
        '''
