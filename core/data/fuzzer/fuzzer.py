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
from core.controllers.w3afException import w3afException

# The data containers
from core.data.dc.cookie import cookie as cookie
from core.data.dc.dataContainer import dataContainer as dc
try:
    import extlib.simplejson as json
except:
    import simplejson as json
from core.data.request.httpPostDataRequest import httpPostDataRequest
from core.data.request.httpQsRequest import httpQsRequest

# import all the mutant types
from core.data.fuzzer.mutantQs import mutantQs
from core.data.fuzzer.mutantPostData import mutantPostData
from core.data.fuzzer.mutantFileName import mutantFileName
from core.data.fuzzer.mutantHeaders import mutantHeaders
from core.data.fuzzer.mutantJSON import mutantJSON
from core.data.fuzzer.mutantCookie import mutantCookie
from core.data.fuzzer.mutantFileContent import mutantFileContent

import core.controllers.outputManager as om

from core.data.dc.form import form


#
#   The following is a list of parameter names that will be ignored during the fuzzing process
#
IGNORED_PARAMETERS = ['__EVENTTARGET', '__EVENTARGUMENT', '__VIEWSTATE', '__VIEWSTATEENCRYPTED', 
                                          '__EVENTVALIDATION', '__dnnVariable', 'javax.faces.ViewState',
                                          'jsf_state_64', 'jsf_sequence', 'jsf_tree', 'jsf_tree_64', 
                                          'jsf_viewid', 'jsf_state', 'cfid', 'cftoken','ASP.NET_sessionid',
                                          'ASPSESSIONID', 'PHPSESSID', 'JSESSIONID']
                                          

def createMutants( freq, mutant_str_list, append=False, fuzzableParamList = [] , oResponse = None ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutant_str_list: a list with mutant strings to use
    @parameter append: This indicates if the content of mutant_str_list should be appended to the variable value
    @parameter fuzzableParamList: If [] then all params are fuzzed. If ['a'] , then only 'a' is fuzzed.
    @return: A Mutant object List.
    '''
    result = []
    
    _fuzzable = _createFuzzable( freq )
    # Query string parameters
    if isinstance( freq, httpQsRequest ):
        om.out.debug('Fuzzing query string')
        result.extend( _createMutantsWorker( freq, mutantQs, mutant_str_list, fuzzableParamList , append ) )
    
    # POST-data parameters
    if isinstance( freq, httpPostDataRequest ):
        # If this is a POST request, it could be a JSON request, and I want to fuzz it !
        om.out.debug('Fuzzing POST data')
        if isJSON( freq ):
            result.extend( _createJSONMutants( freq, mutantJSON, mutant_str_list, fuzzableParamList , append ) )
        else:
            result.extend( _createMutantsWorker( freq, mutantPostData, mutant_str_list, fuzzableParamList , append ) )
    
    # File name
    if 'fuzzedFname' in _fuzzable and isinstance( freq, httpQsRequest ):
        om.out.debug('Fuzzing file name')
        result.extend( _createFileNameMutants( freq, mutantFileName, mutant_str_list, fuzzableParamList , append ) )
    
    # Headers
    if 'headers' in _fuzzable:
        om.out.debug('Fuzzing headers')
        result.extend( _createMutantsWorker( freq, mutantHeaders, mutant_str_list, fuzzableParamList , append, dataContainer=_fuzzable['headers'] ) )
        
    # Cookie values
    if 'cookie' in _fuzzable and freq.getCookie():
        om.out.debug('Fuzzing cookie')
        result.extend( _createMutantsWorker( freq, mutantCookie, mutant_str_list, fuzzableParamList , append, dataContainer=freq.getCookie() ) )
        
    # File content of multipart forms
    if 'fuzzFileContent' in _fuzzable and isinstance( freq, httpPostDataRequest ):
        om.out.debug('Fuzzing file content')
        result.extend( _createFileContentMutants( freq, mutantFileContent, mutant_str_list, fuzzableParamList , append ) )
    
    #
    # Get the original response, and apply it to all mutants
    #
    if oResponse is not None:
        for m in result:
            m.setOriginalResponseBody( oResponse )
        
    return result

def _createJSONMutants( freq, mutantClass, mutant_str_list, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
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
    except Exception, e:
        # We have something that's not URL encoded in the postdata, it could be something
        # like JSON, XML, or multipart encoding. Let's try with JSON
        try:
            jsonPostData = json.loads( postdata )
        except:
            # It's not json, maybe XML or multipart, I don't really care ( at least not in this section of the code )
            return False
        else:
            # Now, fuzz the parsed JSON data...
            return True
    else:
        # No need to do any JSON stuff, the postdata is urlencoded
        return False
    
def _createFileContentMutants( freq, mutantClass, mutant_str_list, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
    @return: Mutants that have the file content changed with the strings at mutant_str_list
    '''
    res = []
    tmp = []
    if freq.getFileVariables():
        for mutant_str in mutant_str_list:
            if type( mutant_str ) == str:
                # I have to create the string_file with a "name" attr. This is needed for MultipartPostHandler
                str_file_instance = string_file( mutant_str )
                extension = cf.cf.getData('fuzzFCExt' ) or 'txt'
                str_file_instance.name = createRandAlpha( 7 ) + '.' + extension
                tmp.append( str_file_instance )
        res = _createMutantsWorker( freq, mutantClass, tmp, freq.getFileVariables() , append )
    return res
    
def _createFileNameMutants( freq, mutantClass, mutant_str_list, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutant_str_list: a list with mutant strings to use
    
    @return: Mutants that have the filename URL changed with the strings at mutant_str_list
    '''
    res = []
    fileName = freq.getURL().getFileName()
    splittedFileName = [ x for x in re.split( r'([a-zA-Z0-9]+)', fileName ) if x != '' ]
    for i in xrange( len( splittedFileName ) ):
        for mutant_str in mutant_str_list:
            if re.match('[a-zA-Z0-9]', splittedFileName[i] ):
                divided_file_name = dc()
                divided_file_name['start'] = ''.join( splittedFileName[: i] )
                if append:
                    divided_file_name['fuzzedFname'] = splittedFileName[i] + urllib.quote_plus( mutant_str )
                else:
                    divided_file_name['fuzzedFname'] = urllib.quote_plus( mutant_str )
                divided_file_name['end'] = ''.join( splittedFileName[i+1:] )
                
                freq_copy = freq.copy()
                freq_copy.setURL( freq.getURL() )
                
                # Create the mutant
                m = mutantClass( freq_copy ) 
                m.setOriginalValue( splittedFileName[i] )
                m.setVar( 'fuzzedFname' )
                m._mutant_dc = divided_file_name
                m.setModValue( mutant_str )
                # Special for filename fuzzing and some configurations of mod_rewrite
                m.setDoubleEncoding( False )
                
                # The same but with a different type of encoding! (mod_rewrite)
                m2 = m.copy()
                m2.setSafeEncodeChars('/')
                
                res.append( m )
                res.append( m2 )
    return res
    
def _createMutantsWorker( freq, mutantClass, mutant_str_list, fuzzableParamList,append, dataContainer=None):
    '''
    An auxiliary function to createMutants.
    
    @return: A list of mutants.
    '''
    result = []
    if not dataContainer:
        dataContainer = freq.getDc()

    for parameter_name in dataContainer:
        
        #
        #   Ignore the banned parameter names
        #
        if parameter_name in IGNORED_PARAMETERS:
            continue
        
        # This for is to support repeated parameter names
        for element_index, element_value in enumerate(dataContainer[parameter_name]):
            
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
                if parameter_name in freq.getFileVariables() and not hasattr(mutant_str, 'name'):
                    continue
                    
                # Only fuzz the specified parameters (if any)
                # or fuzz all of them (the fuzzableParamList == [] case)
                if parameter_name in fuzzableParamList or fuzzableParamList == []:
                    
                    dataContainerCopy = dataContainer.copy()
                    original_value = element_value
                    
                    if append :
                        dataContainerCopy[parameter_name][element_index] += mutant_str
                    else:
                        dataContainerCopy[parameter_name][element_index] = mutant_str

                    # Ok, now we have a data container with the mutant string, but it's possible that
                    # all the other fields of the data container are empty (think about a form)
                    # We need to fill those in, with something *useful* to get around the easiest
                    # developer checks like: "parameter A was filled".
                    
                    # But I only perform this task in HTML forms, everything else is left as it is:
                    if isinstance( dataContainerCopy, form ):
                        for var_name_dc in dataContainerCopy:
                            for element_index_dc, element_value_dc in enumerate(dataContainerCopy[var_name_dc]):
                                if (var_name_dc, element_index_dc) != (parameter_name, element_index) and\
                                dataContainerCopy.getType(var_name_dc) not in ['checkbox', 'radio', 'select', 'file' ]:
                                    
                                    #   Fill only if the parameter does NOT have a value set.
                                    #
                                    #   The reason of having this already set would be that the form
                                    #   has something like this:
                                    #
                                    #   <input type="text" name="p" value="foobar">
                                    #
                                    if dataContainerCopy[var_name_dc][element_index_dc] == '':
                                        #
                                        #   Fill it smartly
                                        #
                                        dataContainerCopy[var_name_dc][element_index_dc] = smartFill(var_name_dc)

                    # __HERE__
                    # Please see the comment above for an explanation of what we are doing here:
                    for var_name in freq.getFileVariables():
                        # I have to create the string_file with a "name" attr.
                        # This is needed for MultipartPostHandler
                        str_file_instance = string_file( '' )
                        extension = cf.cf.getData('fuzzFCExt' ) or 'txt'
                        str_file_instance.name = createRandAlpha( 7 ) + '.' + extension
                        dataContainerCopy[var_name][0] = str_file_instance
                    
                    # Create the mutant
                    freq_copy = freq.copy()
                    m = mutantClass( freq_copy )
                    m.setVar( parameter_name, index=element_index )
                    m.setDc( dataContainerCopy )
                    m.setOriginalValue( original_value )
                    m.setModValue( mutant_str )
                    
                    # Done, add it to the result
                    result.append( m )

    return result
    
def createRandAlpha( length=0 ):
    '''
    Create a random string ONLY with letters
    
    @return: A random string only composed by letters.
    '''
    if length == 0:
        jibber = ''.join([letters])
        ru = ''.join([choice(jibber) for x in range(randint(10, 30))])
    else:
        jibber = ''.join([letters])
        ru = ''.join([choice(jibber) for x in range(length)])
    return ru
    
def createRandAlNum( length=0):
    '''
    Create a random string with random length
    
    @return: A random string of with length > 10 and length < 30.
    '''
    if length == 0:
        jibber = ''.join([letters, digits])
        ru = ''.join([choice(jibber) for x in range(randint(10, 30))])
    else:
        jibber = ''.join([letters, digits])
        ru = ''.join([choice(jibber) for x in range(length)])
    return ru

def createRandNum( length=0, excludeNumbers=[] ):
    '''
    Create a random string ONLY with numbers
    
    @return: A random string only composed by numbers.
    '''
    if length == 0:
        jibber = ''.join([digits])
        ru = ''.join([choice(jibber) for x in range(randint(10, 30))])
    else:
        jibber = ''.join([digits])
        ru = ''.join([choice(jibber) for x in range(length)])
        
    if int(ru) in excludeNumbers:
        try:
            return createRandNum( length, excludeNumbers )
        except:
            # a recursion exceeded could happend here.
            raise w3afException('Failed return random number.')
        
    return ru
    
def createFormatString(  length ):
    '''
    @return: A string with $length %s and a final %n
    '''
    result = '%n' * length
    return result

class string_file( str ):
    isFile = True
    name = ''
    def read( self, size = 0 ):
        return self.__repr__()[1:-1]
        
    def seek( self, foo = 0 ):
        pass
        
def _createFuzzable( freq ):
    '''
    @return: This function verifies the configuration, and creates a map of things that can be fuzzed.
    '''
    _fuzzable = {}
    _fuzzable['dc'] = freq.getDc()
    
    # Add the fuzzable headers
    tmp = {}
    for header in cf.cf.getData('fuzzableHeaders') or []:
        tmp[ header ] = ''
    
    if len( tmp.keys() ):
        _fuzzable['headers'] = tmp
        
    if cf.cf.getData('fuzzableCookie'):     
        _fuzzable['cookie'] = cookie()
    
    if cf.cf.getData('fuzzFileName'):
        _fuzzable['fuzzedFname'] = None
        
    if cf.cf.getData('fuzzFileContent' ):
        _fuzzable['fuzzFileContent'] = None
    
    return _fuzzable
    
from core.data.fuzzer.formFiller import smartFill
