# -*- coding: latin-1 -*-
'''
plugins.py

Copyright 2007 Mariano Nuñez Di Croce @ CYBSEC

This file is part of sapyto, http://www.cybsec.com/EN/research/tools/sapyto.php

sapyto is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

sapyto is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with sapyto; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

import core.controllers.w3afCore as core
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
from core.ui.webUi.webMenu import webMenu
import re

class plugins(webMenu):
    '''
    This is the plugins configuration menu for the web ui.
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        webMenu.__init__(self)
        self._w3afCore = core.wCore
        self._plugins = {}

    def makeMenu(self):
        # Clear the document
        self._content.zero()
        self._content.addNL(3)
        
        # Write the plugin that enables a complete plugin family
        self._content.write('''
        <script type="text/javascript">
        <!--//
        function endsWith(str, s){
            var reg = new RegExp(s + "$");
            return reg.test(str);
        }

        function enableFamily( family ){
            var obj = document.forms[0];
            var j = 0;
            
            for(var i=0; i<obj.elements.length; i++){
                if ( endsWith( obj.elements[i].name, family ) ){
                    if ( j==0){
                        j = 1;
                    }else{
                        if( obj.elements[i].checked==true ){
                            obj.elements[i].checked = false;
                        }else{
                            obj.elements[i].checked = true;
                        }
                    }
                }
            }
        }
        // -->
        </script>
        ''')
        
        # Make a menu with all the registered plugin types
        self._content.writeFormInit('plugins','POST','plugins.py')
        plugTypes = self._w3afCore.getPluginTypes()
        for type in plugTypes:
            self._content.writePluginType(self.escape(type))
            for pluginName in self._w3afCore.getPluginList(type):
                # We need to instantiate the plugin to get its options.
                plugInst = self._w3afCore.getPluginInstance(pluginName, type)
                self._content.writePluginName(self.escape(pluginName), self.escape(type), self.escape(plugInst.getDesc()))
                self._content.addNL()
                options = self.parseXML(plugInst.getOptionsXML())
                self._content.writeConfigOptions(plugInst, options, 'none')
            self._content.writeTypeEnd()
            self._content.addNL(2)
        self._content.addNL(2)
        self._content.writeSubmit('Save')
        self._content.writeFormEnd()
        self.format()
        return self._content.read()
    
    def parsePOST(self, postData):
        '''
        This method is used to parse the POSTed options of the Plugins configuration menu.
        It will configure plugins and set them for execution.
        '''
        # Clear the document
        self._content.zero()

        plugTypes = self._w3afCore.getPluginTypes()
        for type in plugTypes:
            self._plugins[type] = []
            for pluginName in self._w3afCore.getPluginList(type):
                # Check if plugin was set for execution
                plugCheck = 'runPlugin-' + pluginName + '-' + type
                if plugCheck in postData.keys():
                    # Instantiate it to get its options
                    plugInst = self._w3afCore.getPluginInstance(pluginName, type)
                    pluginOptions = self.parseXML(plugInst.getOptionsXML())
                    options4plugin = {}
                    for opt in pluginOptions:
                        if not opt in options4plugin.keys():
                            options4plugin[opt] = {}
                        # Grab fields dynamically.
                        optField =  type + '-' + pluginName + '-' + opt 
                        optRegex = optField + '-(.*?)\ '                        
                        res = re.findall(optRegex, ' '.join(postData.keys()) + ' ') # Regex dummies till death!
                        for field in res:
                            options4plugin[opt][field]= postData[optField + '-' + field][0]                         
                    # Check for Boolean options
                    for opt in options4plugin:
                        if options4plugin[opt]['type'] == 'Boolean':
                            if not 'default' in options4plugin[opt].keys():
                                # If fails, is because checkbox was not sent, so unchecked, so False
                                options4plugin[opt]['default'] = 'False'
                            else:
                                options4plugin[opt]['default'] = 'True'
                                
                    #FIXME: Pass options better!
                    self._w3afCore.setPluginOptions( type, pluginName, options4plugin )
                    om.out.setPluginOptions( pluginName, options4plugin )
                    # Add to temp execution pool
                    self._plugins[type].append(pluginName)
            
            # Just in case, we add the webOutput
            if type == 'output' and 'webOutput' not in self._plugins[type]:
                self._plugins[type].append('webOutput')
                
            # Add to core execution pool
            self._w3afCore.setPlugins(self._plugins[type], type)
        
        self._content.writeMessage('<div id="text">Plugins successfully configured.</div>')
        self._content.writeNextBackPage('Target', 'targets.py', 'Session', 'session.py')
        
        return self._content.read()
