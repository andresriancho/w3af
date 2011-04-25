'''
wordpress_fingerprint.py

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

# Import options
import re

from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.w3afException import w3afException, w3afRunOnce
from core.controllers.coreHelpers.fingerprint_404 import is_404


# Main class
class wordpress_fingerprint(baseDiscoveryPlugin):
    '''
    Finds the version of a WordPress installation.
    @author: Ryan Dewhurst ( ryandewhurst@gmail.com ) www.ethicalhack3r.co.uk
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        self._version = None

    def discover(self, fuzzableRequest ):
        '''
        Finds the version of a WordPress installation.   
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
        (among other things) the URL to test.
        '''
        dirs = []
  
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:

            #########################
            ## Check if the server is running wp ##
            #########################
            
            self._fuzzableRequests = []  
            
            domain_path = fuzzableRequest.getURL().getDomainPath()
            
            # Main scan URL passed from w3af + unique wp file
            wp_unique_url = domain_path.urlJoin( 'wp-login.php' )
            response = self._urlOpener.GET( wp_unique_url, useCache=True )

            # If wp_unique_url is not 404, wordpress = true
            if not is_404( response ):
                dirs.extend( self._createFuzzableRequests( response ) )

                ##############################
                ## Check if the wp version is in index header ##
                ##############################
            
                # Main scan URL passed from w3af + wp index page
                wp_index_url = domain_path.urlJoin( 'index.php' )
                response = self._urlOpener.GET( wp_index_url, useCache=True )

                # Find the string in the response html
                find = '<meta name="generator" content="[Ww]ord[Pp]ress (\d\.\d\.?\d?)" />'
                m = re.search(find, response.getBody())

                # If string found, group version
                if m:
                    m = m.group(1)
                    self._version = m

                    # Save it to the kb!
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('WordPress version')
                    i.setURL( wp_index_url )
                    i.setId( response.id )
                    i.setDesc( 'WordPress version "'+ self._version +'" found in the index header.' )
                    kb.kb.append( self, 'info', i )
                    om.out.information( i.getDesc() )

                #########################
                ## Find wordpress version from data ##
                #########################

                # Wordpress version unique data, file/data/version
                self._wp_fingerprint = [ ('wp-includes/js/tinymce/tiny_mce.js','2009-05-25','2.8'), 
                        ('wp-includes/js/thickbox/thickbox.css','-ms-filter:','2.7.1'), 
                        ('wp-admin/css/farbtastic.css','.farbtastic','2.7'),
                        ('wp-includes/js/tinymce/wordpress.css','-khtml-border-radius:','2.6.1, 2.6.2, 2.6.3 or 2.6.5'),
                        ('wp-includes/js/tinymce/tiny_mce.js','0.7','2.5.1'),
                        ('wp-admin/async-upload.php','200','2.5'),
                        ('wp-includes/images/rss.png','200','2.3.1, 2.3.2 or 2.3.3'),
                        ('readme.html','2.3','2.3'),
                        ('wp-includes/rtl.css','#adminmenu a','2.2.3'),
                        ('wp-includes/js/wp-ajax.js','var a = $H();','2.2.1'),
                        ('wp-app.php','200','2.2')]

                for row in self._wp_fingerprint:
                    test_url = domain_path.urlJoin( row[0] )
                    response = self._urlOpener.GET( test_url, useCache=True )

                    if row[1] == '200' and not is_404(response):
                        self._version = row[2]
                        break
                    elif row[1] in response.getBody():
                        self._version = row[2]
                        break
                    else:
                        self._version = 'lower than 2.2'

                # Save it to the kb!
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('WordPress version')
                i.setURL( test_url )
                i.setId( response.id )
                i.setDesc( 'WordPress version "'+ self._version +'" found from data.' )
                kb.kb.append( self, 'info', i )
                om.out.information( i.getDesc() )

                # Only run once
                self._exec = False

        return dirs
  
    # W3af options and output    
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
        This plugin finds the version of a WordPress installation by fingerprinting it.

        It first checks whether or not the version is in the index header and then it checks for 
        the "real version" through the existance of files that are only present in specific versions.
        '''
