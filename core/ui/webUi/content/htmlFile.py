# -*- coding: latin-1 -*-
'''
htmlFile.py

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

import cgi

class htmlFile:
    '''
    This is a class representing an HTML file.
    
    @author: Mariano Nuñez Di Croce <mnunez@cybsec.com>
    '''
    def __init__( self ):
        self._html = ''

    def write(self, content):
        self._html += content + '\n'
    
    def read(self):
        return self._html
    
    def addNL(self, count=1):
        '''
            Adds new line to the content
            @param count: How many new lines to add
        '''
        for i in range(0, count):
            self._html += '<br>\n'

    def format(self, defs):
        '''
            Formats the HTML file to include styling, etc
        '''
        '''
        header = '<html><head>'
        for css in defs['styles']:
            header += '<link rel="stylesheet" href="' + css + '">'
        for script in defs['jscripts']:
            header += '<script src="' + script + '"></script>'
        header += '</head><body class=bodyc>'
        '''
        header = ''
        footer = '\n</body></html>'
        self._html = header + self._html + footer
    
    def writeError( self, errorMsg ):
        self.write( '<div id="error">'+cgi.escape(errorMsg)+'</div>' )
        
        menu = '<div id="menuh" align="center">'
        menu += '<li><a href="javascript:history.back(1)" id="primero" >&lt;&lt;&nbsp;(back) Try again</a></li>'
        menu += '</div>'
        
        self.write( menu )

        
    def writePluginType(self, type):
        self.write('<input name="enableAll' + type + '" title="Click to enable all plugins of this type." type=checkbox class="confText" onclick=enableFamily("'+type+'");>' )
        self.write('<a href="javascript:;" onMouseDown="toggleDiv(\'divType-' + type + '\');" class=plugType>' + type + '</a>')
        self.write('<div id="divType-'+ type + '" style="display:none">')
    
    def writePluginName(self, name, type, desc):
        self.write('&nbsp;&nbsp;&nbsp;&nbsp;<input type=checkbox name="runPlugin-' + name + '-'+type+'" class=plugCheck>&nbsp;&nbsp;' )
        self.write('<a id="aPlug'+name+'" href="javascript:;" title="Click to configure"  onMouseDown="toggleDiv(\'divBase-' + name + '\');paint(\'aPlug'+name+'\');" class=plugName>' + name + '</a>')
    
    def writeConfigOptions(self, configurableObject, options, display=''):
        '''
        Writes a configurableObject Options, according to Option types, etc.
        '''
        name = cgi.escape( configurableObject.getName() )
        desc = cgi.escape( configurableObject.getDesc() )
        
        # handle long descriptions
        longDesc = None
        try:
            longDesc = cgi.escape( configurableObject.getLongDesc() )
        except:
            pass
        else:
            # Translate the text to "html"
            ld = ''
            for c in longDesc:
                if c == '\n':
                    ld += '<br/>'
                elif c == '\t':
                    ld += '&nbsp;' * 4
                else:
                    ld += c
            longDesc = ld
        
        # Hiding/Unhiding
        self.write('<div id="divBase-'+ name + '" style="display:'+display+'">')
        self.write("<table class=plugconfTable>")
        # print the description ( with the toogle for the long description if neccesary)
        if longDesc:
            self.write('\t<tr class=confTR>\n\t<td class=confTD colspan=2>\n\t<font class=plugDesc>' + desc + '</font><img src="images/question.gif" height=17px width=17px title="Show long description" onClick="toggleDiv(\'divLongDesc-' + name + '\');">\n\t</td>\n\t</tr>')
            # print the long description
            self.write('\t<tr style="display:none" id="divLongDesc-' + name + '" class=confTR>\n\t<td class=confTD colspan=2>\n\t<font class=plugDesc>' + longDesc + '</font>\n\t</td>\n\t</tr>')
        else:
            self.write('\t<tr class=confTR>\n\t<td class=confTD colspan=2>\n\t<font class=plugDesc>' + desc + '</font>\n\t</td>\n\t</tr>')
        
        
        for opt in options:
            type = cgi.escape( options[opt]['type'] )
            default = cgi.escape( options[opt]['default'] )
            desc = cgi.escape( options[opt]['desc'] )
            
            optName = configurableObject.getType() + '-' + name + '-' + opt
            
            if options[opt]['help'] != '':
                desc += '<br><i>Detailed help: </i>' + cgi.escape( options[opt]['help'] )
            if type == 'Boolean':
                check = ''
                if default == 'True':
                    check = 'checked="Yes"'
                input = '\t<input name="' + optName + '-default" type=checkbox class=confText '+check+' value="' + default + '" alt="' + desc + '">'
            else:
                input = '\t<input name="' + optName + '-default" type=text class=confText value="' + default + '" alt="' + desc + '">\n'
            self.write('\t<tr class=confTR>\n\t<td class=confTD>' +opt +':</td>\n\t<td class=confTD>' + input + '&nbsp;&nbsp;\n\t<img src="images/question.gif" height=17px width=17px title="' + desc + '" onClick="toggleDiv(\'divOptHelp-' + optName + '\');">')
            self.write('\t<input type="hidden" name="' + optName + '-type" value="' + type + '">')
            self.write('\t<input type="hidden" name="' + optName + '-desc" value="' + desc + '">\n\t</td>\n\t</tr>')
            self.write('\t<tr id="divOptHelp-' + optName +'" style="display:none">')
            self.write('\t<td class=confTD colspan=2><font class=optDesc>' + desc + '</font>\n\t</td>\n\t</tr>')
        self.write("</table>")
        self.write('</div>')

    def writeTypeEnd(self):
        self.write('</div>')
    
    def writeFormInit(self, formName, formMethod, formAction):
        self.write('<form name="' + formName + '" method="' + formMethod + '" action="' + formAction + '">')
    
    def writeTextInput(self, name, length, value=None):
        if value:
            self.write('<input type="text" name="'+name+'" size="'+str(length)+'" value="'+value+'">')
        else:
            self.write('<input type="text" name="'+name+'" size="'+str(length)+'">')
        
    def writeFormEnd(self):
        self.write('</form>')
    
    def writeSubmit(self, value):
        self.write('<input type=submit class="SubmitButton" value="'+ value +'">')
        
    def writeMessage(self, msg):
        '''
        Writes a HTML formated message
        '''
        self.write('<font class=message>' + msg + '</font>')
    
    def writeNextBackPage(self, nextName, nextUrl, backName, backUrl):
        '''
        Writes a link that can be used to go to the next page.
        This is used when the webUi is used like a wizard.
        '''
        menu = '<div id="menuh" align="center">'
        menu += '<li><a href="'+backUrl+'" id="primero">&lt;&lt;&nbsp;(back) '+backName+'</a></li>'
        menu += '<li><a href="'+ nextUrl + '">'+ nextName +' (next)&nbsp;&gt;&gt;</a></li>'
        menu += '</div>'
        self.write( menu )
        
    def zero( self ):
        '''
        Clears the document, this is used to start over.
        '''
        self._html = ''

    def fileInput( self, fileName, nameSize ):
        self.write('<input type="file" name="'+fileName+'" size="'+str(nameSize)+'">')
        ### TODO:
        # http://www.quirksmode.org/dom/inputfile.html
