'''
phpinfo.py

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
from core.controllers.w3afException import w3afException

from core.controllers.coreHelpers.fingerprint_404 import is_404

import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity
import core.data.kb.info as info
import re


class phpinfo(baseDiscoveryPlugin):
    '''
    Search PHP Info file and if it finds it will determine the version of PHP.
    @author: Viktor Gazdag ( woodspeed@gmail.com )
    '''
    
    '''
    CHANGELOG:
        Feb/17/2009- Added PHP Settings Audit Checks by Aung Khant (aungkhant[at]yehg.net)
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._analyzed_dirs = []
        self._has_audited = 0
        self._new_fuzzable_requests = []

    def discover(self, fuzzableRequest ):
        '''
        For every directory, fetch a list of files and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        self._new_fuzzable_requests = []

        for domain_path in fuzzableRequest.getURL().getDirectories():

            if domain_path not in self._analyzed_dirs:

                # Save the domain_path so I know I'm not working in vane
                self._analyzed_dirs.append( domain_path )

                # Work!
                for php_info_filename in self._get_PHP_infofile():

                    #   Send the requests using threads:
                    targs = ( domain_path, php_info_filename, )
                    self._tm.startFunction( target=self._check_and_analyze, args=targs , ownerObj=self )
            
                # Wait for all threads to finish
                self._tm.join( self )
                
        return self._new_fuzzable_requests

    def _check_and_analyze(self, domain_path, php_info_filename):
        '''
        Check if a php_info_filename exists in the domain_path.
        @return: None, everything is saved to the self._new_fuzzable_requests list.
        '''
        # Request the file
        php_info_url = domain_path.urlJoin( php_info_filename )
        try:
            response = self._urlOpener.GET( php_info_url, useCache=True )
            om.out.debug( '[phpinfo] Testing "' + php_info_url + '".' )
        except w3afException,  w3:
            msg = 'Failed to GET phpinfo file: "' + php_info_url + '".'
            msg += 'Exception: "' + str(w3) + '".'
            om.out.debug( msg )
        else:
            # Feb/17/2009 by Aung Khant:
            # when scanning phpinfo in window box
            # the problem is generating a lot of results
            # due to all-the-same-for-windows files phpVersion.php, phpversion.php ..etc
            # Well, how to solve it? 
            # Finding one phpinfo file is enough for auditing for the target
            # So, we report every phpinfo file found
            # but we do and report auditing once. Sounds logical?
            # 
            # Feb/17/2009 by Andres Riancho:
            # Yes, that sounds ok for me.
            
            # Check if it's a phpinfo file                        
            if not is_404( response ):
                
                # Create the fuzzable request
                self._new_fuzzable_requests.extend( self._createFuzzableRequests( response ) )
                
                '''
                |Modified|
                old: regex_str = 'alt="PHP Logo" /></a><h1 class="p">PHP Version (.*?)</h1>'
                new: regex_str = '(<tr class="h"><td>\n|alt="PHP Logo" /></a>)<h1 class="p">PHP Version (.*?)</h1>'
                
                by aungkhant - I've been seeing phpinfo pages which don't print php logo image. One example, ning.com.
                
                '''
                regex_str = '(<tr class="h"><td>\n|alt="PHP Logo" /></a>)<h1 class="p">PHP Version (.*?)</h1>'
                php_version = re.search(regex_str, response.getBody(), re.IGNORECASE)

                regex_str = 'System </td><td class="v">(.*?)</td></tr>'
                sysinfo = re.search(regex_str, response.getBody() , re.IGNORECASE)

                if (php_version and sysinfo):
                    v = vuln.vuln()
                    v.setPluginName(self.getName())
                    v.setId( response.id )
                    v.setName( 'phpinfo() file found' )
                    v.setSeverity(severity.MEDIUM)
                    v.setURL( response.getURL() )
                    desc = 'The phpinfo() file was found at: ' + v.getURL()
                    desc += '. The version of PHP is: "' + php_version.group(2)
                    desc += '" and the system information is: "' + sysinfo.group(1)
                    desc += '".'
                    v.setDesc( desc )
                    kb.kb.append( self, 'phpinfo', v )
                    om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
                    if (self._has_audited == 0):
                        self.audit_phpinfo(response)
                        self._has_audited = 1
                                
                                 
    def audit_phpinfo(self, response):
        '''
        Scan for insecure php settings
        @author: Aung Khant (aungkhant[at]yehg.net)
        @return none
        
        two divisions: vulnerable settings and useful informative settings
        
        '''        
        
        ##### [Vulnerable Settings] #####
        
        ### [register_globals] ###
        regex_str = 'register_globals</td><td class="v">(On|Off)</td>'
        register_globals = re.search(regex_str, response.getBody() , re.IGNORECASE)
        rg_flag = ''
        if register_globals:
            rg = register_globals.group(1)            
            if(rg == 'On'):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'register_globals: On' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::register_globals is on.'            
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
            else:
                rg_flag = 'info'
                rg_name =  'register_globals: Off'
                rg_desc = 'The phpinfo()::register_globals is off.'
              
        ### [/register_globals] ### 
        
        ### [allow_url_fopen] ###
        regex_str = 'allow_url_fopen</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_fopen = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if allow_url_fopen:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'allow_url_fopen: On' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::allow_url_fopen is enabled.'            
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )           
        ### [/allow_url_fopen] ###    
        
        ### [allow_url_include] ###
        regex_str = 'allow_url_include</td><td class="v">(On|<i>no value</i>)</td>'
        allow_url_include = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if allow_url_include:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'allow_url_include: On' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::allow_url_include is enabled.'            
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )           
        ### [/allow_url_include] ###      

        ### [display_errors] ###
        regex_str = 'display_errors</td><td class="v">(On|<i>no value</i>)</td>'
        display_errors = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if display_errors:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'display_errors: On' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::display_errors is enabled.'            
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )           
        ### [/display_errors] ###
        
        ### [expose_php] ###
        regex_str = 'expose_php</td><td class="v">(On|<i>no value</i>)</td>'
        expose_php = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if expose_php:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'expose_php: On' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::expose_php is enabled.'            
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )           
        ### [/expose_php] ###
        
        ### [lowest_privilege_test] ###
        regex_str = 'User/Group </td><td class="v">(.*?)\((\d.*?)\)/(\d.*?)</td>'
        lowest_privilege_test = re.search(regex_str, response.getBody() , re.IGNORECASE)
        lpt_flag = ''
        if lowest_privilege_test:
            lpt_uname = lowest_privilege_test.group(1)
            lpt_uid = lowest_privilege_test.group(2)
            lpt_uid = int(lpt_uid)
            lpt_gid = lowest_privilege_test.group(3) 
            if( lpt_uid < 99 or lpt_gid < 99 or re.match('root|apache|daemon|bin|operator|adm',lpt_uname,re.IGNORECASE)):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'lowest_privilege_test:fail' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'phpinfo()::PHP may be executing as a higher privileged group. '
                desc += 'Username: ' + lpt_uname + ', '
                desc += 'UserID: ' + str(lpt_uid) + ', '           
                desc += 'GroupID: ' + lpt_gid
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
            else:
                lpt_flag = 'info'
                lpt_name = 'privilege:' + lpt_uname
                lpt_desc = 'phpinfo()::PHP is executing under '
                lpt_desc += 'username: ' + lpt_uname + ', '
                lpt_desc += 'userID: ' + str(lpt_uid) + ', '           
                lpt_desc += 'groupID: ' + lpt_gid
        ### [/lowest_privilege_test] ###       

                
        ### [disable_functions] ###
        regex_str = 'disable_functions</td><td class="v">(.*?)</td>'
        disable_functions = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if disable_functions:
            secure_df = 8
            df = disable_functions.group(1)
            dfe = df.split(',')
            if(len(dfe) < secure_df):    
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'disable_functions:few' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::disable_functions are set to few.'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/disable_functions] ###
     
        ### [curl_file_support] ###
        regex_str = '<h1 class="p">PHP Version (\d).(\d).(\d)</h1>'
        curl_file_support = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if curl_file_support:
            php_major_ver = curl_file_support.group(1)            
            php_minor_ver = curl_file_support.group(2)            
            php_rev_ver = curl_file_support.group(3)
            
            current_ver = php_major_ver + '.' + php_minor_ver + '' + php_rev_ver
            current_ver = float(current_ver)
            php_major_ver = int(php_major_ver)
            php_minor_ver = int(php_minor_ver)
            php_rev_ver = int(php_rev_ver)           
            
            cv4check = float(4.44)
            cv5check = float(5.16)
            curl_vuln = 1
            
            if(php_major_ver == 4):                
                if (current_ver>=cv4check):
                    curl_vuln = 0
            elif (php_major_ver == 5):                
                if (current_ver >= cv5check):
                    curl_vuln = 0
            elif (php_major_ver >= 6):
                curl_vuln = 0
            else:
                curl_vuln = 0
            
            if(curl_vuln == 1):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'curl_file_support:not_fixed' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::cURL::file_support has a security hole present in this'
                desc += ' version of PHP allows the cURL functions to bypass safe_mode and'
                desc += ' open_basedir restrictions.  .'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/curl_file_support] ###

        ### [cgi_force_redirect] ###
        regex_str = 'cgi_force_redirect</td><td class="v">(.*?)</td>'
        cgi_force_redirect = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if cgi_force_redirect:
            utd = cgi_force_redirect.group(1) + ''
            if(utd != 'On'):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'cgi_force_redirect: Off' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::CGI::force_redirect is disabled.'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/cgi_force_redirect] ###

        ### [session_cookie_httponly] ###
        regex_str = 'session\.cookie_httponly</td><td class="v">(Off|no|0)</td>'
        session_cookie_httponly = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if session_cookie_httponly:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'session.cookie_httponly: Off' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::session.cookie_httponly is off.'
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/session_cookie_httponly] ###   
   
        ### [session_save_path] ###
        regex_str = 'session\.save_path</td><td class="v">(<i>no value</i>)</td>'
        session_save_path = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if session_save_path:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'session_save_path:Everyone' )
            v.setSeverity(severity.LOW)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::session.save_path may be set to world-accessible directory.'
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/session_save_path] ###

        ### [session_use_trans] ###
        regex_str = 'session\.use_trans</td><td class="v">(On)</td>'
        session_use_trans = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if session_use_trans:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'session_use_trans: On' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::session.use_trans is enabled. This makes session hijacking easier.'
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/session_use_trans] ###        

        ### [default_charset] ###
        regex_str = 'default_charset</td><td class="v">(Off|no|0)</td>'
        default_charset = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if default_charset:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'default_charset: Off' )
            v.setSeverity(severity.MEDIUM)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::default_charset is set to none. This makes PHP scripts vulnerable'
            desc += ' to variable charset encoding XSS.'
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/default_charset] ###

        ### [enable_dl] ###
        regex_str = 'enable_dl</td><td class="v">(On|Off)</td>'
        enable_dl = re.search(regex_str, response.getBody() , re.IGNORECASE)
        ed_flag = ''
        if enable_dl:
            rg = enable_dl.group(1)
            if(rg == 'On'):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'enable_dl: On' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::enable_dl is on.'            
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )
            else:
                ed_flag = 'info'
                ed_name =  'enable_dl: Off'                 
                ed_desc = 'The phpinfo()::enable_dl is off.'                            
        ### [/enable_dl] ###        
        
        ### [memory_limit] ###
        regex_str = 'memory_limit</td><td class="v">(\d.*?)</td>'
        memory_limit = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if memory_limit:
            secure_ml = 10;
            ml = memory_limit.group(1) + ''
            ml = ml.replace('M','')
            if(ml > secure_ml):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'memory_limit:high' )
                v.setSeverity(severity.MEDIUM)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::memory_limit is set to higher value (' + memory_limit.group(1) + ').'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/memory_limit] ###
        
        ### [post_max_size] ###
        regex_str = 'post_max_size</td><td class="v">(\d.*?)</td>'
        post_max_size = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if post_max_size:
            secure_pms = 20;
            pms = post_max_size.group(1) + ''
            pms = pms.replace('M','')
            pms = int(pms)
            if(pms > secure_pms):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'post_max_size:high' )
                v.setSeverity(severity.LOW)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::post_max_size is set to higher value (' + post_max_size.group(1) + ').'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/post_max_size] ###        

        ### [upload_max_filesize] ###
        regex_str = 'upload_max_filesize</td><td class="v">(\d.*?)</td>'
        upload_max_filesize = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if upload_max_filesize:
            secure_umf = 20;
            umf = upload_max_filesize.group(1) + ''
            umf = umf.replace('M','')
            umf = int(umf)
            if(umf > secure_umf):
                v = vuln.vuln()
                v.setPluginName(self.getName())
                v.setId( response.id )
                v.setName( 'post_max_size:high' )
                v.setSeverity(severity.LOW)
                v.setURL( response.getURL() )
                desc = 'The phpinfo()::upload_max_filesize is set to higher value (' + upload_max_filesize.group(1) + ').'
                v.setDesc( desc )
                kb.kb.append( self, 'phpinfo', v )
                om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/upload_max_filesize] ###
        
        ### [upload_tmp_dir] ###
        regex_str = 'upload_tmp_dir</td><td class="v">(<i>no value</i>)</td>'
        upload_tmp_dir = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if upload_tmp_dir:
            v = vuln.vuln()
            v.setPluginName(self.getName())
            v.setId( response.id )
            v.setName( 'upload_tmp_dir:Everyone' )
            v.setSeverity(severity.LOW)
            v.setURL( response.getURL() )
            desc = 'The phpinfo()::upload_tmp_dir may be set to world-accessible directory.'
            v.setDesc( desc )
            kb.kb.append( self, 'phpinfo', v )
            om.out.vulnerability( v.getDesc(), severity=v.getSeverity() )  
        ### [/upload_tmp_dir] ###
        


        
        ##### [/Vulnerable Settings] #####
        
        ##### [Useful Informative Settings] #####

        ### [privilege] ###
        if lpt_flag == 'info':
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName(lpt_name )            
            i.setURL( response.getURL() )                            
            i.setDesc( lpt_desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )
        ### [/privilege] ###    
        
        ### [register_globals]###
        if rg_flag=='info':
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName( rg_name )            
            i.setURL( response.getURL() )            
            i.setDesc( rg_desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )
        ### [/register_globals]###
        
        ### [enable_dl]###
        if ed_flag == 'info':
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName(ed_name )            
            i.setURL( response.getURL() )                            
            i.setDesc( ed_desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )        
        ### [/enable_dl]###
        
        ### [file_uploads] ###
        regex_str = 'file_uploads</td><td class="v">(On|<i>no value</i>)</td>'
        file_uploads = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if file_uploads:
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setName( 'file_uploads: On' )            
            i.setURL( response.getURL() )
            desc = 'The phpinfo()::file_uploads is enabled.'            
            i.setDesc( desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )
        ### [/file_uploads] ###       
        
        ### [magic_quotes_gpc] ###
        regex_str = 'magic_quotes_gpc</td><td class="v">(On|Off)</td>'
        magic_quotes_gpc = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if magic_quotes_gpc:
            mqg = magic_quotes_gpc.group(1)
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setURL( response.getURL() )
            if (mqg == 'On'):            
                i.setName( 'magic_quotes_gpc: On' )                            
                desc = 'The phpinfo()::magic_quotes_gpc is on.'
            else:
                i.setName( 'magic_quotes_gpc: Off' )                            
                desc = 'The phpinfo()::magic_quotes_gpc is off.'                
            i.setDesc( desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )               

        ### [/magic_quotes_gpc] ###
        
        ### [open_basedir] ###
        regex_str = 'open_basedir</td><td class="v">(.*?)</td>'
        open_basedir = re.search(regex_str, response.getBody() , re.IGNORECASE)
        
        if open_basedir:
            obd = open_basedir.group(1)
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setURL( response.getURL() )
            
            if(obd == '<i>no value</i>'):
                i.setName( 'open_basedir:disabled' )                            
                desc = 'The phpinfo()::open_basedir is not set.'            
                i.setDesc( desc )

            else:
                i.setName( 'open_basedir:enabled' ) 
                desc = 'The phpinfo()::open_basedir is set to '  + open_basedir.group(1) + '.'
                i.setDesc( desc )

        kb.kb.append( self, 'phpinfo', i )            
        om.out.information( i.getDesc() )        
        ### [/open_basedir] ###
        
        ### [session_hash_function] ###
        regex_str = 'session\.hash_function</td><td class="v">(.*?)</td>'
        session_hash_function = re.search(regex_str, response.getBody() , re.IGNORECASE)
        if session_hash_function:
            i = info.info()
            i.setPluginName(self.getName())
            i.setId( response.id )
            i.setURL( response.getURL() )
            if (session_hash_function.group(1) == 0 or session_hash_function.group(1) != 'no'):
                i.setName( 'session.hash_function:md5' )            
                desc = 'The phpinfo()::session.hash_function use md5 algorithm.' 
            else:
                i.setName( 'session.hash_function:sha' )            
                desc = 'The phpinfo()::session.hash_function use sha algorithm.'           
     
              
            i.setDesc( desc )
            kb.kb.append( self, 'phpinfo', i )            
            om.out.information( i.getDesc() )
        ### [/session_hash_function] ###
        
        ##### [/Useful Informative Settings] #####
    
    def _get_PHP_infofile( self ):
        '''
        @return: Filename of the php info file.
        '''
        res = []
        # TODO: If i'm scanning a windows system, do I really need to request case sensitive
        # filenames like phpversion and PHPversion ?
        
        # by aungkhant - I solved your todo.
        # if I detect windows, then remove redundant files
        identified_os = kb.kb.getData('fingerprint_os','operating_system_str')
        ios = ''
        if (len(identified_os) != 0):
            ios = identified_os[0]
        else:
            ios = cf.cf.getData('targetOS')
            
        
        if re.match('windows',ios,re.IGNORECASE):
            res.extend( ['phpinfo.php' , 'info.php','test.php?mode=phpinfo'] )
            res.extend( ['index.php?view=phpinfo','index.php?mode=phpinfo' , '?mode=phpinfo' , '?view=phpinfo'])
            res.extend( ['install.php?mode=phpinfo','INSTALL.php?mode=phpinfo'  ] )
            res.extend( ['admin.php?mode=phpinfo', 'phpversion.php'] )
            res.extend( ['test1.php', 'phpinfo1.php', 'info1.php'] )
            res.extend( ['x.php', 'xx.php', 'xxx.php'] )
        else:
            res.extend( ['phpinfo.php', 'PhpInfo.php','PHPinfo.php','PHPINFO.php', 'phpInfo.php' , 'info.php'])
            res.extend( ['test.php?mode=phpinfo','TEST.php?mode=phpinfo'] )
            res.extend( ['index.php?view=phpinfo','index.php?mode=phpinfo' , '?mode=phpinfo' ,'?view=phpinfo'])
            res.extend( ['install.php?mode=phpinfo','INSTALL.php?mode=phpinfo'  ] )
            res.extend( ['admin.php?mode=phpinfo', 'phpversion.php', 'phpVersion.php','PHPversion.php'] )
            res.extend( ['test1.php', 'phpinfo1.php', 'phpInfo1.php', 'info1.php'] )
            res.extend( ['x.php', 'xx.php', 'xxx.php'] )            
        
        return res

    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions( self, OptionList ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

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
        This plugin searches for the PHP Info file in all the directories and subdirectories that are sent as input
        and if it finds it will try to determine the version of the PHP. The PHP Info file holds information about 
        the PHP and the system (version, environment, modules, extensions, compilation options, etc). For 
        example, if the input is:
            - http://localhost/w3af/index.php
            
        The plugin will perform these requests:
            - http://localhost/w3af/phpinfo.php
            - http://localhost/phpinfo.php
            - ...
            - http://localhost/test.php?mode=phpinfo
        
        Once the phpinfo(); file is found the plugin also checks for probably insecure php settings
        and reports findings.
        '''

