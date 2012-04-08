'''
htmlFile.py

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

from core.controllers.basePlugin.baseOutputPlugin import baseOutputPlugin
from core.controllers.w3afException import w3afException

import core.data.kb.knowledgeBase as kb
import core.data.constants.severity as severity
import core.data.kb.config as cf

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

import sys, os
import cgi
import time
import tempfile
import codecs

TITLE = 'w3af  -  Web Attack and Audit Framework - Vulnerability Report'


class htmlFile(baseOutputPlugin):
    '''
    Print all messages to a HTML file.
    
    @author: Juan Pablo Perez Etchegoyen ( jppereze@cybsec.com )
    '''
    def __init__(self):
        baseOutputPlugin.__init__(self)
        
        # Internal variables
        self._initialized = False
        self._style_filename = 'plugins' + os.path.sep + 'output' + os.path.sep
        self._style_filename += 'htmlFile' + os.path.sep +'style.css'        
        
        # These attributes hold the file pointers
        self._file = None
        self._aditional_info_fh = None        
        
        # User configured parameters
        self._verbose = False
        self._file_name = 'report.html'
    
    def _init( self ):
        '''
        Write messages to HTML file.
        '''
        self._initialized = True
        try:
            self._file = codecs.open( self._file_name, "w", "utf-8", 'replace' )            
            #self._file = open( self._file_name, "w" )
        except IOError, io:
            msg = 'Can\'t open report file "' + os.path.abspath(self._file_name) + '" for writing'
            msg += ': "' + io.strerror + '".'
            raise w3afException( msg )
        except Exception, e:
            msg = 'Can\'t open report file ' + self._file_name + ' for output.'
            msg += ' Exception: "' + str(e) + '".'
            raise w3afException( msg )
        
        try:
            style_file = open( self._style_filename, "r" )
        except:
            raise w3afException('Cant open style file ' + self._style_filename + '.')
        else:
            html = '<HTML>\n<HEAD>\n<TITLE>\n' +  cgi.escape ( TITLE ) + ' </TITLE>\n<meta'
            html += ' http-equiv="Content-Type" content="text/html; charset=UTF-8">\n'
            html += '<STYLE TYPE="text/css">\n<!--\n'
            self._write_to_file( html )
            self._write_to_file( style_file.read() )
            self._write_to_file('//-->\n</STYLE>\n</HEAD>\n<BODY BGCOLOR=white>\n')
            style_file.close()

        low_level_fd, self._aditional_info_fname = tempfile.mkstemp(prefix='w3af')
        self._aditional_info_fh = os.fdopen(low_level_fd, "w+b")

    def _write_to_file( self, msg ):
        '''
        Write msg to the file.
        
        @parameter msg: The message string.
        '''
        try:
            self._file.write( msg )
        except Exception, e:
            print 'An exception was raised while trying to write to the output file:', e
            sys.exit(1)
        
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for debug messages.
        '''
        if not self._initialized:
            self._init()
            
        if self._verbose:
            to_print = self._cleanString(message)
            to_print = cgi.escape(to_print)
            to_print = to_print.replace('\n', '<br/>')
            self._add_to_debug_table( to_print, 'debug' )
    
    def information(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for informational messages.
        '''
        pass

    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action for error messages.
        '''     
        if not self._initialized:
            self._init()
        
        to_print = self._cleanString(message)
        self._add_to_debug_table( cgi.escape(to_print), 'error' )

    def vulnerability(self, message , newLine=True, severity=severity.MEDIUM ):
        '''
        This method is called from the output object. The output object was called from a plugin
        or from the framework. This method should take an action when a vulnerability is found.
        '''     
        pass
    
    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the outside.
        '''
        if not self._initialized:
            self._init()
        to_print = self._cleanString(message)
        self._add_to_debug_table( cgi.escape(to_print), 'console' )
    
    def logEnabledPlugins(self,  plugins_dict,  options_dict):
        '''
        This method is called from the output manager object. This method should take an action
        for the enabled plugins and their configuration. Usually, write the info to a file or print
        it somewhere.
        
        @parameter pluginsDict: A dict with all the plugin types and the enabled plugins for that
                                               type of plugin.
        @parameter optionsDict: A dict with the options for every plugin.
        '''
        to_print = ''
        
        for plugin_type in plugins_dict:
            to_print += self._create_plugin_info( plugin_type, plugins_dict[plugin_type], 
                                                                    options_dict[plugin_type])
        
        # And now the target information
        str_targets = ', '.join( [u.url_string for u in cf.cf.getData('targets')] )
        to_print += 'target\n'
        to_print += '    set target ' + str_targets + '\n'
        to_print += '    back'
        
        to_print += '\n'
        to_print = to_print.replace('\n', '<br/>')
        to_print = to_print.replace(' ', '&nbsp;')
        
        self._add_to_debug_table('<i>Enabled plugins</i>:\n <br/><br/>' + to_print + '\n', 'debug' )
    
    def _add_to_debug_table(self, message, msg_type ):
        '''
        Add a message to the debug table.
        
        @parameter message: The message to add to the table. It's in HTML.
        @parameter msg_type: The type of message
        '''
        if self._aditional_info_fh is not None:
            now = time.localtime(time.time())
            the_time = time.strftime("%c", now)
        
            self._aditional_info_fh.write('<tr>')
            self._aditional_info_fh.write('<td class=content>' + the_time + '</td>')
            self._aditional_info_fh.write('<td class=content>' + msg_type + '</td>')
            self._aditional_info_fh.write('<td class=content>' + message + '</td>')
            self._aditional_info_fh.write('</tr>\n')
    
    def _create_plugin_info(self, plugin_type, plugins_list, plugins_options):
        '''
        @return: A string with the information about enabled plugins and their options.
        
        @parameter plugin_type: audit, discovery, etc.
        @parameter plugins_list: A list of the names of the plugins of plugin_type that are enabled.
        @parameter plugins_options: The options for the plugins
        '''
        response = ''
        
        # Only work if something is enabled
        if plugins_list:
            response = 'plugins\n'
            response += '    ' + plugin_type + ' ' + ', '.join(plugins_list) + '\n'
            
            for plugin_name in plugins_list:
                if plugins_options.has_key(plugin_name):
                    response += '    ' + plugin_type + ' config ' + plugin_name + '\n'
                    
                    for plugin_option in plugins_options[plugin_name]:
                        name = str(plugin_option.getName())
                        value = str(plugin_option.getValue())
                        response += '        set ' + name + ' ' + value + '\n'
                    
                    response += '        back\n'
            
            response += '    back\n'
            
        # The response
        return response
        
    def setOptions( self, OptionList ):
        '''
        Sets the Options given on the OptionList to self. The options are the result of a user
        entering some data on a window that was constructed using the XML Options that was
        retrieved from the plugin using getOptions()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self._file_name = OptionList['fileName'].getValue()
        self._verbose = OptionList['verbose'].getValue()
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'File name where this plugin will write to'
        o1 = option('fileName', self._file_name, d1, 'string')
        
        d3 = 'True if debug information will be appended to the report.'
        o3 = option('verbose', self._verbose, d3, 'boolean')
        
        ol = optionList()
        ol.add(o1)
        ol.add(o3)
        return ol

    def logHttp( self, request, response):
        '''
        Do nothing.
        '''
        pass

    def end (self ):
        '''
        This method is called when the scan has finished.
        '''
        # Just in case...
        if not self._initialized:
            self._init()
            
        #
        # Write the configuration table!
        #
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="30%">
                <tbody> <tr><td>
                <table cellpadding=2 cellspacing=1 border=0 width="100%">
                <td class=title colspan=3>w3af target URL's</td>
                </tr>
                <tr>
                    <td class=sub width="100%">URL</td>
                </tr>''')       

        # Writes the targets to the HTML
        for t in cf.cf.getData('targets'):
            self._write_to_file('''<tr><td class=default width="100%">''')
            self._write_to_file( cgi.escape( t.url_string ) + '<br/>\n')
            self._write_to_file('</td></tr>')

        self._write_to_file('</td></tr></tbody></table></td></tr></tbody></table><br>')

    
        #
        # Write info and vulns
        #
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">
                <tbody> <tr><td>
                <table cellpadding=2 cellspacing=1 border=0 width="100%">
                <td class=title colspan=3>Security Issues</td>
                </tr>
                <tr>
                    <td class=sub width="10%">Type</td>
                    <td class=sub width="10%">Port</td>
                    <td class=sub width="80%">Issue </td>
                </tr>''')       

        # Writes the vulnerability results Table
        vulns = kb.kb.getAllVulns()
        for i in vulns:
            
            #
            #   Get all the information I'll be using
            #
            if i.getURL() is not None:
                port = str( i.getURL().getPort() )
                port = 'tcp/' + port
                escaped_url = cgi.escape (i.getURL().url_string)
                
            else:
                # There is no URL associated with this vuln object
                port = 'Undefined'
                escaped_url = 'Undefined'
            
            self._write_to_file(
                '''<tr>
                <td valign=top class=default width="10%"><font color=red>Vulnerability</font></td>
                <td valign=top class=default width="10%">''' + port + '''</td>
                <td class=default width="80%">'''
                )

            desc = cgi.escape( i.getDesc() ) + '<br/><br/><b>URL :</b> '
            desc += escaped_url + '<br>\n'
            self._write_to_file( desc )

            if i.getSeverity() !=  None:
                self._write_to_file('Severity : ' + cgi.escape( i.getSeverity() ) +'<br> \n')
            self._write_to_file('</td></tr>')

        # Writes the Information results Table
        infos = kb.kb.getAllInfos()     
        for i in infos:

            #
            #   Get all the information I'll be using
            #
            if i.getURL() is not None:
                port = str( i.getURL().getPort() )
                port = 'tcp/' + port
                escaped_url = cgi.escape (i.getURL().url_string)
                
            else:
                # There is no URL associated with this vuln object
                port = 'Undefined'
                escaped_url = 'Undefined'

            self._write_to_file(
                '''<tr>
                    <td valign=top class=default width="10%">
                        <font color=blue>Information</font>
                    </td>
                    <td valign=top class=default width="10%">''' + port + '''</td>
                    <td class=default width="80%">'''
                )

            desc = cgi.escape( i.getDesc() ) + '<br>\n' + '<br/><b>URL :</b> '
            desc += escaped_url + '<br> \n </td></tr>'

            self._write_to_file( desc )

        # Close the upper table
        self._write_to_file('</td></tr></tbody></table></td></tr></tbody></table><br/>')
        self._write_to_file('\n\n')
        
        # Write debug information
        self._write_to_file(
            '''<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">
                <tbody> <tr><td>
                <table cellpadding=2 cellspacing=1 border=0 width="100%">
                <td class=title colspan=3>Security Issues</td>
                </tr>
                <tr>
                    <td class=sub width="20%">Time</td>
                    <td class=sub width="10%">Message type</td>
                    <td class=sub width="70%">Message</td>
                </tr>''')

        if self._aditional_info_fh is not None:
            self._aditional_info_fh.close()
            self._aditional_info_fh = None

        # I do this to avoid reading the whole file into
        # a string as I was doing before with something similar to:
        # foo = file( x ).read() ; write_to_file( foo )  
        for line in file( self._aditional_info_fname ):
            self._write_to_file( line )
        
        # Not sure why... but in some cases the file is not
        # present and this unlink fails, an example of this is
        # here https://sourceforge.net/apps/trac/w3af/ticket/171468
        try:
            os.unlink( self._aditional_info_fname )
        except OSError:
            pass
        
        # Close the debug table
        self._write_to_file('</td></tr></tbody></table></td></tr></tbody></table><br/>')
        self._write_to_file('\n\n')

        # Finish the report 
        self._write_to_file('</BODY>'+ '\n' + '</HTML>'+ '\n')
        
        # Close the file.
        if self._file is not None:
            self._file.close()
            
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to an HTML report file.
        
        Two configurable parameters exist:
            - fileName
            - verbose

        If you want to write every HTTP request/response to a text file, you should use the
        textFile plugin.
        '''
