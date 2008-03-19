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
from core.data.parsers import urlParser as urlParser

# Common modules
import copy
import re
import urllib
import cgi
from core.controllers.w3afException import w3afException

# The data containers
from core.data.dc.cookie import cookie as cookie
from core.data.dc.dataContainer import dataContainer as dc
from extlib.jsonpy import json as json
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

def createMutants( freq, mutantStrList, append=False, fuzzableParamList = [] , oResponse = None ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantStrList: a list with mutant strings to use
    @parameter append: This indicates if the content of mutantStrList should be appended to the variable value
    @parameter fuzzableParamList: If [] then all params are fuzzed. If ['a'] , then only 'a' is fuzzed.
    @return: A Mutant object List.
    '''
    result = []
    
    _fuzzable = _createFuzzable( freq )
    if isinstance( freq, httpQsRequest ):
        result.extend( _createMutantsWorker( freq, mutantQs, mutantStrList, fuzzableParamList , append ) )
    if isinstance( freq, httpPostDataRequest ):
        if isJSON( freq ):
            # If this is a POST request, it could be a JSON request, and I want to fuzz it !
            result.extend( _createJSONMutants( freq, mutantJSON, mutantStrList, fuzzableParamList , append ) )
        else:
            result.extend( _createMutantsWorker( freq, mutantPostData, mutantStrList, fuzzableParamList , append ) )
        
    if 'fuzzedFname' in _fuzzable and isinstance( freq, httpQsRequest ):
        result.extend( _createFileNameMutants( freq, mutantFileName, mutantStrList, fuzzableParamList , append ) )
    if 'headers' in _fuzzable:
        result.extend( _createMutantsWorker( freq, mutantHeaders, mutantStrList, fuzzableParamList , append, dataContainer=_fuzzable['headers'] ) )
    if 'cookie' in _fuzzable and freq.getCookie():
        result.extend( _createMutantsWorker( freq, mutantCookie, mutantStrList, fuzzableParamList , append, dataContainer=freq.getCookie() ) )
    if 'fuzzFileContent' in _fuzzable and isinstance( freq, httpPostDataRequest ):
        result.extend( _createFileContentMutants( freq, mutantFileContent, mutantStrList, fuzzableParamList , append ) )
    
    # Get the original response, and apply it to all mutants
    if oResponse:
        for m in result:
            m.setOriginalResponseBody( oResponse )
    
    return result

def _createJSONMutants( freq, mutantClass, mutantStrList, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutantStrList: a list with mutant strings to use
    @return: Mutants that have the JSON postdata changed with the strings at mutantStrList
    '''
    # We define a function that creates the mutants...
    def _makeMutants( freq, mutantClass, mutantStrList, fuzzableParamList , append, jsonPostData):
        res = []
        
        for fuzzed in _fuzzJSON( mutantStrList, jsonPostData, append ):
        
            # Create the mutants
            freqCopy = freq.copy()
            m = mutantClass( freqCopy ) 
            m.setOriginalValue( jsonPostData )
            m.setVar( 'JSON data' )
            m.setDc( fuzzed )
            res.append( m )
            
        return res
        
    # Now we define a function that does the work...
    def _fuzzJSON( mutantStrList, jsonPostData, append ):
        res = []
        
        if isinstance(jsonPostData, int):
            for mutantStr in mutantStrList:
                if mutantStr.isdigit():
                    # This (a mutant str that really is an integer) will happend once every 100000 years, 
                    # but I wanted to be sure to cover all cases
                    if append:
                        res.append( int(str(jsonPostData) +  str(mutantStr)) )
                    else:
                        res.append( int(mutantStr) )
        
        elif isinstance(jsonPostData, basestring):
            for mutantStr in mutantStrList:
                if append:
                    res.append( jsonPostData +  mutantStr )
                else:
                    res.append( mutantStr )
                    
                    
        elif isinstance( jsonPostData, list ):
            for item, i in zip( jsonPostData,xrange(len(jsonPostData)) ):
                fuzzedItemList = _fuzzJSON( mutantStrList, jsonPostData[i] , append )
                for fuzzedItem in fuzzedItemList:
                    jsonPostDataCopy = copy.deepcopy( jsonPostData )
                    jsonPostDataCopy[ i ] = fuzzedItem
                    res.append( jsonPostDataCopy )
        
        elif isinstance( jsonPostData, dict ):
            for key in jsonPostData:
                fuzzedItemList = _fuzzJSON( mutantStrList, jsonPostData[key] , append )
                for fuzzedItem in fuzzedItemList:
                    jsonPostDataCopy = copy.deepcopy( jsonPostData )
                    jsonPostDataCopy[ key ] = fuzzedItem
                    res.append( jsonPostDataCopy )
        
        return res
    
    # Now, fuzz the parsed JSON data...
    postdata = freq.getData()
    jsonPostData = json.read( postdata )
    return _makeMutants( freq, mutantClass, mutantStrList, fuzzableParamList , append, jsonPostData )

def isJSON( freq ):
    # Only do the JSON stuff if this is really a JSON request...
    postdata = freq.getData()
    try:
        cgi.parse_qs( postdata ,keep_blank_values=True,strict_parsing=True)
    except Exception, e:
        # We have something that's not URL encoded in the postdata, it could be something
        # like JSON, XML, or multipart encoding. Let's try with JSON
        try:
            jsonPostData = json.read( postdata )
        except:
            # It's not json, maybe XML or multipart, I don't really care ( at least not in this section of the code )
            return False
        else:
            # Now, fuzz the parsed JSON data...
            return True
    else:
        # No need to do any JSON stuff, the postdata is urlencoded
        return False
    
def _createFileContentMutants( freq, mutantClass, mutantStrList, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutantStrList: a list with mutant strings to use
    @return: Mutants that have the file content changed with the strings at mutantStrList
    '''
    res = []
    if freq.getFileVariables():
        for mutantStr in mutantStrList:
            if type( mutantStr ) == str:
                # I have to create the fileStr with a "name" attr. This is needed for MultipartPostHandler
                fStr = fileStr( mutantStr )
                extension = cf.cf.getData('fuzzFCExt' ) or 'txt'
                fStr.name = createRandAlpha( 7 ) + '.' + extension
                mutantStrList.append( fStr )
        res.extend( _createMutantsWorker( freq, mutantClass, mutantStrList, freq.getFileVariables() , append ) )
    return res
    
def _createFileNameMutants( freq, mutantClass, mutantStrList, fuzzableParamList , append ):
    '''
    @parameter freq: A fuzzable request with a dataContainer inside.
    @parameter mutantClass: The class to use to create the mutants
    @parameter fuzzableParamList: What parameters should be fuzzed
    @parameter append: True/False, if we should append the value or replace it.
    @parameter mutantStrList: a list with mutant strings to use
    @return: Mutants that have the filename URL changed with the strings at mutantStrList
    '''
    res = []
    fileName = urlParser.getFileName( freq.getURL() )
    splittedFileName = [ x for x in re.split( r'([a-zA-Z0-9]+)', fileName ) if x != '' ]
    for i in xrange( len( splittedFileName ) ):
        for mutantStr in mutantStrList:
            if re.match('[a-zA-Z0-9]', splittedFileName[i] ):
                dividedFileName = dc()
                dividedFileName['start'] = ''.join( splittedFileName[: i] )
                if append:
                    dividedFileName['fuzzedFname'] = splittedFileName[i] + urllib.quote_plus( mutantStr )
                else:
                    dividedFileName['fuzzedFname'] = urllib.quote_plus( mutantStr )
                dividedFileName['end'] = ''.join( splittedFileName[i+1:] )
                
                freqCopy = freq.copy()
                freqCopy.setURL( urlParser.getDomainPath( freq.getURL() ) )
                
                # Create the mutant
                m = mutantClass( freqCopy ) 
                m.setOriginalValue( splittedFileName[i] )
                m.setVar( 'fuzzedFname' )
                m.setDc( dividedFileName )
                m.setModValue( mutantStr )
                # Special for filename fuzzing and some configurations of mod_rewrite
                m.setDoubleEncoding( False )
                
                # The same but with a different type of encoding! (mod_rewrite)
                m2 = m.copy()
                m2.setSafeEncodeChars('/')
                
                res.append( m )
                res.append( m2 )
    return res
    
def _createMutantsWorker( freq, mutantClass, mutantStrList, fuzzableParamList,append, dataContainer=None):
    '''
    An auxiliary function to createMutants.
    '''
    result = []
    
    if not dataContainer:
        dataContainer = freq.getDc()
        
    for var_to_mod in dataContainer.keys():
        for mutantStr in mutantStrList:
            
            # Only fuzz the specified parameters
            if var_to_mod in fuzzableParamList or fuzzableParamList == []:
                
                dataContainerCopy = dataContainer.copy()
                originalValue = dataContainer[var_to_mod]
                
                if append :
                    dataContainerCopy[var_to_mod] = dataContainerCopy[var_to_mod] + mutantStr
                else:
                    dataContainerCopy[var_to_mod] = mutantStr
                
                # Create the mutant
                freqCopy = freq.copy()
                m = mutantClass( freqCopy )
                m.setVar( var_to_mod )
                m.setDc( dataContainerCopy )
                m.setOriginalValue( originalValue )
                m.setModValue( mutantStr )
                
                # Done, add it to the result
                result.append ( m )
                
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

class fileStr( str ):
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
