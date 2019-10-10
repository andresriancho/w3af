"""
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

"""
import hashlib
import json
import os.path

from itertools import repeat, izip
from collections import namedtuple

import w3af.core.controllers.output_manager as om
import w3af.core.data.kb.knowledge_base as kb

from w3af import ROOT_PATH
from w3af.core.controllers.plugins.infrastructure_plugin import InfrastructurePlugin
from w3af.core.controllers.exceptions import NoMoreCalls
from w3af.core.controllers.threads.threadpool import one_to_many
from w3af.core.data.bloomfilter.scalable_bloom import ScalableBloomFilter
from w3af.core.data.kb.info import Info


class php_eggs(InfrastructurePlugin):
    """
    Fingerprint the PHP version using documented easter eggs that exist in PHP.
    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    PHP_EGGS = [('?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000', 'PHP Credits'),
                ('?=PHPE9568F34-D428-11d2-A769-00AA001ACF42', 'PHP Logo'),
                ('?=PHPE9568F35-D428-11d2-A769-00AA001ACF42', 'Zend Logo'),
                ('?=PHPE9568F36-D428-11d2-A769-00AA001ACF42', 'PHP Logo 2')]

    # Empty EGG_DB array, will be filled with external data
    EGG_DB = {}

    def __init__(self):
        InfrastructurePlugin.__init__(self)

        # Already analyzed extensions
        self._already_analyzed_ext = ScalableBloomFilter()

        # Internal DB
        self._db_file = os.path.join(ROOT_PATH, 'plugins', 'infrastructure',
                                     'php_eggs', 'eggs.json')

        # Get data from external JSON file and fill EGG_DB array
        data = self.read_jsondata(self._db_file)
        self.EGG_DB = self.fill_egg_array(data)

    def read_jsondata(self, jsonfile):
        """
        Read a JSON file. File handling for reading a JSON file
        :return: Raw JSON data.
        """
        json_data = open(jsonfile)
        file_data = json.load(json_data)
        json_data.close()
        return file_data

    def fill_egg_array(self, json_egg_data):
        """
        Fill an array with data from a JSON input file.
        :return: An array with PHP-versions with corresponding MD5 hashes.
        """
        egg_db = {}

        for egg in json_egg_data['db']:
            version = egg['version']
            egg_db[version] = {}

            for key in ('credits', 'php_1', 'php_2', 'zend'):
                if key in egg:
                    egg_db[version][key] = egg[key]

        return egg_db

    def discover(self, fuzzable_request, debugging_id):
        """
        Nothing strange, just do some GET requests to the eggs and analyze the
        response.

        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                 (among other things) the URL to test.
        """
        # Get the extension of the URL (.html, .php, .. etc)
        ext = fuzzable_request.get_url().get_extension()

        # Only perform this analysis if we haven't already analyzed this type
        # of extension OR if we get an URL like http://f00b5r/4/     (Note that
        # it has no extension) This logic will perform some extra tests... but
        # we won't miss some special cases. Also, we aren't doing something like
        # "if 'php' in ext:" because we never depend on something so easy to
        # modify as extensions to make decisions.
        if ext not in self._already_analyzed_ext:

            # Now we save the extension as one of the already analyzed
            self._already_analyzed_ext.add(ext)

            # Init some internal variables
            query_results = self._get_php_eggs(fuzzable_request, ext)

            if self._are_php_eggs(query_results):
                # analyze the info to see if we can identify the version
                self._extract_version_from_egg(query_results)
                raise NoMoreCalls

    def _get_php_eggs(self, fuzzable_request, ext):
        """
        HTTP GET the URLs for PHP Eggs
        :return: A list with the HTTP response objects
        """
        def http_get(fuzzable_request, (egg_url, egg_desc)):
            egg_url = fuzzable_request.get_url().uri2url().url_join(egg_url)
            response = self._uri_opener.GET(egg_url, cache=True, grep=False)
            return response, egg_url, egg_desc

        # Send the requests using threads:
        query_results = []

        http_get = one_to_many(http_get)
        fr_repeater = repeat(fuzzable_request)
        args_iterator = izip(fr_repeater, self.PHP_EGGS)
        pool_results = self.worker_pool.imap_unordered(http_get, args_iterator)

        for response, egg_URL, egg_desc in pool_results:
            eqr = EggQueryResult(response, egg_desc, egg_URL)
            query_results.append(eqr)

        return query_results

    def _are_php_eggs(self, query_results):
        """
        Now I analyze if this is really a PHP eggs thing, or simply a response
        that changes a lot on each request. Before, I had something like this:

            if relative_distance(original_response.get_body(),
                                 response.get_body()) < 0.1:

        But I got some reports about false positives with this approach, so now
        I'm changing it to something a little bit more specific.
        """
        images = 0
        not_images = 0

        for query_result in query_results:
            response = query_result.http_response
            content_type, _ = response.get_headers().iget('content-type', '')
            if 'image' in content_type:
                images += 1
            else:
                not_images += 1

        if images >= 2 and not_images == 1:
            #
            # The remote web server has expose_php = On. Report all the findings
            #
            for query_result in query_results:
                desc = ('The PHP framework running on the remote server has a'
                        ' "%s" easter egg, access to the PHP egg is possible'
                        ' through the URL: "%s".')
                desc %= (query_result.egg_desc, query_result.egg_URL)
                
                i = Info('PHP Egg', desc, query_result.http_response.id,
                         self.get_name())
                i.set_url(query_result.egg_URL)
                
                kb.kb.append(self, 'eggs', i)
                om.out.information(i.get_desc())

            return True

        return False

    def _extract_version_from_egg(self, query_results):
        """
        Analyzes the eggs and tries to deduce a PHP version number
        (which is then saved to the kb).
        """
        if not query_results:
            return None
        else:
            desc_hashes = {}

            for query_result in query_results:
                body = query_result.http_response.get_body()
                hash_str = md5_hash(body)
                desc_hashes[query_result.egg_desc] = hash_str

            hash_set = set(desc_hashes.values())

            found = False
            matching_versions = []
            for version in self.EGG_DB:
                version_hashes = set(self.EGG_DB[version].values())

                if len(hash_set) == len(hash_set.intersection(version_hashes)):
                    matching_versions.append(version)
                    found = True

            if matching_versions:

                if len(matching_versions) > 1:
                    desc = ('A PHP easter egg was found that matches several'
                            ' different versions of PHP. The PHP framework'
                            ' version running on the remote server was'
                            ' identified as one of the following:\n- %s')
                else:
                    desc = ('The PHP framework version running on the remote'
                            ' server was identified as:\n- %s')

                versions = '\n- '.join(matching_versions)
                desc %= versions
                
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
                for v in powered_by_headers:
                    if not isinstance(v, basestring):
                        continue

                    if 'php' not in v.lower():
                        continue

                    try:
                        version = v.split('/')[1]
                        break
                    except IndexError:
                        pass

                msg = ('The PHP version could not be identified using PHP eggs,'
                       ' please send this signature and the PHP version to the'
                       ' w3af project develop mailing list. Signature:'
                       ' EGG_DB[\'%s\'] = %r\n')
                msg = msg % (version, desc_hashes)
                om.out.information(msg)

    def get_plugin_deps(self):
        """
        :return: A list with the names of the plugins that should be run before
                 the current one.
        """
        return ['infrastructure.server_header']

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin tries to find the documented easter eggs that exist in PHP
        and identifies the remote PHP version using the easter egg content.
        Known PHP easter eggs are visible in versions 4.0 - 5.4.
        The easter eggs that this plugin verifies are:

        PHP Credits, Logo, Zend Logo, PHP Logo 2:
            - http://php.net/?=PHPB8B5F2A0-3C92-11d3-A3A9-4C7B08C10000
            - http://php.net/?=PHPE9568F34-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F35-D428-11d2-A769-00AA001ACF42
            - http://php.net/?=PHPE9568F36-D428-11d2-A769-00AA001ACF42
        """


def md5_hash(body):
    if isinstance(body, unicode):
        body = body.encode('utf-8')
    return hashlib.md5(body).hexdigest()


EggQueryResult = namedtuple('EggQueryResult', ['http_response',
                                               'egg_desc',
                                               'egg_URL'])
