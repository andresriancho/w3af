# -*- coding: latin-1 -*-
'''
webserver.py

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

import os
from os import sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import mimetypes
import time
import socket
from core.controllers.threads.w3afThread import w3afThread
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
import sys
import cgi

WEBROOT = 'webroot' + os.path.sep

class webserver(w3afThread):
    '''
    This class defines a simple web server, developed to allow web GUI.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''

    def __init__( self, ip, port, wr ):
        w3afThread.__init__(self)
        global WEBROOT
        self._ip = ip
        self._port = port
        WEBROOT = wr
        self._server = None
        self._go = True
        self._running = False
        
    def stop(self):
        om.out.debug('Calling stop of webserver daemon.')
        if self._running:
            self._server.server_close()
            self._go = False
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((self._ip, self._port))
                s.close()
            except:
                pass
            self._running = False
        
    def run(self):
        '''
        Starts the http server.
        '''
        try:
            self._server = HTTPServer((self._ip, self._port), webGUIWebHandler )
        except Exception, e:
            om.out.error('Failed to start web server, error: ' + str(e) )
        else:
            message = 'Web server listening on '+ self._ip + ':'+ str(self._port)
            om.out.debug( message )
            self._running = True
            
            while self._go:
                try:
                    self._server.handle_request()
                except KeyboardInterrupt, ke:
                    om.out.information('Ctrl+C was pressed, bye!')
                    sys.exit(0)
                except:
                    self._server.server_close()
                
class webGUIWebHandler(BaseHTTPRequestHandler):
    
    _menuInstanceMap = {}
    
    def getMenuInstance( self, menuName ):
        '''
        @return: An instance of a menu for the WebUI.
        '''
        # First check if we have a instance for this already in memory
        if menuName in self._menuInstanceMap:
            return self._menuInstanceMap[ menuName ]
        
        else:
            # We need to find the menu module file.
            menuList = [ os.path.splitext(f)[0] for f in os.listdir('core/ui/webUi/') if os.path.splitext(f)[1] == '.py' ]
            menuList.remove('__init__')
            
            if menuName in menuList:
                ModuleName = 'core.ui.webUi.' + menuName
                __import__(ModuleName)
                aModule = sys.modules[ModuleName]
                aClass = getattr(aModule, menuName)
                menuPlug = apply(aClass, ())
                
                # Save it for later
                self._menuInstanceMap[ menuName ] = menuPlug
                
                return menuPlug
                
            raise w3afException('Menu not found')
    
    def do_GET(self):
        if self.path[1:].count('../'):
            self.send_error(404,'Yeah right...')
        else:
            # Handling of sapyto / w3af web menues
            header = self._getMenuHeader()
            if self.path[-3:] == '.py' or self.path[-4:] == '.win':
                menu = self.path[1:-3]
                # If independent windows, don't show menu header
                if self.path[-4:] == '.win':
                    header = ''
                    menu = self.path[1:-4]
                try:
                    aMenu = self.getMenuInstance(menu)
                    resp = aMenu.makeMenu()
                    self.send_response(200)
                    self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    self.wfile.write(header + resp)
                    
                except w3afException:
                    self.send_error(404,'File not found!')
            elif self.path == '/':
                # Handling of main menu
                self.send_response(302)
                self.send_header('Location', '/index.py')
                self.end_headers()
                self.wfile.write('')
            else:
                # Handling of non-menu files.
                
                try:
                    f = open( WEBROOT + sep + self.path[1:])
                except IOError:
                    self.send_error(404,'File Not Found: %s' % self.path)
                else:
                    self.send_response(200)
                    # This aint nice, but this aint a complete web server implementation
                    # it is only here to serve some files to "victim" web servers
                    type, encoding = mimetypes.guess_type( self.path )
                    if type != None:
                        self.send_header('Content-type',    type)
                    else:
                        self.send_header('Content-type',    'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
                    f.close()
        return
    
    def do_POST(self):
        # Handling of sapyto web menues
        header = self._getMenuHeader()
        if self.path[-3:] == '.py':
            menu = self.path[1:-3]
            if self.headers.dict.has_key('content-length'):

                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    try:
                        data = cgi.parse_multipart(self.rfile, pdict)
                    except Exception, e:
                        om.out.error('Invalid multipart form data. Exception: ' + str(e) )
                        data = {}
                elif ctype == 'application/x-www-form-urlencoded':
                    cl = int(self.headers['content-length'])
                    postData = self.rfile.read(cl)
                    try:
                        data = cgi.parse_qs(postData ,keep_blank_values=True,strict_parsing=True)
                    except Exception, e:
                        om.out.error('Invalid urlencoded form data. Exception: ' + str(e) )
                        data = {}
                else:
                    om.out.error('Unknown content-type: "' + ctype + '".')
                    data = {}
                
                aMenu = self.getMenuInstance(menu)
                resp = aMenu.parsePOST(data)
                
                # TODO: Add support for redirections after parsePOST
                self.send_response(200)
                self.send_header('Content-type',    'text/html')
                self.end_headers()
                self.wfile.write(header + resp)
                
    def log_message( self, format, *args):
        '''
        I dont want messages written to stderr, please write them to the om.
        '''
        message = "Local httpd - src: %s - %s" %(self.address_string(),format%args) 
        om.out.debug( message )

    def _getMenuHeader(self):
        try:
            f = open( WEBROOT + sep + 'header_menu.html')
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
        else:
            resp = f.read()
            f.close()
            return resp
                
