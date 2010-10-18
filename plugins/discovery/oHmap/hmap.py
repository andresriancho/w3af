#! /usr/bin/env python
#
#  Fingerprint a web server and identify its vendor/version/OS
#  Copyright (C) 2003  Dustin Lee
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#  You can reach me at <leed@cs.ucdavis.edu>
######################################################################

import sys,pprint,glob,getopt,re,time
import socket, urlparse, select
import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
import core.data.kb.config as cf
import os

class request:
    """Collect elements needed to send a Request to an HTTP server"""
    def __init__(self, url, method='GET', local_uri='/', version='1.0'):
        self.url = url
        self.method = method
        self.local_uri = local_uri
        self.version = version
        self.headers = [['User-Agent', cf.cf.getData('User-Agent')]]
        self.line_joiner = '\r\n'
        self.body = ''
        self.adhoc_method_line = ''

    def __str__(self):
        method_line = self.adhoc_method_line
        if not method_line:
            method_line = '%s %s HTTP/%s'%(self.method, self.local_uri, self.version)

        return self.line_joiner.join([method_line] + \
                                     ['%s: %s'%(x,y) for x,y in self.headers]) + \
                                     (2*self.line_joiner) + self.body

    def submit(self):
        om.out.debug('hmap is sending: ' + str(self) )
        # Echo client program
        HOST = self.url

        tries = 3
        wait_time = 1
        while tries != 0:
            if tries < 3 and VERBOSE: print '!!! TRIES =', tries
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Added by Andres Riancho to get SSL support !
            try:
                s.connect((HOST, PORT))
            except:
                raise w3afException('Connection failed to ' + str(HOST) + ':' + str(PORT) )
            else:
                
                if useSSL:
                    try:
                        s2 = socket.ssl( s )
                    except:
                        raise w3afException('SSL Connection failed to ' + str(HOST) + ':' + str(PORT) )
                    else:
                        s.recv = s2.read
                        s.send = s2.write
                
                data = ''
                
                try:
                    s.send(str(self))
                except:
                    om.out.debug('Failed to send data to socket.' )
                    # Try again
                    tries -= 1
                    time.sleep(wait_time)
                    wait_time *= 2
                    s.close()
                    continue                    
                
                
                ss = s
                try:
                    while 1:
                        ss = select.select([s],[],[],10)[0]
                        if not ss:
                            break
                        ss = ss[0] 
                        temp = ss.recv(1024)
                        if not temp: break
                        data += temp # TODO:  more efficient to append to list
                    s.close()
                except KeyboardInterrupt,e:
                    raise e
                except socket.sslerror, sslerr:
                    # When the remote server has no more data to send
                    # It simply closes the remote connection, which raises:
                    # (6, 'TLS/SSL connection has been closed')
                    if sslerr[0] == 6:
                        return response(data)
                    else:
                        # Try again
                        tries -= 1
                        time.sleep(wait_time)
                        wait_time *= 2
                        s.close()
                        continue
                        
                except Exception:
                    # Try again.
                    tries -= 1
                    time.sleep(wait_time)
                    wait_time *= 2
                    s.close()
                    continue
                break
        return response(data)

    def add_header(self, name, data):
        self.headers.append([name,data])

######################################################################

class response:
    """Read in Response from HTTP server and parse out elements of interest"""
    def __init__(self, raw_text):
        self.raw_text = raw_text
        self.headers = []
        self.body = ''
        self.__parse(raw_text)

    def __parse(self,text):
        if not text:
            self.response_code = 'NO_RESPONSE'
            self.response_text = 'NONE'
            return

        if not re.search('^HTTP/1\.[01] [0-9]{3} [A-Z]{,10}', text):
            self.response_code = 'NO_RESPONSE_CODE' # HTTP/0.9 like
            self.response_text = 'NONE'
            self.body = text
            return

        # really parse it
        crlf_index = text.find('\r\n')
        cr_index = text.find('\r')
        line_splitter = '\r\n'

        # TODO: is this sufficient???
        if crlf_index == -1 or cr_index  < crlf_index:
            line_splitter = '\n'

        response_lines = text.split(line_splitter)
        self.response_line = response_lines[0]
        response_line_match = re.search('(HTTP/1\.[01]) ([0-9]{3}) ([^\r\n]*)', text)
        self.response_code, self.response_text = response_line_match.groups()[1:]

        blank_index = response_lines[:].index('')
        if blank_index == -1:
            blank_index = len(response_lines)

        self.headers = response_lines[1:blank_index]
        # NOTE: !! actually don't need or want body to be split but don't
        #         really care at this point ...
        self.body = response_lines[blank_index:]

        
    def return_code(self):
        return self.response_code, self.response_text

    def describe(self):
        print '-'*70
        print 'RESPONSE LINE:'
        if hasattr(self,'response_line'):
            print self.response_line
        print '-'*70
        print 'HEADERS:'
        if hasattr(self,'headers'):
            print self.headers
        print '-'*70
        print 'BODY:'
        if hasattr(self,'body'):
            print self.body

    def has_header(self, name):
        for h in self.headers:
            if h.startswith(name):
                return 1
        return 0

    def header_data(self,name):
        assert(self.has_header(name))
        for h in self.headers:
            if h.startswith(name):
                return h.split(': ',1)[-1]

    def header_names(self):
        result = []
        for h in self.headers:
            name = h.split(':',1)[0]
            result.append(name)
        return result

    def servername(self):
        if not self.has_header('Server'):
            return None
        return self.header_data('Server')

######################################################################
# Functions for probing server and collecting characteristics

def get_fingerprint(url):
    basic_get(url) # TODO: this is redundant with later test...
    basic_options(url)
    unknown_method(url)
    unauthorized_activity(url)
    nonexistant_object(url)
    malformed_method_line(url)
    long_url_ranges(url)
    long_default_ranges(url)
    many_header_ranges(url)
    large_header_ranges(url)
    unavailable_accept(url)
    fake_content_length(url)
    ### TODO some more tests to add:
    # compare_get_head_header_order  n ## see if body sent back??
       # also see if get same headers in same order
    # require_host
    # unmodified_since  # also with sending bad date

    fingerprint['SYNTACTIC']['HEADER_ORDER'] = winnow_ordered_list(fingerprint['SYNTACTIC']['HEADER_ORDER'])
    return fingerprint


######################################################################
# Known test types for provoking characterisitcs
# Many tests are just "randomly" designed out of thin air
# but many come from reading the RFC and looking for things
# that implementors may have varied in implementations.
def basic_get(url):
    req = request(url)
    res = req.submit()
    get_characteristics('basic_get', res)

def basic_options(url):
    req = request(url,method='OPTIONS')
    res = req.submit()
    get_characteristics('basic_options', res)

def unknown_method(url):
    req = request(url,method='QWERTY')
    res = req.submit()
    get_characteristics('unknown_method', res)

def unauthorized_activity(url):
    
    # Removed the DELETE method so we don't remove a whole site without wanting to :)
    unauthorized_activities = ('OPTIONS', 'TRACE', 'GET', 'HEAD', 
                               'PUT', 'POST', 'COPY', 'MOVE', 'MKCOL', 
                               'PROPFIND', 'PROPPATCH', 'LOCK', 'UNLOCK', 
                               'SEARCH')
    for ua in unauthorized_activities:
        req = request(url,method=ua)
        res = req.submit()
        get_characteristics('unauthorized_activity', res)

def nonexistant_object(url):
    req = request(url,local_uri='/asdfg.hjkl')
    res = req.submit()
    get_characteristics('nonexistant_object', res)  

# ways to mess up the method line
# (nothing)METHOD(space)RELATIVE-URI(space)VERSION(line-sep)
# - replace any one of these with wrong thing
# - string together  variations of any of these
#   - number where expects letter or vice verse
#   - really LONG things
#   - invalid characters
#   - different file system conventions
#   - illegal paths "../../../"
#   - url encoding (hex, unicode, invalid of each)
#   - something instead of nothing and vice versa
#   - uppercase/lowercase
def malformed_method_line(url):
    malformed_methods = ( 'GET', #0 TODO: repeat all these with HEAD and OTHER
                          'GET /',#1
                          'GET / HTTP/999.99',
                          'GET / HHTP/1.0',
                          'GET / HTP/1.0',
                          'GET / HHTP/999.99',
                          #'GET / HHTP/1.0',
                          'GET / hhtp/999.99',
                          'GET / http/999.99',
                          'GET / HTTP/Q.9',
                          'GET / HTTP/9.Q',
                          'GET / HTTP/Q.Q', #10 
                          'GET / HTTP/1.X',
                          'GET / HTTP/1.10',
                          'GET / HTTP/1.1.0',
                          'GET / HTTP/1.2',
                          'GET / HTTP/2.1',
                          'GET / HTTP/1,0',
                          #r'\GET / HTTP/1.0' or '\\GET / HTTP/1.0'
                          #'GET / HTTP\1.0',
                          #'GET / HTTP-1.0',
                          #'GET / HTTP 1.0',
                          'GET / HTTP/1.0X',
                          'GET / HTTP/',
                          #'get / http/1.0',
                          #'qwerty / HTTP/1.0'
                          #'GETX / HTTP/1.0'
                          #' GET/HTTP/1.0',
                          'GET/HTTP/1.0' ,
                          'GET/ HTTP/1.0' ,#20
                          'GET /HTTP/1.0' ,
                          'GET/HTTP /1.0' ,
                          'GET/HTTP/1 .0' ,
                          'GET/HTTP/1. 0' ,
                          'GET/HTTP/1.0 ' ,
                          'GET / HTTP /1.0', #etc.... 
                          'HEAD /.\\ HTTP/1.0', # indicates windows??
                          'HEAD /asdfasdfasdfasdfasdf/../ HTTP/1.0',
                          'HEAD /asdfasdfasdfasdfasdf/.. HTTP/1.0',
                          'HEAD /./././././././././././././././ HTTP/1.0',#30
                          'HEAD /././././././qwerty/.././././././././ HTTP/1.0',
                          #'HEAD ../ HTTP/1.0',
                          'HEAD /.. HTTP/1.0',
                          'HEAD /../ HTTP/1.0',
                          'HEAD /../../../../../ HTTP/1.0',
                          'HEAD .. HTTP/1.0',
                          #'HEAD . HTTP/1.0',
                          'HEAD\t/\tHTTP/1.0',
                          'HEAD ///////////// HTTP/1.0',
                          'Head / HTTP/1.0',
                          '\nHEAD / HTTP/1.0',
                          ' \nHEAD / HTTP/1.0',#40
                          ' HEAD / HTTP/1.0',
                          'HEAD / HQWERTY/1.0', 
                          #      'HEAD http://some.host.com/ HTTP/1.0',
                          #      'HEAD hTTP://some.host.com/ HTTP/1.0',
                          #      'HEAD http://some.host.com HTTP/1.0',
                          'HEAD %s HTTP/1.0' % url,
                          #'HEAD hTTP://$url/ HTTP/1.0',
                          #'HEAD http://$url HTTP/1.0',
                          'HEAD %s' % url,
                          'HEAD http:// HTTP/1.0',
                          'HEAD http:/ HTTP/1.0',
                          'HEAD http: HTTP/1.0',
                          'HEAD http HTTP/1.0',
                          'HEAD h HTTP/1.0',
                          #      'HEAD HTTP://some.host.com/ HTTP/1.0',
                          #'HEAD HTTP://$url/ HTTP/1.0',
                          'HEAD HTTP://qwerty.asdfg.com/ HTTP/1.0', #50
                          'GET GET GET',
                          'HELLO',
                          #      'HEAD%00 / HTTP/1.0',
                          'GET \0 / HTTP/1.0',
                          'GET / \0 HTTP/1.0',
                          'GET / HTTP/1.0\0',
                          'GET / H',
                          ' GET / HTTP/1.0',
                          ' '*1000 + 'GET / HTTP/1.0',
                          'GET'+' '*1000+'/ HTTP/1.0',
                          'GET '+'/'*1000+' HTTP/1.0', #60
                          'GET /'+' '*1000+'HTTP/1.0',
                          'GET / '+'H'*1000+'TTP/1.0',
                          'GET / '+'HTTP'+'/'*1000+'1.0',
                          'GET / '+'HTTP/'+'1'*1000+'.0',
                          'GET / '+'HTTP/1'+'.'*1000+'0',
                          'GET / '+'HTTP/1.'+'0'*1000,
                          'GET / HTTP/1.0' + ' ' * 1000,
                          '12345 GET / HTTP/1.0',
                          '12345 / HTTP/1.0',
                          # check if \0 is really a null
                          '\0',#70
                          '\0'*1000,
                          '\0'+'GET / HTTP/1.0',
                          '\0'*1000+'GET / HTTP/1.0',
                          '\r\n'*1000+'GET / HTTP/1.0',
                          'Get / HTTP/1.0',
                          'GET\0/\0HTTP/1.0', 
                          'GET . HTTP/1.0',
                          'GET index.html HTTP/1.0', # is this legal?
                          'GET / HTTP/1.',
                          '', #80
                          ' ',
                          ' '*1000,
                          '/',
                          '/' * 1000,
                          'GET FTP://asdfasdf HTTP/1.0',
                          'GET / HTTP/1.0 X', 
                          # any or all parts or request URL encoded
                          #>>> [hex(ord(x)) for x in "GET / HTTP/1.0"]
                          #['0x47', '0x45', '0x54', '0x20', '0x2f', '0x20', '0x48', '0x54', '0x54', '0x50', '0x2f', '0x31', '0x2e', '0x30']
                          '%47ET / HTTP/1.0',
                          '%47%45%54 / HTTP/1.0',
                          'GET %2f HTTP/1.0',
                          'GET %2F HTTP/1.0', #90
                          'GET%20/ HTTP/1.0',
                          'GET / FTP/1.0',
                          'GET \ HTTP/1.0', # windows style
                          #'GET \./',
                          #'GET \.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\.\. HTTP/1.0'
                          'GET C:\ HTTP/1.0',
                          'HTTP/1.0 / GET', # and other permutations
                          # try various escape sequences from c etal
                          # \a = bell
                          # \b = back space?
                          'ALL YOUR BASE ARE BELONG TO US', 
                          'GET "/" HTTP/1.0',
                          "GET '/' HTTP/1.0",
                          'GET `/` HTTP/1.0', 
                          '"GET / HTTP/1.0"', #100
                          '"GET / HTTP/1.0',
                          '"GET" / HTTP/1.0',
                          '""GET / HTTP/1.0',
                          'GEX\bT / HTTP/1.0', # espace characters
                          )

    #print len(malformed_methods)
    for index, mm in zip(range(len(malformed_methods)), malformed_methods):
        req = request(url)
        req.adhoc_method_line = mm
        res = req.submit()
        get_characteristics('MALFORMED_'+('000'+str(index))[-3:], res)

def large_binary_searcher(url, large_helper, largest, guesses=[]):
    ranges = [(x,large_helper(url, x)) for x in [1]+guesses+[largest]]
    
    while 1:
        halfways = find_halfways(ranges)
        if not halfways:
            break
        for hw in halfways:
            ranges.append((hw, large_helper(url, hw)))
        ranges.sort()

    ranges = minimize_ranges(ranges)
    
    return ranges

def find_halfways(ranges):
    # assumes they are sorted
    grouped_ranges = []
    for r in ranges:
        if len(grouped_ranges) == 0:
            grouped_ranges.append([r])
            continue
        if r[1] == grouped_ranges[-1][-1][1]:
            grouped_ranges[-1].append(r)
            continue
        grouped_ranges.append([r])

    halfways = []
    for i in range(len(grouped_ranges) - 1):
        largest_previous = grouped_ranges[i][-1]
        smallest_next = grouped_ranges[i+1][0]

        if (smallest_next[0] - largest_previous[0]) == 1:
            continue
        hw = ((smallest_next[0] - largest_previous[0]) / 2) + largest_previous[0]
        if VERBOSE: print largest_previous, hw, smallest_next
        halfways.append(hw)

    return halfways

def minimize_ranges(ranges):
    # assumes they are sorted
    # TODO: this is the same code as above just copied!!!
    grouped_ranges = []
    for r in ranges:
        if len(grouped_ranges) == 0:
            grouped_ranges.append([r])
            continue
        if r[1] == grouped_ranges[-1][-1][1]:
            grouped_ranges[-1].append(r)
            continue
        grouped_ranges.append([r])

    minimized = []
    for gr in grouped_ranges:
        minimized.append(gr[0])
        if len(gr) > 1:
            minimized.append(gr[-1])

    return minimized

# TODO: maybe do this recursively????
# TODO: remember that header size et all are configurable in apache
def long_url_helper(url,size):
    #long_name = 'a'*size
    req = request(url,local_uri=('/'+('a'*size)))
    res = req.submit()
    get_characteristics('LONG_URL_RANGES', res)
    return res.response_code

# TODO: note that don't call get_characteristics
#      since don't have a response to deal with here
def long_url_ranges(url):
    # TODO: base these on "best guess" of what talking to
    #      e.g. if think it's apache 1.3.9 then use those to avoid
    #      so many long requests
    initial_guesses = [99,100,201,202,208,209,210,211,254,255,256,
                       765,766,
                       8079,8080,8176,8177]
    ranges = large_binary_searcher(url, long_url_helper, 10000, guesses=initial_guesses)
    add_characteristic('SEMANTIC','LONG_URL_RANGES', ranges)    

def long_default_helper(url,size):
    req = request(url,local_uri=('/'*size))
    res = req.submit()
    get_characteristics('LONG_DEFAULT_RANGES', res)
    return res.response_code

def long_default_ranges(url):
    ranges = large_binary_searcher(url, long_default_helper, 10000)
    add_characteristic('SEMANTIC','LONG_DEFAULT_RANGES', ranges)    

def many_header_helper(url,size):
    req = request(url)
    for i in range(size):
        req.add_header('HEADER'+('0000000000'+str(i)[-10:]), ('0000000000'+str(i))[-10:] )
    res = req.submit()
    get_characteristics('MANY_HEADER_RANGES', res)
    return res.response_code

def many_header_ranges(url):
    initial_guesses = [99,100,228,229,]
    ranges = large_binary_searcher(url, many_header_helper, 10000, guesses=initial_guesses)
    add_characteristic('SEMANTIC','MANY_HEADER_RANGES', ranges) 
    
def large_header_helper(url,size):
    req = request(url)
    req.add_header('LARGE_HEADER', 'a'*size )
    res = req.submit()
    get_characteristics('LARGE_HEADER_RANGES', res)
    return res.response_code

def large_header_ranges(url):
    initial_guesses = [8176,8177,]
    ranges = large_binary_searcher(url, large_header_helper, 10000, guesses=initial_guesses)
    add_characteristic('SEMANTIC','LARGE_HEADER_RANGES', ranges)    
    

def unavailable_accept(url):
    req = request(url)
    req.add_header('Accept', 'qwer/asdf')
    res = req.submit()
    get_characteristics('unavailable_accept', res)
    
def fake_content_length(url):
    req = request(url)
    req.add_header('Content-Length', '1000000000')
    req.body = 'qwerasdfzxcv'
    res = req.submit()
    get_characteristics('fake_content_length', res)

# TODO: put this global declaration somewhere easier to find....
fingerprint = {'LEXICAL' : {},
               'SYNTACTIC' : {},
               'SEMANTIC' : {},}

def add_characteristic(category,name,value,data_type=None):
    # just add if not already in there
    if not fingerprint[category].has_key(name):
        # TODO: probably don't need a data type just look at data...
        if data_type == 'LIST':
            value = [value]
        fingerprint[category][name] = value
        return
    # don't duplicate
    if fingerprint[category][name] == value:
        return
    # create or add to list as necessary
    if type(fingerprint[category][name]) != type([]):
        fingerprint[category][name] = [fingerprint[category][name],value]
    elif value not in fingerprint[category][name]:
        fingerprint[category][name].append(value)

def get_characteristics(test_name, res):
    if VERBOSE: print 'processing', test_name
    
    response_code, response_text = res.return_code()
    claimed_servername = res.servername()

    if response_code not in ['NO_RESPONSE_CODE', 'NO_RESPONSE']:
        add_characteristic('LEXICAL',response_code,response_text)
        add_characteristic('LEXICAL','SERVER_NAME', claimed_servername)

    if test_name.endswith('RANGES'):
        return # only need the code and text

    if res.has_header('Allow'):
        data = res.header_data('Allow')
        add_characteristic('SYNTACTIC','ALLOW_ORDER',data)

    if res.has_header('Public'):
        data = res.header_data('Public')
        add_characteristic('SYNTACTIC','PUBLIC_ORDER',data)

    if res.has_header('Vary'):
        data = res.header_data('Vary')
        add_characteristic('SYNTACTIC','VARY_ORDER',data)

    if test_name.startswith('MALFORMED_'):
        add_characteristic('SEMANTIC',test_name, response_code)

    if response_code not in ['NO_RESPONSE_CODE', 'NO_RESPONSE']:
        header_names = res.header_names()
        add_characteristic('SYNTACTIC', 'HEADER_ORDER', header_names, data_type='LIST')
    else:
        ### Added by APR to solve a wierd exception....
        add_characteristic('SYNTACTIC', 'HEADER_ORDER', [], data_type='LIST')
        
    if res.has_header('ETag'):
        data = res.header_data('ETag')
        add_characteristic('SYNTACTIC', 'ETag', data)
    elif res.has_header('Etag'):
        data = res.header_data('Etag')
        add_characteristic('SYNTACTIC', 'ETag', data)

# 'HEADER_ORDER': [   [   'Date',
#                        'Server',
#                        'Last-Modified',
#                        'ETag',
#                        'Accept-Ranges',
#                        'Content-Length',
#                        'Connection',
#                        'Content-Type'],
#                    [   'Date',
#                        'Server',
#                        'Content-Length',
#                        'Allow',
#                        'Connection'],
#                    [   'Date',
#                        'Server',
#                        'Allow',
#                        'Connection'],
#                    ['Date', 'Server', 'Connection'],
#                    [   'Date',
#                        'Server',
#                        'Connection',
#                        'Transfer-Encoding'],
#                    [   'Date',
#                        'Server',
#                        'Alternates',
#                        'Vary',
#                        'TCN',
#                        'Connection']],
# clean up redundancies in lists of lists
def winnow_ordered_list(ordered_list):
    #print ordered_list
    if len(ordered_list) < 2:
        #print 'ordered_list too small to look at'
        return
    
    ordered_list.sort(lambda a,b: cmp(len(a), len(b)))
    #print 'sorted order', ordered_list

    index = 0
    result = []
    for (index, elem) in zip(range(len(ordered_list) - 1),ordered_list):
        is_ok = 1
        for other in ordered_list[index+1:]:
            if is_partial_ordered_sublist(elem, other):
                #print elem,'is sublist of', other
                is_ok = 0
                break
        if is_ok:
            result.append(elem)
    result.append(ordered_list[-1])
    #print result
    return result
        
def is_partial_ordered_sublist(small,large):
    if len(small) > len(large):
        return 0
    if small == large:
        return 1
    presort = []
    try:
        presort = [large.index(x) for x in small]
    except ValueError:
        return 0
    postsort = presort[:]
    postsort.sort()
    #print presort, postsort
    if -1 in presort or presort != postsort:
        return 0
    return 1

######################################################################
# Functions for comparing to known profiles
#
def find_most_similar(known_servers, subject):

    scores = []

    #TODO: make each of these it's own function....

    for server in known_servers:
        matches = 0
        mismatches = 0
        unknowns = 0
        
        # LEXICAL
        codes = ('200', '207',
                 '301', '302',
                 '400', '401', '403', '404', '405', '406', '411', '413', '414',
                 '500', '501',)
        for code in codes:
            known_server_text = ''
            subject_server_text = ''
            if server['LEXICAL'].has_key(code):
                known_server_text = server['LEXICAL'][code]
            if subject['LEXICAL'].has_key(code):
                subject_server_text = subject['LEXICAL'][code]

            if known_server_text == '' or subject_server_text == '':
                unknowns += 1
            elif known_server_text == subject_server_text:
                matches += 1
            else:
                mismatches += 1

        # SYNTACTIC
        # allow order
        known_server_allows = ''
        subject_server_allows = ''
        if server['SYNTACTIC'].has_key('ALLOW_ORDER'):
            known_server_allows = server['SYNTACTIC']['ALLOW_ORDER']
        if subject['SYNTACTIC'].has_key('ALLOW_ORDER'):
            subject_server_allows = subject['SYNTACTIC']['ALLOW_ORDER']

        if known_server_allows and subject_server_allows:
            if known_server_allows == subject_server_allows:
                matches += 1
            else:
                mismatches += 1
        else:
            unknowns += 1
    
        ## etag match
        #check if server has ETag and subject has ETag
        #   if either not then unknonw
        #if subject matches server by regex
        #   matches += 1
        #else
        #   mismatches += 1
        
        # SEMANTIC
        # malformed_???
        for num in range(105):
            malformed = 'MALFORMED_' + ('000'+str(num))[-3:]
            known_server_mal = server['SEMANTIC'][malformed]
            subject_server_mal = subject['SEMANTIC'][malformed]
            
            if known_server_mal == subject_server_mal:
                matches += 1
            else:
                mismatches += 1

        # long ranges
        known_server_long_url = server['SEMANTIC']['LONG_URL_RANGES']
        subject_server_long_url = subject['SEMANTIC']['LONG_URL_RANGES']
        if known_server_long_url == subject_server_long_url:
            matches += 1
            #print 'LONG_URL_RANGES match', server['LEXICAL']['SERVER_NAME']
            #print known_server_long_url
        else:
            mismatches += 1

        # long default "/" ranges
        known_server_long_default = server['SEMANTIC']['LONG_DEFAULT_RANGES']
        subject_server_long_default = subject['SEMANTIC']['LONG_DEFAULT_RANGES']
        if known_server_long_default == subject_server_long_default:
            matches += 1
            #print 'LONG_URL_DEFAULT_RANGES match', server['LEXICAL']['SERVER_NAME']
            #print known_server_long_default
        else:
            mismatches += 1

        # unique header exists
        # e.g. X-Pad, etc - or just do ALL known headers....
        
        scores.append([server, (matches,mismatches,unknowns)])

    return scores

# [a,b,c,e,f] and [a,c,d,f,g] are both ordered the same.....
# -1/0/1 = no/maybe/yes
# TODO: get this working....
def partial_same_order(list1, list2):
    common = {}
    #print 'comparing lists: ',list1,list2
    for x in list1+list2:
        if x not in common:
            common[x] = 0
        common[x] += 1
    common_items = {}
    #common_items = [common_items[k] = v for k,v in common if v == 2]
    for k,v in common:
        if v == 2:
            common[k] = v
    common1 = [] # is there a simple way??
    common2 = []
    for i in list1:
        if common_items.has_key(i):
            common1.append(i)
    for i in list2:
        if common_items.has_key(i):
            common2.append(i)

    #print common1,common2
    if common1 == []:
        return 0
    elif common1 == common2:
        return 1
    else:
        return -1

def usage():
    print """
hmap is a web server fingerprinter.

hmap [-hpgn] {url | filename}

e.g.
   hmap http://localhost:82

   hmap -p www.somehost.net.80

-h         this info...
-n         show this many of the top possible matches
-p         run with a prefetched file
-g         gather only (don't do comparison)
-c         show this many closest matches
"""
    sys.exit()

###################################################################### 
# This was added by Andres Riancho to make hmap work inside w3af
# it is a "copy" of the "main" with a lot of default parameters :P
VERBOSE = 0
PORT = 80
useSSL = False

def testServer( ssl, server, port, matchCount, generateFP ):
    global VERBOSE
    global PORT 
    global useSSL
    VERBOSE = 0
    PORT = port
    useSSL = ssl
    
    MATCH_COUNT = matchCount
    fingerprintDir = 'plugins'+os.path.sep+'discovery'+os.path.sep+'oHmap'+os.path.sep+'known.servers'+os.path.sep
    
    # Get the fingerprint
    target_url = server
    fp = get_fingerprint(target_url)

    # Read the fingerprint db
    known_servers = []
    for f in glob.glob(fingerprintDir+'*'):
        ksf = file(f)
        try:
            ### FIXME: This eval is awful, I should change it to pickle.
            ks = eval(ksf.read())
        except Exception,  e:
            raise w3afException('The signature file "' + f + '" has an invalid sintax.')
        else:
            known_servers.append(ks)
            ksf.close()
    
    # Generate the fingerprint file
    if generateFP:
        for i in xrange(10):
            try:
                fd = open( 'hmap-fingerprint-' + server + '-'+ str(i), 'w' )
            except Exception,  e:
                raise w3afException('Cannot open fingerprint file. Error:' + str(e))
            else:
                import pprint
                pp = pprint.PrettyPrinter(indent=4)
                pprint.PrettyPrinter(stream=fd).pprint(fp)
                fd.close()
                break
    
    # Compare
    scores = find_most_similar(known_servers, fp)
    def score_cmp(score1,score2):
        (server1, (matches1,mismatches1,unknowns1)) = score1
        (server2, (matches2,mismatches2,unknowns2)) = score2
    
        if -cmp(matches1,matches2) != 0:
            return -cmp(matches1,matches2)
    
        return cmp (server1,server2)
    scores.sort(score_cmp)
    
    res = []
    for (server, (matches,mismatches,unknowns)) in scores[:MATCH_COUNT]:
        res.append(server['LEXICAL']['SERVER_NAME'])

    return res

