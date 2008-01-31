'''
parseOptions.py

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

import re
from core.controllers.w3afException import w3afException
import xml.dom.minidom

def parseOptions( pluginName, optionsMap ):
    '''
    Parses options from the getOptionsXML() and returns a the parsed result.
    '''
    parsedOptions = {}
    
    for i in optionsMap.keys():
        type = optionsMap[i]['type']
        value = optionsMap[i]['default']
        res = None
        try:
            if type == 'integer':
                res = int(value)
            elif type == 'float':
                res = float(value)
            elif type == 'boolean':
                if value.lower() == 'true':
                    res = True
                else:
                    res = False
            elif type == 'list':
                # Yes, we are regex dummies
                value += ','
                res = re.findall('(".*?"|\'.*?\'|.*?),', value)
                if res != []:
                    res = [y.strip() for y in res if y != '']
                    
                    # Now I check for single and double quotes
                    for u in res:
                        if ( u.startswith('"') and u.endswith('"') ) or ( u.startswith("'") and u.endswith("'") ):
                            res.append( u[1:-1] )
                            res.remove( u )

                else:
                    raise ValueError
            elif type == 'string':
                res = str(value)
            else:
                raise w3afException('Unknown type: ' + type)
        except ValueError:
            raise w3afException('The variable "'+ i +'" has the following value: "' + value + '" and cannot be casted to "' + type + '".')
        else:
            parsedOptions[ i ] = res
    
    return pluginName, parsedOptions

def parseXML( xmlString ):
    '''
    Parses the XML Options from a plugin.
    '''
    options = {}
    xmlString.replace( '\t' , '' )
    xmlDoc = xml.dom.minidom.parseString( xmlString )
    
    def setParameter( optionName, tag ):
        try:
            options[ optionName ][ tag ] = option.getElementsByTagName(tag)[0].childNodes[0].data
        except:
            options[ optionName ][ tag ] = ''
            
    for option in xmlDoc.getElementsByTagName('Option'):
        # I'm inside an option tag
        '''
        <Option name="checkPersistent">
            <default>True</default>
            <desc>Search persistent</desc>
            <type>Boolean</type>
        </Option>
        '''
        optionName = option.getAttribute('name')
        options[ optionName ] = {}
        
        setParameter( optionName, 'default' )
        setParameter( optionName, 'desc' )
        setParameter( optionName, 'help' )
        setParameter( optionName, 'type' )
        setParameter( optionName, 'required' )
        
    xmlDoc.unlink()
    return options
    
