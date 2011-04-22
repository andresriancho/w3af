'''
phpEggs.py

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
from core.controllers.misc.levenshtein import relative_distance
from core.controllers.w3afException import w3afRunOnce, w3afException

from core.data.bloomfilter.pybloom import ScalableBloomFilter

import core.data.kb.knowledgeBase as kb
import core.data.kb.info as info

import md5


class phpEggs(baseDiscoveryPlugin):
    '''
    Fingerprint the PHP version using documented easter eggs that exist in PHP.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        baseDiscoveryPlugin.__init__(self)
        self._exec = True
        
        # Already analyzed extensions
        self._already_analyzed_ext = ScalableBloomFilter()
        
        # This is a list of hashes and description of the egg for every PHP version.
        self._egg_DB = {}
        self._egg_DB["4.1.2"] = [ 
                ("744aecef04f9ed1bc39ae773c40017d1", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.2.2"] = [ 
                ("758ccaa9094cdeedcfc60017e768137e", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("85be3b4be7bfe839cbb3b4f2d30ff983", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.3.10"] = [ 
                ("1e8fe4ae1bf06be222c1643d32015f0c", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.3.10-18"] = [ 
                ("1e8fe4ae1bf06be222c1643d32015f0c", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.3.11"] = [ 
                ("1e8fe4ae1bf06be222c1643d32015f0c", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("a8ad323e837fa00771eda6b709f40e37", "PHP Logo 2"), 
                ("a8ad323e837fa00771eda6b709f40e37", "Zend Logo") ]
        self._egg_DB["4.3.2"] = [ 
                ("8a8b4a419103078d82707cf68226a482", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.3.8"] = [ 
                ("96714a0fbe23b5c07c8be343adb1ba90", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("a57bd73e27be03a62dd6b3e1b537a72c", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.3.9"] = [ 
                ("f9b56b361fafd28b668cc3498425a23b", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB['4.3.10'] = [
                ('7b27e18dc6f846b80e2f29ecf67e4133', 'PHP Logo'),
                ('43af90bcfa66f16af62744e8c599703d', 'Zend Logo'),
                ('b233cc756b06655f47489aa2779413d7', 'PHP Credits'),
                ('185386dd4b2eff044bd635d22ae7dd9e', 'PHP Logo 2')] 
        self._egg_DB["4.4.0"] = [ 
                ("ddf16ec67e070ec6247ec1908c52377e", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.4.0 for Windows"] = [ 
                ("6d974373683ecfcf30a7f6873f2d234a", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.4.4"] = [ 
                ("bed7ceff09e9666d96fdf3518af78e0e", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.4.4-8+etch6"] = [ 
                ("31a2553efc348a21b85e606e5e6c2424", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["4.4.7"] = [ 
                ("72b7ad604fe1362f1e8bf4f6d80d4edc", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB['4.4.7, PleskWin, ASP.NET'] = [
                ('b8477b9b88e90f12e3200660a70eb765', 'Zend Logo'),
                ('b8477b9b88e90f12e3200660a70eb765', 'PHP Credits'),
                ('b8477b9b88e90f12e3200660a70eb765', 'PHP Logo 2'),
                ('b8477b9b88e90f12e3200660a70eb765', 'PHP Logo')]
        self._egg_DB["4.4.8"] = [ 
                ("4cdfec8ca11691a46f4f63839e559fc5", "PHP Credits"), 
                ("11b9cfe306004fce599a1f8180b61266", "PHP Logo"), 
                ("4b2c92409cf0bcf465d199e93a15ac3f", "PHP Logo 2"), 
                ("da2dae87b166b7709dbd4061375b74cb", "Zend Logo") ]
        self._egg_DB["5.0.3"] = [ 
                ("def61a12c3b0a533146810403d325451", "PHP Credits"), 
                ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"), 
                ("37e194b799d4aaff10e39c4e3b2679a2", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.1.1"] = [ 
                ("5518a02af41478cfc492c930ace45ae5", "PHP Credits"), 
                ("8ac5a686135b923664f64fe718ea55cd", "PHP Logo"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB['5.1.2'] = [
                ('b83433fb99d0bef643709364f059a44a', 'PHP Credits'),
                ('8ac5a686135b923664f64fe718ea55cd', 'PHP Logo'),
                ('4b2c92409cf0bcf465d199e93a15ac3f', 'PHP Logo 2'),
                ('7675f1d01c927f9e6a4752cf182345a2', 'Zend Logo') ]
        self._egg_DB["5.1.6"] = [ 
                ("4b689316409eb09b155852e00657a0ae", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.0"] = [ 
                ("e566715bcb0fd2cb1dc43ed076c091f1", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.0-8+etch10"] = [ 
                ("e566715bcb0fd2cb1dc43ed076c091f1", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.0-8+etch7"] = [ 
                ("307f5a1c02155ca38744647eb94b3543", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.1"] = [ 
                ("d3894e19233d979db07d623f608b6ece", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.2"] = [ 
                ("56f9383587ebcc94558e11ec08584f05", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.3-1+b1"] = [ 
                ("c37c96e8728dc959c55219d47f2d543f", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.4"] = [ 
                ("74c33ab9745d022ba61bc43a5db717eb", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.5"] = [ 
                ("f26285281120a2296072f21e21e7b4b0", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.4-2ubuntu5.3"] = [ 
                ("f26285281120a2296072f21e21e7b4b0", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.5-3"] = [ 
                ("b7e4385bd7f07e378d92485b4722c169", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("0152ed695f4291488741d98ba066d280", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.6"] = [ 
                ("bbd44c20d561a0fc5a4aa76093d5400f", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB["5.2.6RC4-pl0-gentoo"] = [ 
                ("d03b2481f60d9e64cb5c0f4bd0c87ec1", "PHP Credits"), 
                ("c48b07899917dfb5d591032007041ae3", "PHP Logo"), 
                ("50caaf268b4f3d260d720a1a29c5fe21", "PHP Logo 2"), 
                ("7675f1d01c927f9e6a4752cf182345a2", "Zend Logo") ]
        self._egg_DB['5.2.8-pl1-gentoo'] = [
                ('c48b07899917dfb5d591032007041ae3', 'PHP Logo'), 
                ('40410284d460552a6c9e10c1f5ae7223', 'PHP Credits'), 
                ('50caaf268b4f3d260d720a1a29c5fe21', 'PHP Logo 2'), 
                ('7675f1d01c927f9e6a4752cf182345a2', 'Zend Logo')]
        
    def discover(self, fuzzableRequest ):
        '''
        Nothing strange, just do some GET requests to the eggs and analyze the response.
        
        @parameter fuzzableRequest: A fuzzableRequest instance that contains (among other things) the URL to test.
        '''
        if not self._exec:
            # This will remove the plugin from the discovery plugins to be runned.
            raise w3afRunOnce()
        else:
            # Get the extension of the URL (.html, .php, .. etc)
            ext = fuzzableRequest.getURL().getExtension()
            
            # Only perform this analysis if we haven't already analyzed this type of extension
            # OR if we get an URL like http://f00b5r/4/     (Note that it has no extension)
            # This logic will perform some extra tests... but we won't miss some special cases
            # Also, we aren't doing something like "if 'php' in ext:" because we never depend
            # on something so changable as extensions to make decisions.
            if ext == '' or ext not in self._already_analyzed_ext:
                
                # Init some internal variables
                GET_results = []
                original_response = self._urlOpener.GET( fuzzableRequest.getURL(), useCache=True )
                
                # Perform the GET requests to see if we have a phpegg
                for egg, egg_desc in self._get_eggs():
                    egg_URL = fuzzableRequest.getURL().uri2url().urlJoin( egg )
                    try:
                        response = self._urlOpener.GET( egg_URL, useCache=True )
                    except KeyboardInterrupt,e:
                        raise e
                    except w3afException, w3:
                        raise w3
                    else:
                        GET_results.append( (response, egg_desc, egg_URL) )
                        
                #
                #   Now I analyze if this is really a PHP eggs thing, or simply a response that
                #   changes a lot on each request. Before, I had something like this:
                #
                #       if relative_distance(original_response.getBody(), response.getBody()) < 0.1:
                #
                #   But I got some reports about false positives with this approach, so now I'm
                #   changing it to something a little bit more specific.
                images = 0
                not_images = 0
                for response, egg_desc, egg_URL in GET_results:
                    if 'image' in response.getContentType():
                        images += 1
                    else:
                        not_images += 1
                
                if images == 3 and not_images == 1:
                    #
                    #   The remote web server has expose_php = On. Report all the findings.
                    #
                    for response, egg_desc, egg_URL in GET_results:
                        i = info.info()
                        i.setPluginName(self.getName())
                        i.setName('PHP Egg - ' + egg_desc)
                        i.setURL( egg_URL )
                        desc = 'The PHP framework running on the remote server has a "'
                        desc += egg_desc +'" easter egg, access to the PHP egg is possible'
                        desc += ' through the URL: "'+  egg_URL + '".'
                        i.setDesc( desc )
                        kb.kb.append( self, 'eggs', i )
                        om.out.information( i.getDesc() )
                        
                        #   Only run once.
                        self._exec = False
                
                    # analyze the info to see if we can identify the version
                    self._analyze_egg( GET_results )
                
                # Now we save the extension as one of the already analyzed
                if ext != '':
                    self._already_analyzed_ext.add(ext)
        
        return []
    
    def _analyze_egg( self, response ):
        '''
        Analyzes the eggs and tries to deduce a PHP version number
        ( which is then saved to the kb ).
        '''
        if not response:
            return None
        else:
            cmp_list = []
            for r in response:
                cmp_list.append( (md5.new(r[0].getBody()).hexdigest(), r[1] ) )
            cmp_set = set( cmp_list )
            
            found = False
            matching_versions = []
            for version in self._egg_DB:
                version_hashes = set( self._egg_DB[ version ] )
            
                if len( cmp_set ) == len( cmp_set.intersection( version_hashes ) ):
                    matching_versions.append( version )
                    found = True
            
            if matching_versions:
                i = info.info()
                i.setPluginName(self.getName())
                i.setName('PHP Egg')
                msg = 'The PHP framework version running on the remote server was identified as:'
                for m_ver in matching_versions:
                    msg += '\n- ' + m_ver
                i.setDesc( msg )
                i['version'] = matching_versions
                kb.kb.append( self, 'version', i )
                om.out.information( i.getDesc() )

            if not found:
                version = 'unknown'
                powered_by_headers = kb.kb.getData( 'serverHeader' , 'poweredByString' )
                try:
                    for v in powered_by_headers:
                        if 'php' in v.lower():
                            version = v.split('/')[1]
                except:
                    pass
                msg = 'The PHP version could not be identified using PHP eggs, please send this'
                msg += ' signature and the PHP version to the w3af project develop mailing list.'
                msg += ' Signature: self._egg_DB[\''+ version + '\'] = ' + str(list(cmp_set))
                msg += '\n'
                msg += 'The serverHeader plugin reported this PHP version: "' + version + '".'
                om.out.information( msg )
            
    def _get_eggs( self ):
        '''
        @return: A list of tuples with the egg url and a description.
        '''
        res = []
        res.append( ('?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000', 'PHP Credits') )
        res.append( ('?=PHPE9568F34-D428-11d2-A769-00AA001ACF42', 'PHP Logo') )
        res.append( ('?=PHPE9568F35-D428-11d2-A769-00AA001ACF42', 'Zend Logo') )
        res.append( ('?=PHPE9568F36-D428-11d2-A769-00AA001ACF42', 'PHP Logo 2') )
        return res
        
    def getOptions( self ):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol
        
    def setOptions( self, optionsMap ):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter optionsMap: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass
        
    def getPluginDeps( self ):
        '''
        @return: A list with the names of the plugins that should be runned before the
        current one.
        '''
        return ['discovery.serverHeader']
    
    def getLongDesc( self ):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find the documented easter eggs that exist in PHP and identify
        the remote PHP version using the easter egg content. The easter eggs that this plugin
        verifies are:
        
            - http://php.net/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000 ( PHP Credits )
            - http://php.net/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42  ( PHP Logo )
            - http://php.net/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42  ( Zend Logo )
            - http://php.net/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42  ( PHP Logo 2 )
        '''
