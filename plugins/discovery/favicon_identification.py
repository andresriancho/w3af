'''
favicon_identification.py

Copyright 2009 Vlatko Kosturjak
Plugin based on wordpress_fingerprint.py and pykto.py

More information to be found here:
    http://www.owasp.org/index.php/Category:OWASP_Favicon_Database_Project
    http://kost.com.hr/favicon.php

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
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin

import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln
import core.data.kb.info as info
import core.data.constants.severity as severity

from core.controllers.coreHelpers.fingerprint_404 import is_404
from core.controllers.w3afException import w3afException, w3afRunOnce

import re
import md5
import os.path


# Main class
class favicon_identification(baseDiscoveryPlugin):
    '''
    Identify server software using favicon.
    @author: Vlatko Kosturjak  <kost@linux.hr> http://kost.com.hr
    '''

    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        
        # Internal variables
        self._exec = True
        self._version = None

        # User configured parameters
        self._db_file = 'plugins' + os.path.sep + 'discovery' + os.path.sep + 'favicon'
        self._db_file += os.path.sep + 'favicon-md5'

    def discover(self, fuzzableRequest ):
        '''
        Identify server software using favicon.   
        @parameter fuzzableRequest: A fuzzableRequest instance that contains 
        (among other things) the URL to test.
        '''
        if not self._exec :
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
            
        else:
            
            # Only run once
            self._exec = False

            domain_path = fuzzableRequest.getURL().getDomainPath()
            
            def_favicon_url = domain_path.urlJoin('favicon.ico' )
            response = self._urlOpener.GET( def_favicon_url, useCache=True )

            if not is_404( response ):
                favmd5=md5.new(response.getBody()).hexdigest()

                try:
                    # read MD5 database.
                    db_file_1 = open(self._db_file, "r")
                except Exception, e:
                    raise w3afException('Failed to open the MD5 database. Exception: "' + str(e) + '".')
                else:
                    favicon_list = db_file_1.readlines()
                    db_file_1.close()
                
                desc = ''
                # check if MD5 is matched in database/list
                for fmd5 in favicon_list:
                    dbline=fmd5.split( ":", 2 );
                    md5part=dbline[0].split();
                    if dbline[0]==favmd5:
                        if len(dbline)>1:
                            favname=dbline[1].rstrip()
                            desc += 'Favicon.ico file was identified as "' + favname + '".'
                            break
                
                #
                #   Left here for debugging, but the final user doesn't really care about the md5
                #   of the favicon if it was not identified.
                #
                #desc += 'Favicon MD5: "'+ favmd5 +'".'
                
                if desc:
                    # Save it to the kb!
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Favicon identification')
                    i.setURL( def_favicon_url )
                    i.setId( response.id )
                    i.setDesc( desc )
                    kb.kb.append( self, 'info', i )
                    om.out.information( i.getDesc() )
                else:
                    #
                    #   Report to the kb that we failed to ID this favicon.ico and that the md5
                    #   should be sent to the developers.
                    #
                    i = info.info()
                    i.setPluginName(self.getName())
                    i.setName('Favicon identification failed')
                    i.setURL( def_favicon_url )
                    i.setId( response.id )
                    desc = 'Favicon identification failed, please send a mail to w3af-develop'
                    desc += '@lists.sourceforge.net including this md5 hash "'+favmd5+'"'
                    desc += ' and what server or Web application it represents. New fingerprints'
                    desc += ' make this plugin more powerfull and accurate.'
                    i.setDesc( desc )
                    kb.kb.append( self, 'info', i )
                    om.out.information( i.getDesc() )


        return []
  
    # w3af options and output    
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
        This plugin identifies software version using favicon.ico file.

        It checks MD5 of favicon against the MD5 database of favicons. See also: 
            http://www.owasp.org/index.php/Category:OWASP_Favicon_Database_Project
            http://kost.com.hr/favicon.php
        '''
