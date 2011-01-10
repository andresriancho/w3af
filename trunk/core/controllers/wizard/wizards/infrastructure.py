'''
infrastructure.py

Copyright 2008 Andres Riancho

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
from core.controllers.w3afException import w3afException
import core.controllers.outputManager as om
from core.controllers.wizard.wizard import wizard


class infrastructure(wizard):
    
    def __init__( self, w3af_core ):
        '''
        This method should be overwritten by the actual wizards, so they can define what questions they are
        going to ask.
        '''
        wizard.__init__( self, w3af_core )

        self._questionList = self._get_instances( ['infrastructure_1','infrastructure_2','infrastructure_3'
                                                ,'infrastructure_4','infrastructure_internet_1'] )
        
    def getWizardDescription(self):
        '''
        This method should be overwritten by the actual wizards.
        
        @return: A string that describes what the wizard will let you configure.
        '''
        return '''This wizard creates a scan profile that aims to identify the Web infrastructure
        of the target site.'''

    def getName(self):
        '''
        @return: The name of the wizard.
        '''
        return 'Infrastructure wizard'

