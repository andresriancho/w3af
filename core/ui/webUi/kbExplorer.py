# -*- coding: latin-1 -*-
'''
kbExplorer.py

Copyright 2007 Mariano Nuez Di Croce @ CYBSEC

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
# Import sapyto
import core.controllers.w3afCore
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
from core.ui.webUi.webMenu import webMenu

class kbExplorer(webMenu):
    '''
    This is web interface to the KnowledgeBase.
    
    @author: Mariano Nuez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        webMenu.__init__(self)
        self._refreshTime = 5000
    
    def makeMenu(self):
        '''
        This shows knowledgeBase, refreshing automatically
        '''
        # Now we made the menu out of the KB
        dkb = kb.kb.dump()
        header = '<html><head>'
        
        # Refresh js function
        #header += '<script>function refresh() { window.location.href = self.location.href; } setTimeout("refresh()",'+ str(self._refreshTime) +');</script>' 

        header +=  '<link rel="StyleSheet" href="css/tree.css" type="text/css"><SCRIPT src="javascripts/tree.js"></script><script src="javascripts/functions.js"></script>'
        header += '<script>var Tree = new Array;\n'
        body = header
        pCont = 0
        i = 0
        for plug in dkb.keys():
            body += 'Tree['+str(i)+'] = "'+str(i+1)+'|0|'+self.escape(plug)+'|#";\n'
            pCont = i + 1
            i += 1
            for key in dkb[plug]:
                value = dkb[plug][key]
                if isinstance(value, list):
                    valueList = [ str(x) for x in value ]
                    value = ','.join(valueList)
                body += 'Tree['+ str(i)+'] = "'+str(i+1)+'|'+str(pCont)+'|'+ key + ': ' + self.escape(str(value)) +'|#";\n'
                i += 1
        initJs = '</script>'
        
        initJs +='</head><body><div class="tree"><script>createTree(Tree);</script></div><body></html>'
        return body + initJs
