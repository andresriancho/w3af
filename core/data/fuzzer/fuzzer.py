'''
fuzzer.py

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

# Some generic imports for creating strings
from string import letters, digits
from random import choice, randint

import core.data.kb.config as cf

# Common modules
import copy
import re
import urllib
import cgi
import json

from core.controllers.w3afException import w3afException

# The data containers
from core.data.dc.cookie import Cookie
from core.data.dc.dataContainer import DataContainer
from core.data.request.httpPostDataRequest import httpPostDataRequest
from core.data.request.httpQsRequest import HTTPQSRequest

# import all the mutant types
from core.data.fuzzer.formFiller import smartFill
from core.data.fuzzer.mutantQs import mutantQs
from core.data.fuzzer.mutantPostData import mutantPostData
from core.data.fuzzer.mutantFileName import mutantFileName
from core.data.fuzzer.mutantUrlParts import mutantUrlParts
from core.data.fuzzer.mutantHeaders import mutantHeaders
from core.data.fuzzer.mutantJSON import mutantJSON
from core.data.fuzzer.mutantCookie import mutantCookie
from core.data.fuzzer.mutantFileContent import mutantFileContent

import core.controllers.outputManager as om

from core.controllers.misc.io import NamedStringIO
from core.data.dc.form import Form


#
# The following is a list of parameter names that will be ignored during
# the fuzzing process
#
IGNORED_PARAMETERS = [
    '__EVENTTARGET', '__EVENTARGUMENT', '__VIEWSTATE', '__VIEWSTATEENCRYPTED', 
    '__EVENTVALIDATION', '__dnnVariable', 'javax.faces.ViewState',
    'jsf_state_64', 'jsf_sequence', 'jsf_tree', 'jsf_tree_64', 
    'jsf_viewid', 'jsf_state', 'cfid', 'cftoken','ASP.NET_sessionid',
    'ASPSESSIONID', 'PHPSESSID', 'JSESSIONID'
    ]

def createMutants(freq, mutant_str_list, append=False,
                  fuzzableParamList=[], oResponse=None):
    '''
    @parameter freq: A fuzzable request with a DataContainer inside.
    @parameter mutant_str_list: a list with mutant strings to use
    @parameter append: This indicates if the content of mutant_str_list should
        be appended to the variable value
    @parameter fuzzableParamList: If [] then all params are fuzzed. If ['a'],
        then only 'a' is fuzzed.
    @return: A Mutant object List.
    '''
    result = []
    _fuzzable = _createFuzzable(freq)
    
    if isinstance(freq, HTTPQSRequest):
        
        # Query string parameters    
        om.out.debug('Fuzzing query string')
        result.extend(_createMutantsWorker(freq, mutantQs, mutant_str_list,
                                           fuzzableParamList, append))
        
        # File name
        if 'fuzzedFname' in _fuzzable:
            om.out.debug('Fuzzing file name')
            result.extend(_createFileNameMutants(freq, mutantFileName, 
                                 mutant_str_list, fuzzableParamList, append))

        if 'fuzzURLParts' in _fuzzable:
            om.out.debug('Fuzzing URL parts')
            result.extend(_createUrlPartsMutants(freq, mutantUrlParts, 
                                 mutant_str_list, fuzzableParamList, append))
 
    # POST-data parameters
    elif isinstance(freq, httpPostDataRequest):
        # If this is a POST request, it could be a JSON request, and I want
        # to fuzz it!
        om.out.debug('Fuzzing POST data')
        if isJSON(freq):
            result.extend(_createJSONMutants(freq, mutantJSON, mutant_str_list,
                                             fuzzableParamList, append))
        else:
            result.extend(_createMutantsWorker(freq, mutantPostData,
                                   mutant_str_list, fuzzableParamList, append))
        
        # File content of multipart forms
        if 'fuzzFileContent' in _fuzzable:
            om.out.debug('Fuzzing file content')
            result.extend(_createFileContentMutants(freq, mutant_str_list,
                                                    fuzzableParamList, append))
    # Headers
    if 'headers' in _fuzzable:
        om.out.debug('Fuzzing headers')
        result.extend(_createMutantsWorker(freq, mutantHeaders, mutant_str_list,
                                           fuzzableParamList, append, 
                                           dataContainer=_fuzzable['headers']))
        
    # Cookie values
    if 'cookie' in _fuzzable and freq.getCookie():
        om.out.debug('Fuzzing cookie')
        mutants = _createMutantsWorker(freq, mutantCookie, mutant_str_list,
                                       fuzzableParamList, append,
                                       dataContainer=freq.getCookie())        
        result.extend( mutants )
    
    #
    # Improvement to reduce false positives with a double check:
    #    Get the original response and link it to each mutant.
    #
    # Improvement to reduce network traffic:
    #    If the original response has an "ETag" header, set a "If-None-Match"
    #    header with the same value. On a test that I ran, the difference was
    #    very noticeable:
    #        - Without sending ETag headers: 304046 bytes
    #        - Sending ETag headers:          55320 bytes
    #
    # This is very impressing, but the performance enhancement is only
    # possible IF the remote server sends the ETag header, and for example
    # Apache+PHP doesn't send that tag by default (only sent if the PHP developer
    # added some code to his PHP to do it).
    #
    if oResponse is not None:
        
        headers = oResponse.getHeaders()
        etag = headers.get('ETag', None)
        
        for m in result:
            m.setOriginalResponseBody( oResponse.getBody() )
            
            if etag is not None:
                orig_headers = m.getHeaders()
                orig_headers['If-None-Match'] = etag
                m.setHeaders(orig_headers) 
        
    return result

def _createJSONMutants(freq, mutantClass, mutant_str_list, fuzzableParamList, append):
    '''
    @param freq: A fuzzable request with a DataContainer inside.
    @param mutantClass: The class to use to create the mutants
    @param fuzzableParamList: What parameters should be fuzzed
    @param append: True/False, if we should append the value or replace it.
    @param mutant_str_list: a list with mutant strings to use
    @return: Mutants that have the JSON postdata changed with the strings at mutant_str_list
    '''
    # We define a function that creates the mutants...
    def _makeMutants( freq, mutantClass, mutant_str_list, fuzzableParamList , append, jsonPostData):
        res = []
        
        for fuzzed_json, original_value in _fuzzJSON( mutant_str_list, jsonPostData, append ):
        
            # Create the mutants
            freq_copy = freq.copy()
            m = mutantClass( freq_copy ) 
            m.setOriginalValue( original_value )
            m.setVar( 'JSON data' )
            m.setDc( fuzzed_json )
            res.append( m )
            
        return res
        
    # Now we define a function that does the work...
    def _fuzzJSON( mutant_str_list, jsonPostData, append ):
        '''
        @return: A list with tuples containing
        (fuzzed list/dict/string/int that represents a JSON object, original value)
        '''
        res = []
        
        if isinstance(jsonPostData, int):
            for mutant_str in mutant_str_list:
                if mutant_str.isdigit():
                    # This (a mutant str that really is an integer) will happend once every 100000 years, 
                    # but I wanted to be sure to cover all cases. This will look something like:
                    #
                    # 1
                    #
                    # In the postdata.
                    if append:
                        fuzzed = int(str(jsonPostData) +  str(mutant_str))
                        res.append( (fuzzed, str(jsonPostData)) )
                    else:
                        fuzzed = int(mutant_str)
                        res.append( (fuzzed, jsonPostData) )
        
        elif isinstance(jsonPostData, basestring):
            # This will look something like:
            #
            # "abc"
            #
            # In the postdata.
            for mutant_str in mutant_str_list:
                if append:
                    fuzzed = jsonPostData +  mutant_str
                    res.append( (fuzzed, jsonPostData) )
                else:
                    res.append( (mutant_str, jsonPostData) )
                    
                    
        elif isinstance( jsonPostData, list ):
            # This will look something like:
            #
            # ["abc", "def"]
            #
            # In the postdata.
            for item, i in zip( jsonPostData,xrange(len(jsonPostData)) ):
                fuzzed_item_list = _fuzzJSON( mutant_str_list, jsonPostData[i] , append )
                for fuzzed_item, original_value in fuzzed_item_list:
                    jsonPostDataCopy = copy.deepcopy( jsonPostData )
                    jsonPostDataCopy[ i ] = fuzzed_item
                    res.append( (jsonPostDataCopy, original_value) )
        
        elif isinstance( jsonPostData, dict ):
            for key in jsonPostData:
                fuzzed_item_list = _fuzzJSON( mutant_str_list, jsonPostData[key] , append )
                for fuzzed_item, original_value in fuzzed_item_list:
                    jsonPostDataCopy = copy.deepcopy( jsonPostData )
                    jsonPostDataCopy[ key ] = fuzzed_item
                    res.append( (jsonPostDataCopy, original_value) )
        
        return res
    
    # Now, fuzz the parsed JSON data...
    postdata = freq.getData()
    jsonPostData = json.loads( postdata )
    return _makeMutants( freq, mutantClass, mutant_str_list, fuzzableParamList , append, jsonPostData )

def isJSON( freq ):
    # Only do the JSON stuff if this is really a JSON request...
    postdata = freq.getData()
    try:
        cgi.parse_qs( postdata ,keep_blank_values=True,strict_parsing=True)
    except Exception:
        # We have something that's not URL encoded in the postdata, it could be something
        # like JSON, XML, or multipart encoding. Let's try with JSON
        try:
            json.loads( postdata )
        except:
            # It's not json, maybe XML or multipart, I don't really care ( at least not in this section of the code )
            return False
        else:
            # Now, fuzz the parsed JSON data...
            return True
    else:
        # No need to do any JSON stuff, the postdata is urlencoded
        return False
    
def _createFileContentMutants(freq, mutant_str_list, fuzzableParamList, append):
    '''
    @parameter freq: A fuzzable request with a DataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
    @return: Mutants that have the file content changed with the strings at mutant_str_list
    '''
    res = []
    file_vars = freq.getFileVariables()
    
    if file_vars:
        tmp = []
        ext = cf.cf.getData('fuzzFCExt') or 'txt'
        
        for mutant_str in mutant_str_list:
            if isinstance(mutant_str, basestring):
                # I have to create the NamedStringIO with a "name".
                # This is needed for MultipartPostHandler
                fname = "%s.%s" % (createRandAlpha(7), ext)
                str_file = NamedStringIO(mutant_str, name=fname)
                tmp.append(str_file)
        res = _createMutantsWorker(freq, mutantFileContent,
                                   tmp, file_vars, append)
    
    return res
    
def _createFileNameMutants(freq, mutantClass, mutant_str_list, fuzzableParamList, append ):
    '''
    @parameter freq: A fuzzable request with a DataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
    
    @return: Mutants that have the filename URL changed with the strings at mutant_str_list
    
    >>> from core.data.parsers.urlParser import url_object
    >>> from core.data.request.fuzzableRequest import fuzzableRequest
    >>> url = url_object('http://www.w3af.com/abc/def.html')
    >>> fr = fuzzableRequest(url)
    >>> mutant_list = _createFileNameMutants( fr, mutantFileName, ['ping!','pong-'], [], False )
    >>> [ m.getURL().url_string for m in mutant_list]
    [u'http://www.w3af.com/abc/ping%21.html', u'http://www.w3af.com/abc/pong-.html', u'http://www.w3af.com/abc/def.ping%21', u'http://www.w3af.com/abc/def.pong-']
    
    >>> mutant_list = _createFileNameMutants( fr, mutantFileName, ['/etc/passwd',], [], False )
    >>> [ m.getURL().url_string for m in mutant_list]
    [u'http://www.w3af.com/abc/%2Fetc%2Fpasswd.html', u'http://www.w3af.com/abc//etc/passwd.html', u'http://www.w3af.com/abc/def.%2Fetc%2Fpasswd', u'http://www.w3af.com/abc/def./etc/passwd']

    '''
    res = []
    fname = freq.getURL().getFileName()
    fname_chunks = [x for x in re.split(r'([a-zA-Z0-9]+)', fname) if x] 
    
    for idx, fn_chunk in enumerate(fname_chunks):
        
        for mutant_str in mutant_str_list:
            
            if re.match('[a-zA-Z0-9]', fn_chunk):
                divided_fname = DataContainer()
                divided_fname['start'] = ''.join(fname_chunks[:idx])
                divided_fname['end'] = ''.join(fname_chunks[idx+1:])
                divided_fname['fuzzedFname'] = \
                    (fn_chunk if append else '') + urllib.quote_plus(mutant_str)
                
                freq_copy = freq.copy()
                freq_copy.setURL(freq.getURL())
                
                # Create the mutant
                m = mutantClass(freq_copy) 
                m.setOriginalValue(fn_chunk)
                m.setVar('fuzzedFname')
                m.setMutantDc(divided_fname)
                m.setModValue(mutant_str)
                # Special for filename fuzzing and some configurations
                # of mod_rewrite
                m.setDoubleEncoding(False)
                res.append(m)
                
                # The same but with a different type of encoding! (mod_rewrite)
                m2 = m.copy()
                m2.setSafeEncodeChars('/')
                
                if m2.getURL() != m.getURL():
                    res.append(m2)
    return res
    
def _createMutantsWorker(freq, mutantClass, mutant_str_list,
                         fuzzableParamList, append, dataContainer=None):
    '''
    An auxiliary function to createMutants.
    
    @return: A list of mutants.

    >>> from core.data.request.fuzzableRequest import fuzzableRequest
    >>> from core.data.parsers.urlParser import url_object
    >>> from core.data.dc.dataContainer import DataContainer

    Mutant creation
    >>> d = DataContainer()
    >>> d['a'] = ['1',]
    >>> d['b'] = ['2',]
    >>> freq = fuzzableRequest(url_object('http://www.w3af.com/'), dc=d)
    >>> f = _createMutantsWorker( freq, mutantQs, ['abc', 'def'], [], False)
    >>> [ i.getDc() for i in f ]
    [DataContainer({'a': ['abc'], 'b': ['2']}), DataContainer({'a': ['def'], 'b': ['2']}), DataContainer({'a': ['1'], 'b': ['abc']}), DataContainer({'a': ['1'], 'b': ['def']})]

    Append
    >>> d = DataContainer()
    >>> d['a'] = ['1',]
    >>> d['b'] = ['2',]
    >>> freq = fuzzableRequest(url_object('http://www.w3af.com/'), dc=d)
    >>> f = _createMutantsWorker( freq, mutantQs, ['abc', 'def'], [], True)
    >>> [ i.getDc() for i in f ]
    [DataContainer({'a': ['1abc'], 'b': ['2']}), DataContainer({'a': ['1def'], 'b': ['2']}), DataContainer({'a': ['1'], 'b': ['2abc']}), DataContainer({'a': ['1'], 'b': ['2def']})]

    Repeated parameters
    >>> d = DataContainer()
    >>> d['a'] = ['1','2','3']
    >>> freq.setDc(d)
    >>> f = _createMutantsWorker( freq, mutantQs, ['abc', 'def'], [], False)
    >>> [ i.getDc() for i in f ]
    [DataContainer({'a': ['abc', '2', '3']}), DataContainer({'a': ['def', '2', '3']}), DataContainer({'a': ['1', 'abc', '3']}), DataContainer({'a': ['1', 'def', '3']}), DataContainer({'a': ['1', '2', 'abc']}), DataContainer({'a': ['1', '2', 'def']})]

    SmartFill of parameters
    >>> from core.data.dc.form import Form
    >>> from core.data.request.httpPostDataRequest import httpPostDataRequest
    >>> f = Form()
    >>> _ = f.addInput( [("name", "address") , ("type", "text")] )
    >>> _ = f.addInput( [("name", "foo") , ("type", "text")] )
    >>> pdr = httpPostDataRequest(url_object('http://www.w3af.com/'), dc=f)
    >>> f = _createMutantsWorker( pdr, mutantPostData, ['abc', 'def'], [], False)
    >>> [ i.getDc() for i in f ]
    [Form({'address': ['abc'], 'foo': ['56']}), Form({'address': ['def'], 'foo': ['56']}), Form({'address': ['Bonsai Street 123'], 'foo': ['abc']}), Form({'address': ['Bonsai Street 123'], 'foo': ['def']})]

    Support for HTTP requests that have both QS and POST-Data
    >>> f = Form()
    >>> _ = f.addInput( [("name", "password") , ("type", "password")] )
    >>> pdr = httpPostDataRequest(url_object('http://www.w3af.com/foo.bar?action=login'), dc=f)
    >>> mutants = _createMutantsWorker( pdr, mutantPostData, ['abc', 'def'], [], False)
    >>> [ i.getURI() for i in mutants ]
    [<url_object for "http://www.w3af.com/foo.bar?action=login">, <url_object for "http://www.w3af.com/foo.bar?action=login">]
    >>> [ i.getDc() for i in mutants ]
    [Form({'password': ['abc']}), Form({'password': ['def']})]
    '''
    result = []
    if not dataContainer:
        dataContainer = freq.getDc()

    for pname in dataContainer:
        
        #
        # Ignore the banned parameter names
        #
        if pname in IGNORED_PARAMETERS:
            continue
        
        # This for is to support repeated parameter names
        for element_index, element_value in enumerate(dataContainer[pname]):
            
            for mutant_str in mutant_str_list:
                
                # Exclude the file parameters, those are fuzzed in _createFileContentMutants()
                # (if the framework if configured to do so)
                #
                # But if we have a form with files, then we have a multipart form, and we have to keep it
                # that way. If we don't send the multipart form as multipart, the remote programming
                # language may ignore all the request, and the parameter that we are
                # fuzzing (that's not the file content one) will be ignored too
                #
                # The "keeping the multipart form alive" thing is done some lines below, search for
                # the "__HERE__" string!
                #
                # The exclusion is done here:
                if pname in freq.getFileVariables() and not hasattr(mutant_str, 'name'):
                    continue
                    
                # Only fuzz the specified parameters (if any)
                # or fuzz all of them (the fuzzableParamList == [] case)
                if pname in fuzzableParamList or fuzzableParamList == []:
                    
                    dc_copy = dataContainer.copy()
                    original_value = element_value
                    
                    # Ok, now we have a data container with the mutant string, but it's possible that
                    # all the other fields of the data container are empty (think about a form)
                    # We need to fill those in, with something *useful* to get around the easiest
                    # developer checks like: "parameter A was filled".
                    
                    # But I only perform this task in HTML forms, everything else is left as it is:
                    if isinstance(dc_copy, Form):
                        for var_name_dc in dc_copy:
                            for element_index_dc, element_value_dc in enumerate(dc_copy[var_name_dc]):
                                if (var_name_dc, element_index_dc) != (pname, element_index) and\
                                dc_copy.getType(var_name_dc) not in ['checkbox', 'radio', 'select', 'file' ]:
                                    
                                    #   Fill only if the parameter does NOT have a value set.
                                    #
                                    #   The reason of having this already set would be that the form
                                    #   has something like this:
                                    #
                                    #   <input type="text" name="p" value="foobar">
                                    #
                                    if dc_copy[var_name_dc][element_index_dc] == '':
                                        #
                                        #   Fill it smartly
                                        #
                                        dc_copy[var_name_dc][element_index_dc] = smartFill(var_name_dc)

                    # __HERE__
                    # Please see the comment above for an explanation of what we are doing here:
                    for var_name in freq.getFileVariables():
                        # I have to create the NamedStringIO with a "name".
                        # This is needed for MultipartPostHandler
                        fname = "%s.%s" % (createRandAlpha(7), 
                                           cf.cf.getData('fuzzFCExt' ) or 'txt') 
                        str_file = NamedStringIO('', name=fname)
                        dc_copy[var_name][0] = str_file
                    
                    if append:
                        mutant_str = original_value + mutant_str
                    dc_copy[pname][element_index] = mutant_str
                    
                    # Create the mutant
                    freq_copy = freq.copy()
                    m = mutantClass( freq_copy )
                    m.setVar( pname, index=element_index )
                    m.setDc( dc_copy )
                    m.setOriginalValue( original_value )
                    m.setModValue( mutant_str )
                    
                    # Done, add it to the result
                    result.append( m )

    return result
    
def _createUrlPartsMutants(freq, mutantClass, mutant_str_list, fuzzableParamList, append):
    '''
    @parameter freq: A fuzzable request with a DataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
    
    @return: Mutants that have the filename URL changed with the strings at mutant_str_list
    
    >>> from core.data.parsers.urlParser import url_object
    >>> from core.data.request.fuzzableRequest import fuzzableRequest
    >>> url = url_object('http://www.w3af.com/abc/def')
    >>> fr = fuzzableRequest(url)
    >>> mutant_list = _createUrlPartsMutants(fr, mutantUrlParts, ['ping!'], [], False)
    >>> [m.getURL().url_string for m in mutant_list]
    [u'http://www.w3af.com/ping%21/def', u'http://www.w3af.com/ping%2521/def', u'http://www.w3af.com/abc/ping%21', u'http://www.w3af.com/abc/ping%2521']
    
    '''
    res = []
    path_sep = '/'
    path = freq.getURL().getPath()
    path_chunks = path.split(path_sep)
    for idx, p_chunk in enumerate(path_chunks):
        if not p_chunk:
            continue
        for mutant_str in mutant_str_list:
            divided_path = DataContainer()
            divided_path['start'] = path_sep.join(path_chunks[:idx] + [''])
            divided_path['end'] = path_sep.join([''] + path_chunks[idx+1:])
            divided_path['fuzzedUrlParts'] = \
                (p_chunk if append else '') + urllib.quote_plus(mutant_str)
            freq_copy = freq.copy()
            freq_copy.setURL(freq.getURL())
            m = mutantClass(freq_copy) 
            m.setOriginalValue(p_chunk)
            m.setVar('fuzzedUrlParts')
            m.setMutantDc(divided_path)
            m.setModValue(mutant_str)
            res.append(m)
            # Same URLs but with different types of encoding!
            m2 = m.copy()
            m2.setDoubleEncoding(True)
            res.append(m2)
    return res
 
def createRandAlpha(length=0):
    '''
    Create a random string ONLY with letters
    
    @return: A random string only composed by letters.

    >>> x = createRandAlpha( length=10 )
    >>> len(x) == 10
    True
    >>> x = createRandAlpha( length=20 )
    >>> len(x) == 20
    True
    >>> x = createRandAlpha( length=5 )
    >>> y = createRandAlpha( length=5 )
    >>> z = createRandAlpha( length=5 )
    >>> w = createRandAlpha( length=5 )
    >>> x != y != z != w
    True
    '''
    return ''.join(choice(letters) for x in xrange(length or randint(10, 30)))
    
def createRandAlNum(length=0):
    '''
    Create a random string with random length
    
    @return: A random string of with length > 10 and length < 30.

    >>> x = createRandNum( length=10 )
    >>> len(x) == 10
    True
    >>> x = createRandNum( length=20 )
    >>> len(x) == 20
    True
    >>> x = createRandNum( length=5 )
    >>> y = createRandNum( length=5 )
    >>> z = createRandNum( length=5 )
    >>> w = createRandNum( length=5 )
    >>> x != y != z != w
    True
    '''
    jibber = ''.join([letters, digits])
    return ''.join(choice(jibber) for x in xrange(length or randint(10, 30)))

def createRandNum(length=0, excludeNumbers=[]):
    '''
    Create a random string ONLY with numbers
    
    @return: A random string only composed by numbers.

    >>> x = createRandNum( length=1 )
    >>> int(x) in range(10)
    True
    >>> x = createRandNum( length=2 )
    >>> int(x) in range(100)
    True
    >>> x = createRandNum( length=3 )
    >>> int(x) in range(1000)
    True
    '''
    ru = ''.join(choice(digits) for x in xrange(length or randint(10, 30)))
        
    if int(ru) in excludeNumbers:
        try:
            return createRandNum(length, excludeNumbers)
        except:
            # a recursion exceeded could happend here.
            raise w3afException('Failed return random number.')
    return ru
    
def createFormatString(length):
    '''
    @return: A string with $length %s and a final %n
    '''
    result = '%n' * length
    return result

def _createFuzzable(freq):
    '''
    @return: This function verifies the configuration, and creates a map of
        things that can be fuzzed.
    '''
    _fuzzable = {}
    _fuzzable['dc'] = freq.getDc()
    config = cf.cf
    
    # Add the fuzzable headers
    fuzzheaders = dict((h, '') for h in config.getData('fuzzableHeaders', []))
    
    if fuzzheaders:
        _fuzzable['headers'] = fuzzheaders
        
    if config.getData('fuzzableCookie'):     
        _fuzzable['cookie'] = Cookie()
    
    if config.getData('fuzzFileName'):
        _fuzzable['fuzzedFname'] = None
        
    if config.getData('fuzzFileContent'):
        _fuzzable['fuzzFileContent'] = None

    if config.getData('fuzzURLParts'):
        _fuzzable['fuzzURLParts'] = None
    
    return _fuzzable