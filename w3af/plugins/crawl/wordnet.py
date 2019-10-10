"""
wordnet.py

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
from itertools import chain, repeat, izip

from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
from w3af.core.controllers.misc.fuzzy_string_cmp import fuzzy_not_equal

from w3af.core.data.fuzzer.utils import rand_alpha
from w3af.core.data.fuzzer.mutants.filename_mutant import FileNameMutant
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.nltk_wrapper.nltk_wrapper import wn
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_list import OptionList
from w3af.core.data.request.fuzzable_request import FuzzableRequest


class wordnet(CrawlPlugin):
    """
    Use the wordnet lexical database to find new URLs.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    def __init__(self):
        CrawlPlugin.__init__(self)

        # User defined parameters
        self._wordnet_results = 5

    def crawl(self, fuzzable_request, debugging_id):
        """
        :param debugging_id: A unique identifier for this call to discover()
        :param fuzzable_request: A fuzzable_request instance that contains
                                    (among other things) the URL to test.
        """
        original_response = self._uri_opener.send_mutant(fuzzable_request)
        original_response_repeat = repeat(original_response)

        mutants = self._generate_mutants(fuzzable_request)

        args = izip(original_response_repeat, mutants)

        #   Send the requests using threads:
        self.worker_pool.map_multi_args(self._check_existance, args)

    def _check_existance(self, original_response, mutant):
        """
        Actually check if the mutated URL exists.

        :return: None, all important data is put() to self.output_queue
        """
        response = self._uri_opener.send_mutant(mutant)

        if is_404(response):
            return

        if fuzzy_not_equal(original_response.body, response.body, 0.85):
            
            # Verify against something random
            rand = rand_alpha()
            rand_mutant = mutant.copy()
            rand_mutant.set_token_value(rand)
            rand_response = self._uri_opener.send_mutant(rand_mutant)
            
            if fuzzy_not_equal(response.body, rand_response.body, 0.85):
                
                fr = FuzzableRequest(response.get_uri())
                self.output_queue.put(fr)

    def _generate_mutants(self, fuzzable_request):
        """
        Based on the fuzzable request, i'll search the wordnet database and
        generated A LOT of mutants.

        :return: A list of mutants.
        """
        return chain(self._generate_fname(fuzzable_request),
                     self._generate_qs(fuzzable_request))

    def _generate_qs(self, fuzzable_request):
        """
        Check the URL query string.
        :return: A list of mutants.
        """
        query_string = fuzzable_request.get_uri().querystring
        
        for token in query_string.iter_tokens():
            wordnet_results = self._search_wn(token.get_value())

            mutants = QSMutant.create_mutants(fuzzable_request, wordnet_results,
                                              [token.get_name()], False, {})

            for mutant in mutants:
                yield mutant

    def _search_wn(self, word):
        """
        Search the wordnet for this word, based on user options.

        :return: A list of related words.
        """
        result = []
        
        if not word or word.isdigit():
            return result

        with self._plugin_lock:
            # Now the magic that gets me a lot of results:
            try:
                result.extend(wn.synsets(word)[0].hypernyms()[0].hyponyms())
            except:
                pass
    
            synset_list = wn.synsets(word)
    
            for synset in synset_list:
    
                # first I add the synset as it is:
                result.append(synset)
    
                # Now some variations...
                result.extend(synset.hypernyms())
                result.extend(synset.hyponyms())
                result.extend(synset.member_holonyms())
                result.extend(synset.lemmas()[0].antonyms())

        # Now I have a results list filled up with a lot of words, the problem
        # is that this words are really Synset objects, so I'll transform them
        # to strings:
        result = [i.name().split('.')[0] for i in result]

        # Another problem with Synsets is that the name is "underscore
        # separated" so, for example: "big dog" is "big_dog"
        result = [i.replace('_', ' ') for i in result]

        # Now I make a "uniq"
        result = list(set(result))
        if word in result:
            result.remove(word)

        # The next step is to order each list by popularity, so I only send to
        # the web the most common words, not the strange and unused words.
        result = self._popularity_contest(result)

        # Respect the user settings
        result = result[:self._wordnet_results]

        return result

    def _popularity_contest(self, result):
        """
        :param results: The result map of the wordnet search.
        :return: The same result map, but each item is ordered by popularity
        """
        def sort_function(i, j):
            """
            Compare the lengths of the objects.
            """
            return cmp(len(i), len(j))

        result.sort(sort_function)

        return result

    def _generate_fname(self, fuzzable_request):
        """
        Check the URL filenames
        :return: A list mutants.
        """
        url = fuzzable_request.get_url()
        fname_ext = url.get_file_name()
        splitted_fname_ext = fname_ext.split('.')
        
        if not len(splitted_fname_ext) == 2:
            return []
        
        name = splitted_fname_ext[0]

        wordnet_result = self._search_wn(name)
        
        # Given that we're going to be testing these as filenames, we're
        # going to remove the ones with spaces, since that's very strange
        # to find online
        wordnet_result = [word for word in wordnet_result if ' ' not in word]
        
        fuzzer_config = {'fuzz_url_filenames': True}

        mutants = FileNameMutant.create_mutants(fuzzable_request,
                                                wordnet_result, [0], False,
                                                fuzzer_config)
        
        return mutants

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'Only use the first wnResults (wordnet results) from each category.'
        o = opt_factory('wn_results', self._wordnet_results, d, 'integer')
        ol.add(o)

        return ol

    def set_options(self, options_list):
        """
        This method sets all the options that are configured using the user
        interface generated by the framework using the result of get_options().

        :param options_list: A dictionary with the options for the plugin.
        :return: No value is returned.
        """
        self._wordnet_results = options_list['wn_results'].get_value()

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin finds new URL's using wn.

        An example is the best way to explain what this plugin does, let's
        suppose that the input for this plugin is:
            - http://a/index.asp?color=blue

        The plugin will search the wordnet database for words that are related
        with "blue", and return for example: "black" and "white". So the plugin
        requests this two URL's:
            - http://a/index.asp?color=black
            - http://a/index.asp?color=white

        If the response for those URL's is not a 404 error, and has not the same
        body content, then we have found a new URI. The wordnet database is
        bundled with w3af, more information about wordnet can be found at:
        http://wn.princeton.edu/
        """
