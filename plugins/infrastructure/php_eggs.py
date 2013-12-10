'''
php_eggs.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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
import hashlib
import json

from itertools import repeat, izip
from collections import namedtuple

import core.controllers.output_manager as om
import core.data.kb.knowledge_base as kb

from core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from core.controllers.misc.decorators import runonce
from core.controllers.exceptions import w3afException, w3afRunOnce
from core.controllers.threads.threadpool import one_to_many
from core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from core.data.kb.info import Info


class php_eggs(InfrastructurePlugin):
    '''
    Fingerprint the PHP version using documented easter eggs that exist in PHP.
    :author: Andres Riancho (andres.riancho@gmail.com)
    '''
    PHP_EGGS = [('?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000', 'PHP Credits'),
                ('?=PHPE9568F34-D428-11d2-A769-00AA001ACF42', 'PHP Logo'),
                ('?=PHPE9568F35-D428-11d2-A769-00AA001ACF42', 'Zend Logo'),
                ('?=PHPE9568F36-D428-11d2-A769-00AA001ACF42', 'PHP Logo 2')]

    # PHP versions 4.0.0 - 4.0.6
    # PHP versions 4.1.0 - 4.1.3
    # PHP versions 4.2.0 - 4.2.3
    # PHP versions 4.3.0 - 4.3.11
    # PHP versions 4.4.0 - 4.4.9
    # PHP versions 5.0.0 - 5.0.5
    # PHP versions 5.1.0 - 5.1.6
    # PHP versions 5.2.0 - 5.2.17
    # PHP versions 5.3.0 - 5.3.27
    # PHP versions 5.4.0 - 5.4.22 (still in progress)
    # Remark: PHP versions 5.5.x has no PHP-Eggs.
    # Remark: PHP Logo 2 is not always available. 
    
    # Empty EGG_DB array, will be filled with external data
    EGG_DB = {}

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Already analyzed extensions
        self._already_analyzed_ext = ScalableBloomFilter()

        # User configured parameters
        self._db_file = os.path.join('plugins', 'infrastructure', 'php_eggs', 'eggs.json')

        # Get data from external JSON file and fill EGG_DB array
        data = self.read_jsondata(self._db_file)
        php_eggs.EGG_DB = self.fill_egg_array(data)

    @runonce(exc_class=w3afRunOnce)

    # File handling for reading a JSON file
    def read_jsondata(self,jsonfile):
        '''
        Read a JSON file.
        :return: Raw JSON data. 
        '''
        json_data = open(jsonfile)
        filedata = json.load(json_data)
        json_data.close()
        return filedata

    # Fill EGG array from JSON input file
    def fill_egg_array(self,json_egg_data):
        '''
        Fill an array with data from a JSON input file.
        :return: An array with PHP-versions with corresponding MD5 hashes.
        '''
        egg_array = {}
        for version in json_egg_data['db']:
            egg_array[str(version['version'])] = [
                (str(version['credits']), "PHP Credits"),
                (str(version['php_1']), "PHP Logo"),
                (str(version['php_2']), "PHP Logo 2"),
                (str(version['zend']), "Zend Logo")]
        return egg_array

    def discover(self, fuzzable_request):
        '''
        Nothing strange, just do some GET requests to the eggs and analyze the
        response.

        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        '''
        # Get the extension of the URL (.html, .php, .. etc)
        ext = fuzzable_request.get_url().get_extension()

        # Only perform this analysis if we haven't already analyzed this type
        # of extension OR if we get an URL like http://f00b5r/4/     (Note that
        # it has no extension) This logic will perform some extra tests... but
        # we won't miss some special cases. Also, we aren't doing something like
        # "if 'php' in ext:" because we never depend on something so changable
        # as extensions to make decisions.
        if ext not in self._already_analyzed_ext:

            # Now we save the extension as one of the already analyzed
            self._already_analyzed_ext.add(ext)

            # Init some internal variables
            query_results = self._GET_php_eggs(fuzzable_request, ext)

            if self._are_php_eggs(query_results):
                # analyze the info to see if we can identify the version
                self._extract_version_from_egg(query_results)

    def _GET_php_eggs(self, fuzzable_request, ext):
        '''
        HTTP GET the URLs for PHP Eggs
        :return: A list with the HTTP response objects
        '''
        def http_get(fuzzable_request, (egg_url, egg_desc)):
            egg_URL = fuzzable_request.get_url().uri2url().url_join(egg_url)
            try:
                response = self._uri_opener.GET(egg_URL, cache=True)
            except w3afException, w3:
                raise w3
            else:
                return response, egg_URL, egg_desc

        # Send the requests using threads:
        query_results = []
        EggQueryResult = namedtuple('EggQueryResult', ['http_response',
                                                       'egg_desc',
                                                       'egg_URL'])
        
        http_get = one_to_many(http_get)
        fr_repeater = repeat(fuzzable_request)
        args_iterator = izip(fr_repeater, self.PHP_EGGS)
        pool_results = self.worker_pool.imap_unordered(http_get,
                                                       args_iterator)

        for response, egg_URL, egg_desc in pool_results:
            eqr = EggQueryResult(response, egg_desc, egg_URL)
            query_results.append(eqr)

        return query_results

    def _are_php_eggs(self, query_results):
        '''
        Now I analyze if this is really a PHP eggs thing, or simply a response that
        changes a lot on each request. Before, I had something like this:

            if relative_distance(original_response.get_body(), response.get_body()) < 0.1:

        But I got some reports about false positives with this approach, so now I'm
        changing it to something a little bit more specific.
        '''
        images = 0
        not_images = 0
        for query_result in query_results:
            if 'image' in query_result.http_response.content_type:
                images += 1
            else:
                not_images += 1

        if images == 3 and not_images == 1:
            #
            #   The remote web server has expose_php = On. Report all the findings.
            #
            for query_result in query_results:
                desc = 'The PHP framework running on the remote server has a'\
                       ' "%s" easter egg, access to the PHP egg is possible'\
                       ' through the URL: "%s".'
                desc = desc % (query_result.egg_desc, query_result.egg_URL)
                
                i = Info('PHP Egg', desc, query_result.http_response.id, self.get_name())
                i.set_url(query_result.egg_URL)
                
                kb.kb.append(self, 'eggs', i)
                om.out.information(i.get_desc())

            return True

        return False

    def _extract_version_from_egg(self, query_results):
        '''
        Analyzes the eggs and tries to deduce a PHP version number
        ( which is then saved to the kb ).
        '''
        if not query_results:
            return None
        else:
            cmp_list = []
            for query_result in query_results:
                body = query_result.http_response.get_body()
                if isinstance(body, unicode): body = body.encode('utf-8')
                hash_str = hashlib.md5(body).hexdigest()
                
                cmp_list.append((hash_str, query_result.egg_desc))
                
            cmp_set = set(cmp_list)

            found = False
            matching_versions = []
            for version in self.EGG_DB:
                version_hashes = set(self.EGG_DB[version])

                if len(cmp_set) == len(cmp_set.intersection(version_hashes)):
                    matching_versions.append(version)
                    found = True

            if matching_versions:
                desc = 'The PHP framework version running on the remote'\
                       ' server was identified as:\n- %s'
                versions = '\n- '.join(matching_versions)
                desc = desc % versions
                
                response_ids = [r.http_response.get_id() for r in query_results]
                
                i = Info('Fingerprinted PHP version', desc, response_ids,
                         self.get_name())
                i['version'] = matching_versions
                
                kb.kb.append(self, 'version', i)
                om.out.information(i.get_desc())

            if not found:
                version = 'unknown'
                powered_by_headers = kb.kb.raw_read('server_header',
                                                    'powered_by_string')
                try:
                    for v in powered_by_headers:
                        if 'php' in v.lower():
                            version = v.split('/')[1]
                except:
                    pass
                
                msg = 'The PHP version could not be identified using PHP eggs,'\
                      ', please send this signature and the PHP version to the'\
                      ' w3af project develop mailing list. Signature:'\
                      ' EGG_DB[\'%s\'] = %s\n'
                msg = msg % (version, str(list(cmp_set)))
                om.out.information(msg)

    def get_plugin_deps(self):
        '''
        :return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return ['infrastructure.server_header']

    def get_long_desc(self):
        '''
        :return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin tries to find the documented easter eggs that exist in PHP
        and identifies the remote PHP version using the easter egg content.
        Known PHP easter eggs are visible in versions 4.0 - 5.4.
        The easter eggs that this plugin verifies are:

        PHP Credits, Logo, Zend Logo, PHP Logo 2:
            - http://php.net/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000
            - http://php.net/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42
        '''
