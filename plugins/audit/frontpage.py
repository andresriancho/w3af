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

import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity
import core.data.kb.vuln as vuln

from core.controllers.w3afException import w3afException
from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin

from core.data.bloomfilter.bloomfilter import scalable_bloomfilter
from core.data.fuzzer.fuzzer import createRandAlpha
from core.data.options.option import option
from core.data.options.optionList import optionList


class frontpage(baseAuditPlugin):
    '''
    Tries to upload a file using frontpage extensions (author.dll).
    
    @author: Andres Riancho (andres.riancho@gmail.com)
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._already_tested = scalable_bloomfilter()
        self._stop_on_first = True

    def audit(self, freq ):
        '''
        Searches for file upload vulns using a POST to author.dll.
        
        @param freq: A fuzzable_request
        '''
        domain_path = freq.getURL().getDomainPath()
        
        if self._stop_on_first and kb.kb.getData(self, 'frontpage'):
            # Nothing to do, I have found vuln(s) and I should stop on first
            msg = 'Not verifying if I can upload files to: "' + domain_path
            msg += '" using author.dll. Because I already found one vulnerability.'
            om.out.debug(msg)
            return
        
        # I haven't found any vulns yet, OR i'm trying to find every
        # directory where I can write a file.
        if domain_path not in self._already_tested:
            self._already_tested.add( domain_path )
            
            # Find a file that doesn't exist and then try to upload it
            for _ in xrange(3):
                rand_file = createRandAlpha( 5 ) + '.html'
                rand_path_file = domain_path.urlJoin(rand_file)
                res = self._uri_opener.GET( rand_path_file )
                if is_404( res ):
                    upload_id = self._upload_file( domain_path,  rand_file )
                    self._verify_upload( domain_path,  rand_file,  upload_id )
                    break
            else:
                msg = 'frontpage plugin failed to find a 404 page. This is'
                msg += ' mostly because of an error in 404 page detection.'
                om.out.error(msg)
            
    def _upload_file( self, domain_path,  rand_file ):
        '''
        Upload the file using author.dll
        
        @parameter domain_path: http://localhost/f00/
        @parameter rand_file: fj01afka.html
        '''
        file_path = domain_path.getPath() + rand_file
        
        # TODO: The frontpage version should be obtained from the information saved in the kb
        # by the infrastructure.frontpage_version plugin!
        # The 4.0.2.4715 version should be dynamic!
        # The information is already saved in the crawl plugin in the line:
        # i['version'] = version_match.group(1)
        content = "method=put document:4.0.2.4715&service_name=&document=[document_name="
        content += file_path
        content += ";meta_info=[]]&put_option=overwrite&comment=&keep_checked_out=false"
        content += '\n'
        # The content of the file I'm uploading is the file name reversed
        content += rand_file[::-1]
        
        # TODO: The _vti_bin and _vti_aut directories should be PARSED from the _vti_inf file
        # inside the infrastructure.frontpage_version plugin, and then used here
        target_url = domain_path.urlJoin( '_vti_bin/_vti_aut/author.dll' )

        try:
            res = self._uri_opener.POST( target_url , data=content )
        except w3afException,  e:
            om.out.debug('Exception while uploading file using author.dll: ' + str(e))
        else:
            if res.getCode() in [200]:
                msg = 'frontpage plugin seems to have successfully uploaded a file to'
                msg += ' the remote server.'
                om.out.debug(msg)
            return res.id
        
        return 200
            
    def _verify_upload(self,  domain_path,  rand_file,  upload_id):
        '''
        Verify if the file was uploaded.
        
        @parameter domain_path: http://localhost/f00/
        @parameter rand_file: The filename that was supposingly uploaded
        @parameter upload_id: The id of the POST request to author.dll
        '''        
        target_url = domain_path.urlJoin( rand_file )
        
        try:
            res = self._uri_opener.GET( target_url )
        except w3afException,  e:
            msg = 'Exception while verifying if the file that was uploaded using'
            msg += ' author.dll was there: ' + str(e)
            om.out.debug(msg)
        else:
            # The file we uploaded has the reversed filename as body 
            if res.getBody() == rand_file[::-1] and not is_404( res ):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setURL( target_url )
                v.setId( [upload_id, res.id] )
                v.setSeverity(severity.HIGH)
                v.setName( 'Insecure Frontpage extensions configuration' )
                v.setMethod( 'POST' )
                msg = 'An insecure configuration in the frontpage extensions'
                msg += ' allows unauthenticated users to upload files to the'
                msg += ' remote web server.' 
                v.setDesc( msg )
                om.out.vulnerability(v.getDesc(), severity=v.getSeverity())
                kb.kb.append( self, 'frontpage', v )
            else:
                msg = 'The file that was uploaded using the POST method is not'
                msg += ' present on the remote web server at %s' % target_url
                om.out.debug( msg )

    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = optionList()
        
        d = 'Stop on the first successful file upload'
        h = 'The default value is usually a good idea, because if we can upload a file '
        h += 'to a directory, the chances are that we can upload to every directory;'
        h += ' and if this is the case, we would get a lot of vulnerabilities reported,'
        h += ' that are really only one.'
        o = option('stopOnFirst', self._stop_on_first, d, 'boolean', help=h)
        ol.add(o)
        
        return ol

    def set_options( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of get_options().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._stop_on_first = optionsMap['stopOnFirst'].getValue()

    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['infrastructure.frontpage_version']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin audits the frontpage extension configuration by trying to
        upload a file to the remote server using the author.dll script provided
        by FrontPage.
        '''
