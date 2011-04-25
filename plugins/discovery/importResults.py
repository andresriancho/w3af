'''
importResults.py

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

# options
from core.data.options.option import option
from core.data.options.optionList import optionList

from core.controllers.basePlugin.baseDiscoveryPlugin import baseDiscoveryPlugin
from core.controllers.w3afException import w3afRunOnce
from core.data.request.frFactory import createFuzzableRequestRaw
from core.data.parsers.urlParser import url_object

import csv
import re
import os


class importResults(baseDiscoveryPlugin):
    '''
    Import URLs found by other tools.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)

        # Internal variables
        self._exec = True
        
        # User configured parameters
        self._input_csv = ''
        self._input_webscarab = ''
        self._input_burp = ''

    def discover(self, fuzzableRequest ):
        '''
        Read the input file, and create the fuzzableRequests based on that information.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains
                                    (among other things) the URL to test. It ain't used.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()

        else:
            self._exec = False
            res = []

            # Load data from the csv file
            if self._input_csv != '':
                try:
                    file_handler = file( self._input_csv )
                except Exception, e:
                    msg = 'An error was found while trying to read the input file: "'
                    msg += str(e) + '".'
                    om.out.error( msg )
                else:
                    for row in csv.reader(file_handler):
                        obj = self._obj_from_csv( row )
                        if obj:
                            res.append( obj )
            
            # Load data from WebScarab's saved conversations
            elif self._input_webscarab != '':
                try:
                    files = os.listdir( self._input_webscarab )
                except Exception, e:
                    msg = 'An error was found while trying to read the conversations directory: "'
                    msg += str(e) + '".'
                    om.out.error( msg )
                else:
                    files.sort()
                    for req_file in files:
                        # Only read requests, not the responses.
                        if not re.search( "([\d]+)\-request", req_file ):
                            continue
                        objs = self._objs_from_log( os.path.join( self._input_webscarab, req_file ) )
                        res.extend( objs )
                        
            # Load data from Burp's log
            elif self._input_burp != '':
                if os.path.isfile( self._input_burp ):
                    try:
                        res.extend( self._objs_from_log(self._input_burp) )
                    except Exception,  e:
                        msg = 'An error was found while trying to read the Burp log file: "'
                        msg += str(e) + '".'
                        om.out.error( msg )
                
        return res
    
    def _obj_from_csv( self, csv_row ):
        '''
        @return: A fuzzableRequest based on the csv_line.
        '''
        try:
            (method, uri, postdata) = csv_row
        except ValueError, value_error:
            msg = 'The file format is incorrect, an error was found while parsing: "'
            msg += str(csv_row) + '". Exception: "' + str(value_error) + '".'
            om.out.error( msg )
        else:
            # Create the obj based on the information
            uri = url_object( uri )
            if uri.is_valid_domain():
                return createFuzzableRequestRaw( method, uri, postdata, {} )
            
    def _objs_from_log( self, req_file ):
        '''
        This code was largely copied from Bernardo Damele's sqlmap[0] . See
        __feedTargetsDict() in lib/core/options.py. So credits belong to the
        sqlmap project.

        [0] http://sqlmap.sourceforge.net/

        @author Patrick Hof
        '''
        res = []
        fp = open( req_file, "r" )
        fread = fp.read()
        fread = fread.replace( "\r", "" )
        req_res_list = fread.split( "======================================================" )
        
        port   = None
        scheme = None

        for request in req_res_list:
            if scheme is None:
                scheme_port = re.search(
                        "\d\d[\:|\.]\d\d[\:|\.]\d\d\s+(http[\w]*)\:\/\/.*?\:([\d]+)",
                        request,
                        re.I
                )

            if scheme_port:
                scheme = scheme_port.group( 1 )
                port   = scheme_port.group( 2 )

            if not re.search ( "^[\n]*(GET|POST).*?\sHTTP\/", request, re.I ):
                continue

            if re.search( "^[\n]*(GET|POST).*?\.(gif|jpg|png)\sHTTP\/", request, re.I ):
                continue

            method       = None
            url          = None
            postdata     = None
            host = None
            headers      = {}
            get_post_req = False
            lines        = request.split( "\n" )

            for line in lines:
                if len( line ) == 0 or line == "\n":
                    continue

                if line.startswith( "GET " ) or line.startswith( "POST " ):
                    if line.startswith( "GET " ):
                        index = 4
                    else:
                        index = 5

                    url    = line[index:line.index(" HTTP/")]
                    method = line[:index-1]

                    get_post_req = True

                # XXX do we really need this? This is from the sqlmap code.
                # 'data' would be 'postdata' here. I can't figure out why this
                # is needed. Does WebScarab occasionally split requests to a new
                # line if they are overly long, so that we need to search for
                # GET parameters even after the URL was parsed? But that
                # wouldn't make sense with the way 'url' is set in line 168.
                # 
                # GET parameters 
                # elif "?" in line and "=" in line and ": " not in line:
                #     data    = line

                # Parse headers
                elif ": " in line:
                    key, value = line.split(": ", 1)
                    headers[key] = value
                    
                    if key.lower() == 'host':
                        host = value

                # POST parameters
                elif method is not None and method == "POST" and "=" in line:
                    postdata = line

            if get_post_req:
                if not url.startswith( "http" ):
                    url    = "%s://%s:%s%s" % ( scheme or "http", host, port or "80", url )
                    scheme = None
                    port   = None

                res.append( createFuzzableRequestRaw( method, url, postdata, headers ) )
                
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''
        d1 = 'Define the CSV input file from which to create the fuzzable requests'
        h1 = 'The input file is comma separated and holds the following data:'
        h1 += ' HTTP-METHOD,URI,POSTDATA'
        o1 = option('input_csv', self._input_csv, d1, 'string', help=h1)
        
        d2 = 'Define the Burp log file from which to create the fuzzable requests'
        h2 = 'The input file needs to be in Burp format.'
        o2 = option('input_burp', self._input_burp, d2, 'string', help=h2)
        
        d3 = 'Define the WebScarab conversation directory from which to create the fuzzable requests'
        h3 = 'The directory needs to contain WebScarab conversation files.'
        o3 = option('input_webscarab', self._input_webscarab, d3, 'string', help=h3)

        ol = optionList()
        ol.add(o1)
        ol.add(o2)
        ol.add(o3)
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._input_csv = optionsMap['input_csv'].getValue()
        self._input_burp = optionsMap['input_burp'].getValue()
        self._input_webscarab = optionsMap['input_webscarab'].getValue()
        
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
        This plugin serves as an entry point for the results of other tools that search for URLs.
        The plugin reads from different input files and directories and creates the fuzzable requests
        that are needed by the audit plugins.
        
        Three configurable parameter exist:
            - input_csv
            - input_burp
            - input_webscarab
        '''
