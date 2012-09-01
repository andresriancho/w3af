'''
html_file.py

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
import os
import sys
import cgi
import time
import codecs

from string import Template

import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import core.data.kb.vuln as vuln

from core.controllers.plugins.output_plugin import OutputPlugin
from core.controllers.w3afException import w3afException
from core.data.db.disk_list import disk_list
from core.data.options.option import option
from core.data.options.option_list import OptionList


TITLE = 'w3af  -  Web Attack and Audit Framework - Vulnerability Report'

HTML_HEADER = Template( '<!DOCTYPE html>\n<html>\n<head>\n<title>$title</title>\n'
            '<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />\n' 
            '<style type="text/css">\n<!--\n$css-->\n</style>\n</head>\n'
            '<body bgcolor=white>\n' )


class html_file(OutputPlugin):
    '''
    Generate HTML report with identified vulnerabilities and log messages.
    
    @author: Andres Riancho ((andres.riancho@gmail.com))
    '''
    def __init__(self):
        OutputPlugin.__init__(self)
        
        # Internal variables
        self._initialized = False
        self._style_filename = os.path.join('plugins', 'output', 
                                            'html_file','style.css' )        
        
        # These attributes hold the file pointers
        self._file = None
        self._aditional_info = disk_list()
        
        # User configured parameters
        self._verbose = False
        self._file_name = 'report.html'
    
    def _init( self ):
        '''
        Write messages to HTML file.
        '''
        if not self._initialized: 
            self._initialized = True
            try:
                self._file = codecs.open( self._file_name, "w", "utf-8", 'replace' )            
                #self._file = open( self._file_name, "w" )
            except IOError, io:
                msg = 'Can\'t open report file "%s" for writing: "%s"'
                msg = msg % (os.path.abspath(self._file_name), io.strerror)
                raise w3afException( msg )
            except Exception, e:
                msg = 'Can\'t open report file "%s" for writing: "%s"'
                msg = msg % (os.path.abspath(self._file_name), e)
                raise w3afException( msg )
            
            try:
                style_file = open( self._style_filename, "r" )
            except Exception, e:
                msg = 'Can\'t open CSS style file "%s" for reading: "%s"'
                msg = msg % (os.path.abspath(self._style_filename), e)
                raise w3afException( msg )
            else:
                html = HTML_HEADER.substitute(title=cgi.escape (TITLE),
                                              css=style_file.read())
                self._write_to_file( html )
    
    def _write_to_file( self, *msg_list ):
        '''
        Write all parameters to the output file.
        
        @parameter msg_list: The messages (strings) to write to the file.
        '''
        for msg in msg_list:
            try:
                self._file.write( msg + '\n' )
            except Exception, e:
                msg = 'An exception was raised while trying to write to the'
                msg += ' output file in output.html_file: "%s"' % e
                print msg
                sys.exit(1)
    
    def debug(self, message, newLine = True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for debug messages.
        '''
        self._init()
        
        if self._verbose:
            to_print = self._clean_string(message)
            to_print = cgi.escape(to_print)
            to_print = to_print.replace('\n', '<br />')
            self._add_to_debug_table( to_print, 'debug' )
    
    
    def do_nothing(self, *args, **kwds): pass
    information = vulnerability = do_nothing
    
    def error(self, message , newLine = True ):
        '''
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for error messages.
        '''
        self._init()             
        to_print = self._clean_string(message)
        self._add_to_debug_table( cgi.escape(to_print), 'error' )


    def console( self, message, newLine = True ):
        '''
        This method is used by the w3af console to print messages to the
        outside.
        '''
        self._init()
        to_print = self._clean_string(message)
        self._add_to_debug_table( cgi.escape(to_print), 'console' )
    
    def log_enabled_plugins(self,  plugins_dict,  options_dict):
        '''
        This method is called from the output manager object. This method 
        should take an action for the enabled plugins and their configuration.
        Usually, write the info to a file or print it somewhere.
        
        @parameter pluginsDict: A dict with all the plugin types and the 
                                enabled plugins for that type of plugin.
        @parameter optionsDict: A dict with the options for every plugin.
        '''
        to_print = ''
        
        for plugin_type in plugins_dict:
            to_print += self._create_plugin_info( plugin_type, 
                                                  plugins_dict[plugin_type], 
                                                  options_dict[plugin_type])
        
        # And now the target information
        str_targets = ', '.join( [u.url_string for u in cf.cf.get('targets')] )
        to_print += 'target\n'
        to_print += '    set target ' + str_targets + '\n'
        to_print += '    back'
        
        to_print += '\n'
        to_print = to_print.replace('\n', '<br />')
        to_print = to_print.replace(' ', '&nbsp;')
        
        self._add_to_debug_table('<i>Enabled plugins</i>:\n <br /><br />' + to_print + '\n', 'debug' )
    
    def _add_to_debug_table(self, message, msg_type ):
        '''
        Add a message to the debug table.
        
        @parameter message: The message to add to the table. It's in HTML.
        @parameter msg_type: The type of message
        '''
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        
        msg = '<tr><td class=content>%s</td><td class=content>%s</td>' \
              '<td class=content>%s</td></tr>'
        self._aditional_info.append( msg % (the_time, msg_type, message) )
            
    def set_options( self, option_list ):
        '''
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using get_options()
        
        This method MUST be implemented on every plugin. 
        
        @return: No value is returned.
        ''' 
        self._file_name = option_list['fileName'].getValue()
        self._verbose = option_list['verbose'].getValue()
        
    def get_options( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        ol = OptionList()
        
        d = 'File name where this plugin will write to'
        o = option('fileName', self._file_name, d, 'string')
        ol.add(o)
        
        d = 'True if debug information will be appended to the report.'
        o = option('verbose', self._verbose, d, 'boolean')
        ol.add(o)
        
        return ol

    def end (self ):
        '''
        This method is called when the scan has finished.
        '''
        self._init()
                
        self._write_to_file(
            '<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="30%">',
            '<tbody>',
            '<tr><td>',
            '<table cellpadding=2 cellspacing=1 border=0 width="100%">',
            '<tr><td class=title colspan=3>w3af target URL\'s</td></tr>',
            '<tr><td class=sub width="100%">URL</td></tr>')

        target_html = '<tr><td class=default width="100%%">%s</td></tr>'
        
        for t in cf.cf.get('targets'):
            self._write_to_file( target_html % cgi.escape( t.url_string ) )

        self._write_to_file('</table></td></tr></tbody></table><br />')

    
        #
        # Write info and vulns
        #
        self._write_to_file(
            '<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">',
            '<tbody> <tr><td>',
            '<table cellpadding=2 cellspacing=1 border=0 width="100%">',
            '<tr><td class=title colspan=3>Security Issues</td></tr>',
            '<tr>',
                '<td class=sub width="10%">Type</td>',
                '<td class=sub width="10%">Port</td>',
                '<td class=sub width="80%">Issue </td>',
            '</tr>')

        # Writes the vulnerabilities and informations to the results table
        infos = kb.kb.getAllInfos()
        
        for i in infos:

            #   Get all the information I'll be using
            desc = cgi.escape( i.getDesc() )
            severity = cgi.escape( i.getSeverity() )

            if i.getURL() is not None:
                port = str( i.getURL().getPort() )
                port = 'tcp/' + port
                escaped_url = cgi.escape (i.getURL().url_string)
            else:
                port = 'There is no port associated with this item.'
                escaped_url = 'There is no URL associated with this item.'
            
            if isinstance(i, vuln.vuln):
                color = 'red'
                i_class = 'Vulnerability'
            else:
                color = 'blue'
                i_class = 'Information'
            
            information_row = '<tr><td valign=top class=default width="10%%">' \
                              '<font color=%s>%s</font></td>'\
                              '<td valign=top class=default width="10%%">%s</td>' \
                              '<td class=default width="80%%">%s<br /><br />'\
                              '<b>URL:</b> %s<br />'\
                              '<b>Severity:</b> %s<br />'\
                              '</td></tr>'
            
            self._write_to_file( information_row % (color, i_class,
                                                    port,
                                                    desc,
                                                    escaped_url,
                                                    severity) )

        # Close the information/vulnerability table
        self._write_to_file('</table></td></tr></tbody></table><br />')
        
        # Write debug information
        self._write_to_file(
            '<table bgcolor="#a1a1a1" cellpadding=0 cellspacing=0 border=0 width="75%">' \
            '<tbody> <tr><td>' \
                '<table cellpadding=2 cellspacing=1 border=0 width="100%">' \
                    '<tr><td class=title colspan=3>Security Issues</td></tr>' \
                    '<tr>' \
                        '<td class=sub width="25%">Time</td>' \
                        '<td class=sub width="10%">Type</td>' \
                        '<td class=sub width="65%">Message</td>' \
                    '</tr>')

        for line in self._aditional_info:
            self._write_to_file( line )
        
        # Close the debug table
        self._write_to_file('</table></td></tr></tbody></table><br />')

        # Finish the report 
        self._write_to_file('</body>', '</html>')
        
        # Close the file.
        if self._file is not None:
            self._file.close()
            
    def get_long_desc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin writes the framework messages to an HTML report file.
        
        Two configurable parameters exist:
            - fileName
            - verbose

        If you want to write every HTTP request/response to a text file, you
        should use the text_file plugin.
        '''

