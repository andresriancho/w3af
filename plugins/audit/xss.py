'''
xss.py

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

from core.data.fuzzer.fuzzer import *
import core.controllers.outputManager as om
from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
import core.data.kb.knowledgeBase as kb
from core.controllers.w3afException import w3afException
import core.data.parsers.urlParser as urlParser
import core.data.kb.vuln as vuln
import core.data.constants.severity as severity

class xss(baseAuditPlugin):
    '''
    Find cross site scripting vulnerabilities.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Some internal variables to keep track of remote web application sanitization
        self._fuzzableRequests = []
        self._xssMutants = []
        
        self._reportedDouble = []
        self._reportedSimple = []
        self._reportedLtGt = []
        self._reported = []
        
        self._echoed = []
        self._notEchoed = []
      
        # User configured parameters
        self._checkPersistent = True
        self._numberOfChecks = 2
        
        self._xss_strings_length = len( self._getXssStrings(all=True) )
        
    def _fuzzRequests(self, freq ):
        '''
        Tests an URL for XSS vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug( 'Xss plugin is testing: ' + freq.getURL() )
        self._fuzzableRequests.append( freq )
        
        xssStrings = self._getXssStrings()
        mutantList = createMutants( freq , xssStrings )
            
        for mutant in mutantList:
            
            # verify if the variable we are fuzzing is actually being echoed back
            if self._isEchoed( mutant ):
            
            #if True:
                # This "if True" is here just for testing!
                
                if self._hasNoBug( 'xss', 'xss', mutant.getURL() , mutant.getVar() ):
                    # Only spawn a thread if the mutant has a modified variable
                    # that has no reported bugs in the kb
                    
                    send = True
                    if mutant.getModValue().count('\'') or mutant.getModValue().count('\"'):
                        if (mutant.getVar(), mutant.getURL()) in self._reportedSimple\
                        or (mutant.getVar(), mutant.getURL()) in self._reportedDouble:
                            send = False
    
                    if mutant.getModValue().count('<') or mutant.getModValue().count('>'):
                        if (mutant.getVar(), mutant.getURL()) in self._reportedLtGt:
                            send = False
    
                    if send:
                        targs = (mutant,)
                        self._tm.startFunction( target=self._sendMutant, args=targs, ownerObj=self )
        
    def _getXssStrings( self, all=False ):
        '''
        Does a select to the DB for a list of XSS strings that will be tested agains the site.
        
        @return: A list with all XSS strings to test. Example: [ '<>RANDOMIZE','alert(RANDOMIZE)']
        '''
        xss_strings = []
        ### TODO: analyze http://ha.ckers.org/xss.html and decide what to use
        
        # no quotes
        # The number 2 is to inject in permanent xss and not "letting the user know we are testing the site"
        # And also please note that I don't have this: alert2('abc') ; this "failure" will let me find XSS in web applications
        # that have magic_quotes enabled and will also "double" invalidate the JS code, because RANDOMIZE will be
        # replaced by something like j0a9sf877 and that will be an undefined variables.
        xss_strings.append("<SCRIPT>alert2(RANDOMIZE)</SCRIPT>")
        
        # Single quotes
        xss_strings.append("<SCRIPT>a=/RANDOMIZE/\nalert(a.source)</SCRIPT>")
        
        # http://secunia.com/advisories/9716/
        xss_strings.append("<%00SCRIPT>alert('RANDOMIZE')</SCRIPT>")
        
        xss_strings.append("javascript:alert('RANDOMIZE');")    
        xss_strings.append("JaVaScRiPt:alert('RANDOMIZE');")
        xss_strings.append("javas\tcript:alert('RANDOMIZE');")
        
        # Double quotes
        xss_strings.append('javascript:alert("RANDOMIZE");')
        xss_strings.append('JaVaScRiPt:alert("RANDOMIZE");')
        xss_strings.append('<SCRIPT>alert("RANDOMIZE")</SCRIPT>')
        xss_strings.append('javas\tcript:alert("RANDOMIZE");')
        
        # I need to identify everything I send to the web app
        self._rndValue = createRandAlNum()
        
        if not all:
            xss_strings = xss_strings[:self._numberOfChecks]
        xss_strings = [ x.replace( 'RANDOMIZE', self._rndValue ) for x in xss_strings ]

        return xss_strings
    
    def _isEchoed( self, mutant ):
        '''
        Verify if the parameter we are fuzzing is really being echoed back in the
        HTML response or not. If it aint echoed there is no chance we are going to
        find a XSS here.
        @parameter mutant: The request to send.
        @return: True if variable is echoed
        '''
        if (mutant.getURL(),mutant.getVar()) in self._echoed:
            res = True
        elif (mutant.getURL(),mutant.getVar()) in self._notEchoed:
            res = False
        else:
            dc = mutant.getDc()
            rndNum = str( createRandAlNum( 5 ) )

            oldValue = mutant.getModValue() 
            mutant.setModValue(rndNum)

            response = self._sendMutant( mutant, analyze=False )
            
            # restore the mutant values
            mutant.setModValue(oldValue)

            if response.getBody().count( rndNum ):
                # record that this variable is echoed
                self._echoed.append( (mutant.getURL(),mutant.getVar()) )
                om.out.debug('The variable ' + mutant.getVar() + ' is being echoed back.' )
                res = True
            else:
                # record that this variable aint echoed
                self._notEchoed.append( (mutant.getURL(),mutant.getVar()) )
                om.out.debug('The variable ' + mutant.getVar() + ' is NOT being echoed back.' )
                
                # I return True here, so the FIRST non-echoed value is sent
                # this is for permanent XSS checking. The second time I ask if
                # this is being echoed back, i'll get a false, cause its in the self._notEchoed
                # list.
                res = True
        
        return res
    
    def _analyzeResult( self, mutant, response ):
        # Register the modified qstring that we created for permanent XSS checking
        self._addToPermanentXssChecking( mutant )
        
        htmlString = response.getBody()
        vulnerable = False
        if htmlString.count( mutant.getModValue() ):
                # Ok, we MAY have found a xss. Let's remove some false positives.
                if mutant.getModValue().lower().count( 'javas' ):
                    # I have to check if javascript was written inside a SRC parameter of html
                    # afaik it is the only place this type (<IMG SRC="javascript:alert('XSS');">) of xss works.
                    if self._checkHTML( mutant.getModValue(), htmlString ):
                        vulnerable = True
                else:
                    # Not a javascript type of xss, it's a <SCRIPT>...</SCRIPT> type
                    vulnerable = True
        else:
            # verify filters
            self._checkFilters( mutant, response )
        
        if vulnerable:
            if mutant.getModValue().count('alert2'):
                modValue = mutant.getModValue()
                modValue = modValue.replace('alert2','alert')
                mutant.setModValue( modValue )
                
            v = vuln.vuln( mutant )
            v.setId( response.id )
            v.setName( 'Cross site scripting vulnerability' )
            v.setSeverity(severity.MEDIUM)
            v.setDesc( 'Cross Site Scripting was found at: ' + v.getURL() + ' . Using method: ' + v.getMethod() + '. ' + mutant.printModValue() )

            if (v.getVar(), v.getURL()) in self._reportedLtGt:
                v['escapesLtGt'] = True
            else:
                v['escapesLtGt'] = False
            if (v.getVar(), v.getURL()) in self._reportedSimple:
                v['escapesSingle'] = True
            else:
                v['escapesSingle'] = False
            if (v.getVar(), v.getURL()) in self._reportedDouble:
                v['escapesDouble'] = True                   
            else:
                v['escapesDouble'] = False
            
            kb.kb.append( self, 'xss', v )
    
    def _checkFilters( self, mutant, response ):
        '''
        Check how special chars are filtered or escaped.
        '''
        htmlString = response.getBody()
        if htmlString.count( self._rndValue ):
            # Input is being echoed back to the user. Lets see what filters are being used !
            start = htmlString.find( self._rndValue )
            zone = htmlString[ start -20 : start + 20 ]
            
            for escape in ["\\'",'\\"']:
                if zone.count( escape ):
                    if escape == "\\'" and \
                    (mutant.getVar(), mutant.getURL()) not in self._reportedSimple  and not mutant.dynamicURL():
                        om.out.information('Simple quotes are being escaped using backslashes in parameter ' + \
                        mutant.getVar() + ' in URL ' + mutant.getURL() )
                        self._reportedSimple.append( (mutant.getVar(), mutant.getURL()) )
                        
                    elif escape == '\\"' and \
                    (mutant.getVar(), response.getURL()) not in self._reportedDouble and not mutant.dynamicURL():
                        om.out.information('Double quotes are being escaped using backslashes in parameter ' + \
                        mutant.getVar() + ' in URL ' + mutant.getURL() + '.')
                        self._reportedDouble.append( (mutant.getVar(), mutant.getURL()) )

            for escape in ['&lt;','&gt;']:
                if zone.count( escape ):
                    if (mutant.getVar(), mutant.getURL()) not in self._reportedLtGt and not mutant.dynamicURL():
                        om.out.information('Lower Than and Grater Than symbols are being escaped using html encoding in parameter ' + \
                        mutant.getVar() + ' in URL ' + mutant.getURL() + '.')
                        self._reportedLtGt.append( (mutant.getVar(), mutant.getURL()) )
                        
    def _checkHTML( self, xssString , htmlString ):
        '''
        This function checks if the javascript XSS is going to work or not.
        Examples:
        Request: http://a.com/f.php?a=javascript:alert('XSS');
        HTML Response: <IMG SRC="javascript:alert('XSS');">
        _checkHTML returns True
        
        Request: http://a.com/f.php?a=javascript:alert('XSS');
        HTML Response: I love javascript:alert('XSS');
        _checkHTML returns False
        
        '''
        htmlString = htmlString.replace(' ','')
        xssString = xssString.replace(' ','')
        XssTags = []
        XssTags.extend(['<img','<script'])
        
        whereXssStarts = htmlString.find( xssString )
        for tag in XssTags:
            whereTagStarts = htmlString.rfind( tag , 1, whereXssStarts )
            if whereTagStarts != -1:
                betweenImgAndXss = htmlString[ whereTagStarts+1 : whereXssStarts ]
                if betweenImgAndXss.count('<') or betweenImgAndXss.count('>'):
                    return False
                else:
                    return True
            return False
        
    def _addToPermanentXssChecking( self, mutant ):
        '''
        This is used to check for permanent xss.
        
        @return: No value is returned.
        '''
        self._xssMutants.append( mutant )
        
    def end( self ):
        '''
        This method is called to check for permanent Xss. 
        Many times a xss aint on the page we get after the GET/POST of the xss string.
        This method searches for the xss string on all the pages that are available.
        
        @return: None, vulns are saved to the kb.
        '''
        self._tm.join( self )
        if self._checkPersistent:
            for fr in self._fuzzableRequests:
                response = self._sendMutant( fr, analyze=False )
                
                for mutant in self._xssMutants:
                    if response.getBody().count( mutant.getModValue() ):
                        
                        v = vuln.vuln()
                        v.setURL( fr.getURL() )
                        v.setDc( fr.getDc() )
                        v.setMethod( fr.getMethod() )
                        
                        v['permanent'] = True
                        v['oldMutant'] = mutant
                        if ( v['oldMutant'].getVar(), v['oldMutant'].getURL()) in self._reportedLtGt:
                            v['escapesLtGt'] = True
                        else:
                            v['escapesLtGt'] = False
                        if ( v['oldMutant'].getVar(), v['oldMutant'].getURL()) in self._reportedSimple:
                            v['escapesSingle'] = True
                        else:
                            v['escapesSingle'] = False
                        if ( v['oldMutant'].getVar(), v['oldMutant'].getURL()) in self._reportedDouble:
                            v['escapesDouble'] = True                   
                        else:
                            v['escapesDouble'] = False
                        v.setName( 'Permanent cross site scripting vulnerability' )
                        v.setSeverity(severity.HIGH)
                        v.setDesc( 'Permanent Cross Site Scripting was found at: ' + response.getURL() + ' . Using method: ' + v.getMethod() + '. The XSS was sent to the URL: ' + mutant.getURL()+ '. ' + mutant.printModValue() )
                        v.setId( response.id )
                        kb.kb.append( self, 'xss', v )
                        break
        
        self.printUniq( kb.kb.getData( 'xss', 'xss' ), 'VAR' )

    def getOptionsXML(self):
        '''
        This method returns a XML containing the Options that the plugin has.
        Using this XML the framework will build a window, a menu, or some other input method to retrieve
        the info from the user. The XML has to validate against the xml schema file located at :
        w3af/core/ui/userInterface.dtd
        
        @return: XML with the plugin options.
        ''' 
        return  '<?xml version="1.0" encoding="ISO-8859-1"?>\
        <OptionList>\
            <Option name="checkPersistent">\
                <default>'+str(self._checkPersistent)+'</default>\
                <desc>Search persistent XSS</desc>\
                <help>If set to True, w3af will navigate all pages of the target one more time, searching for persistent cross site scripting bugs.</help>\
                <type>boolean</type>\
            </Option>\
            <Option name="numberOfChecks">\
                <default>'+str(self._numberOfChecks)+'</default>\
                <desc>Set the amount of checks to perform for each fuzzable parameter. Valid numbers: 1 to '+str(self._xss_strings_length)+'.</desc>\
                <help>The XSS checks are ordered, if you set numberOfChecks to two, this plugin will only send two XSS strings to \
                each fuzzable parameter of the remote web application. In most cases this setting is correct and you shouldn\'t\
                change it. If you are really determined and don\'t want to loose the 1% of the vulnerabilities that is left out\
                by this setting, feel free to set this number to '+str(self._xss_strings_length)+'.</help>\
                <type>integer</type>\
            </Option>\
        </OptionList>\
        '

    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptionsXML().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        self._checkPersistent = optionsMap['checkPersistent']
        if optionsMap['numberOfChecks'] >= 1 and optionsMap['numberOfChecks'] <= self._xss_strings_length:
            self._numberOfChecks = optionsMap['numberOfChecks']
        else:
            raise w3afException('Please enter a valid numberOfChecks value (1-'+str(self._xss_strings_length)+').')
        
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
        This plugin finds Cross Site Scripting (XSS) vulnerabilities.
        
        Two configurable parameters exist:
            - checkPersistent
            - checkLevel
            
        To find XSS bugs the plugin will send a set of java-scripts to every injection point, and search for that input in the 
        response. The parameter "checkPersistent" configures the plugin to store all data sent to the web application and
        at the end, request all pages again searching for that input; the checkLevel determines how many javascript
        strings are sent to every injection point.
        '''
