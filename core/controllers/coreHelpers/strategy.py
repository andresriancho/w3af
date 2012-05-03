'''
strategy.py

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
import itertools
import traceback
import Queue
import time

import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
import core.controllers.outputManager as om

from core.controllers.coreHelpers.update_urls_in_kb import update_URLs_in_KB
from core.controllers.threads.threadManager import threadManagerObj as tm
from core.controllers.w3afException import (w3afException, w3afRunOnce,
    w3afMustStopException, w3afMustStopOnUrlError)

from core.data.request.frFactory import createFuzzableRequests
from core.data.db.disk_set import disk_set


class w3af_core_strategy(object):
    '''
    This is the simplest scan strategy which follows this logic:
        
        while new_things_found():
            discovery()
            bruteforce()
        audit(things)
    
    It has been w3af's main algorithm for a while, and what we want to do now
    is to decouple it from the core in order to make experiments and implement
    new algorithms that are more performant.
    
    Use this strategy as a base for your experiments!
    '''
    def __init__(self, w3af_core):
        self._w3af_core = w3af_core
        
        # Internal variables:
        self._fuzzable_request_set  = set()
        kb.kb.save('urls', 'fuzzable_requests', self._fuzzable_request_set)

    def start(self):
        '''
        Starts the work!
        User interface coders: Please remember that you have to call 
        core.plugins.init_plugins() method before calling start.
        
        @return: No value is returned.
        '''
        try:
            self._pre_discovery()
            
            self._fuzzable_request_set.update( self._discover_and_bruteforce() )
            
            if not self._fuzzable_request_set:
                om.out.information('No URLs found during discovery phase.')
                self._w3af_core._end()
            else:
                self._post_discovery()
                self._audit()
                self._w3af_core._end()
            
        except w3afException, e:
            self._w3af_core._end(e)
            raise
        except KeyboardInterrupt, e:
            self._w3af_core._end()
            # I wont handle this, the user interface must know what to do with it
            raise
    
    def _post_discovery(self):
        '''
        This method is called after the discovery and brutefore phases finish
        and performs these things:
            * Cleanup
            * Report results to the user
            * Filter duplicate fuzzable requests
            * Return 
        '''
        # Remove the discovery and bruteforce plugins from memory
        # This is a performance enhancement.
        self._w3af_core.plugins.plugins['discovery'] = []
        self._w3af_core.plugins.plugins['bruteforce'] = []

        # Filter out the fuzzable requests that aren't important 
        # (and will be ignored by audit plugins anyway...)
        #
        #   What I want to do here, is filter the repeated fuzzable requests.
        #   For example, if the spidering process found:
        #       - http://host.tld/?id=3739286
        #       - http://host.tld/?id=3739285
        #       - http://host.tld/?id=3739282
        #       - http://host.tld/?id=3739212
        #
        #   I don't want to have all these different fuzzable requests. The reason is that
        #   audit plugins will try to send the payload to each parameter, thus generating
        #   the following requests:
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #       - http://host.tld/?id=payload1
        #
        #   w3af has a cache, but its still a waste of time to send those requests.
        #
        #   Now lets analyze this with more than one parameter. Spidered URIs:
        #       - http://host.tld/?id=3739286&action=create
        #       - http://host.tld/?id=3739285&action=create
        #       - http://host.tld/?id=3739282&action=remove
        #       - http://host.tld/?id=3739212&action=remove
        #
        #   Generated requests:
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=3739286&action=payload1
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=3739285&action=payload1
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=3739282&action=payload1
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=3739212&action=payload1
        #
        #   In cases like this one, I'm sending these repeated requests:
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=payload1&action=create
        #       - http://host.tld/?id=payload1&action=remove
        #       - http://host.tld/?id=payload1&action=remove
        #   But there is not much I can do about it... (except from having a nice cache)
        #
        #   TODO: Is the previous statement completely true?
        #
        '''filtered_fuzzable_requests = []
        for fr_original in self._fuzzable_request_set:
            
            different_from_all = True
            
            for fr_filtered in filtered_fuzzable_requests:
                if fr_filtered.is_variant_of( fr_original ):
                    different_from_all = False
                    break
            
            if different_from_all:
                filtered_fuzzable_requests.append( fr_original )
        
        self._fuzzable_request_set = filtered_fuzzable_requests
        '''
        # Sort URLs
        tmp_url_list = kb.kb.getData( 'urls', 'url_objects')[:]
        tmp_url_list = list(set(tmp_url_list))
        tmp_url_list.sort()
        
        msg = 'Found %s URLs and %s different points of injection.' 
        msg = msg % (len(tmp_url_list), len(self._fuzzable_request_set))
        om.out.information( msg )
        
        # print the URLs
        om.out.information('The list of URLs is:')
        for i in tmp_url_list:
            om.out.information( '- ' + i )

        # Now I simply print the list that I have after the filter.
        tmp_fr = [ '- ' + str(fr) for fr in self._fuzzable_request_set]
        tmp_fr.sort()

        om.out.information('The list of fuzzable requests is:')
        map(om.out.information, tmp_fr)
              
    def _pre_discovery(self):
        '''
        Create the first fuzzableRequestList
        '''

        # We only want to scan pages that in current scope
        get_curr_scope_pages = lambda fr: \
            fr.getURL().getDomain() == url.getDomain()

        for url in cf.cf.getData('targets'):
            try:
                #
                #    GET the initial target URLs in order to save them
                #    in a list and use them as our bootstrap URLs
                #
                response = self._w3af_core.uriOpener.GET(url, useCache=True)
                self._fuzzable_request_set.update( filter(
                    get_curr_scope_pages, createFuzzableRequests(response)) )

                #
                #    NOTE: I need to perform this test here in order to avoid some weird
                #    thread locking that happens when the webspider calls is_404, and
                #    because I want to initialize the is_404 database in a controlled
                #    try/except block.
                #
                from core.controllers.coreHelpers.fingerprint_404 import is_404
                is_404(response)

            except KeyboardInterrupt:
                self._w3af_core._end()
                raise
            except (w3afMustStopOnUrlError, w3afException, w3afMustStopException), w3:
                om.out.error('The target URL: %s is unreachable.' % url)
                om.out.error('Error description: %s' % w3)
            except Exception, e:
                om.out.error('The target URL: %s is unreachable '
                             'because of an unhandled exception.' % url)
                om.out.error('Error description: "%s". See debug '
                             'output for more information.' % e)
                om.out.error('Traceback for this error: %s' % 
                             traceback.format_exc())
        
        # Load the target URLs to the KB
        update_URLs_in_KB( self._fuzzable_request_set )
                
    def _auth_login(self):
        '''
        Make login to the web app when it is needed.
        '''
        for plugin in self._w3af_core.plugins.plugins['auth']:
            if not plugin.is_logged():
                plugin.login()

    def _discover_and_bruteforce( self ):
        '''
        Discovery and bruteforce phases are related, so I have joined them
        here in this method.
        
        @return: A list with fuzzable requests that were found during discovery
                 and bruteforce.
        '''
        res = set()
        add = res.add
        #TODO: This is a horrible thing to do, we consume lots of memory
        #      for just a loop. The issue is that we had some strange
        #      "RuntimeError: Set changed size during iteration" and I had
        #      no time to solve them.
        tmp_set = set(self._fuzzable_request_set)
        
        while True:
            discovered_fr_list = self._discover( tmp_set )
            successfully_bruteforced = self._bruteforce( discovered_fr_list )

            chain = itertools.chain( discovered_fr_list,
                                     successfully_bruteforced,
                                     self._fuzzable_request_set)
            map(add, chain)
            
            if not successfully_bruteforced:
                # Haven't found new credentials
                break
            else:
                # So in the next "while True:" loop I can do a discovery
                # using the new URLs found during bruteforce
                tmp_set = successfully_bruteforced
                
                # Now I reconfigure the urllib to use the newly found credentials
                self._reconfigureUrllib()
        
        # Update the KB before returning
        update_URLs_in_KB( res )
        
        return res
    
    def _reconfigureUrllib( self ):
        '''
        Configure the main urllib with the newly found credentials.
        '''
        for v in kb.kb.getData( 'basicAuthBrute' , 'auth' ):
            self._w3af_core.uriOpener.settings.setBasicAuth( v.getURL(),
                                                             v['user'],
                                                             v['pass'] )

    def quit(self):
        # End all plugins
        self._w3af_core._end(ignore_err=True)
    
    def stop(self):
        # End all plugins
        self._w3af_core._end(ignore_err=True)
    
    def pause(self, pause_yes_no):
        pass
    
    def _discover(self, to_walk):
        '''
        This method will run the discover_worker, which will run all the discovery
        plugins in a loop in order to find new URLs, forms, web services, etc.
        
        @return: A list of fuzzable requests.
        '''
        # Init some internal variables
        self._w3af_core.status.set_phase('discovery')

        # Run all the discovery plugins        
        result = self._discover_worker( to_walk )
        
        # Let the plugins know that they won't be used anymore
        self._end_discovery()
        
        return result
    
    def _end_discovery( self ):
        '''
        Let the discovery plugins know that they won't be used anymore.
        '''
        for p in self._w3af_core.plugins.plugins['discovery']:
            try:
                p.end()
            except Exception, e:
                om.out.error('The plugin "%s" raised an exception in the '
                             'end() method: %s' % (p.getName(), e))
    
    def get_discovery_time(self):
        '''
        @return: The time between now and the start of the discovery phase in
                 minutes.
        '''
        now = time.time()
        diff = now - self._w3af_core._start_time_epoch
        return diff / 60
    
    def _should_stop_discovery(self):
        '''
        @return: True if we should stop the discovery phase because of time limit
                 set by the user, or simply because the user wants to stop the
                 discovery phase.
        '''
        # If the user wants to stop, I have to stop and at least
        # return the findings I've got until now.
        if self._w3af_core.status.is_stopped():
            return True
        
        if self.get_discovery_time() > cf.cf.getData('maxDiscoveryTime'):
            om.out.information('Maximum discovery time limit hit.')
            return True
        
        return False
    
    def _discover_worker(self, to_walk):
        '''
        This method will run discovery plugins in a loop until no new knowledge
        (ie fuzzable requests) is found.
        
        TODO: unit-test this method
        
        @return: A list with the found fuzzable requests.
        '''
        om.out.debug('Called _discover_worker()' )
        result = []
        
        while to_walk:
            
            # Progress stuff, do this inside the while loop, because the to_walk 
            # variable changes in each loop
            amount_of_tests = len(self._w3af_core.plugins.plugins['discovery']) * len(to_walk)
            self._w3af_core.progress.set_total_amount(amount_of_tests)
            
            plugins_to_remove_list = []
            fuzz_reqs = {}
            
            for plugin in self._w3af_core.plugins.plugins['discovery']:
                
                # Login is needed,
                self._auth_login()
                
                for fr in to_walk:
                    
                    # Should I continue with the discovery phase? If not, return
                    # what I know for now and forget about all the remaining work
                    if self._should_stop_discovery(): return result
                    
                    # Status reporting
                    self._w3af_core.status.set_running_plugin(plugin.getName())
                    self._w3af_core.status.set_current_fuzzable_request(fr)
                    
                    try:
                        try:
                            # Perform the actual work
                            plugin_result = plugin.discover_wrapper(fr)
                        finally:
                            tm.join(plugin)
                    except KeyboardInterrupt:
                        om.out.information('The user interrupted the discovery phase, '
                                           'continuing with audit.')
                        return result
                    except w3afException,e:
                        om.out.error(str(e))
                    except w3afRunOnce:
                        # Some plugins are ment to be run only once
                        # that is implemented by raising a w3afRunOnce
                        # exception
                        plugins_to_remove_list.append(plugin)
                    else:
                        # We don't trust plugins, i'll only work if this
                        # is a list or something else that is iterable
                        lst = fuzz_reqs.setdefault(plugin.getName(), [])
                        if hasattr(plugin_result, '__iter__'):
                            lst.extend(fr for fr in plugin_result)
                                
                    om.out.debug('Ending plugin: ' + plugin.getName())
                    
                    # Finished one loop, inc!
                    self._w3af_core.progress.inc()
            
            # Remove the plugins that don't want to be run anymore
            self._remove_discovery_plugin( plugins_to_remove_list )
            
            # The search has finished - now performing some mangling
            # and filtering with the requests before the next loop
            new_fuzz_reqs = self._filter_mangle_discovery_fr( fuzz_reqs, result )
            result.extend( new_fuzz_reqs )
            
            # Update the list / queue that lives in the KB
            update_URLs_in_KB(new_fuzz_reqs)

            # Get ready for next while loop
            to_walk = new_fuzz_reqs
        
        return result


    def _filter_mangle_discovery_fr(self, fuzz_reqs, result):
        '''
        @param fuzz_reqs: A dict with plugin name as key and fuzzable requests
                          found by the plugin during the last run.
        @param result: The fuzzable requests that were already identified by
                       other discovery plugins during this or previous discovery
                       loops.
        @return: A list with the NEW fuzzable requests that were found, these
                 have been filtered based on the target url, if they are new
                 or not, etc.
        '''
        new_fr = []
        base_urls_cf = cf.cf.getData('baseURLs')
        
        for pname, fuzzable_list in fuzz_reqs.iteritems():
            
            for fr in fuzzable_list:
                fr_uri = fr.getURI()
                # No need to care about fragments
                # (http://a.com/foo.php#frag). Remove them
                fr.setURI(fr_uri.removeFragment())
                
                if fr_uri.baseUrl() in base_urls_cf and\
                fr not in result:
                    # Found a new fuzzable request
                    new_fr.append(fr)
        
            # Print the new URLs in a sorted manner.
            for url in sorted(set(fr.getURL().url_string for fr in new_fr)):
                msg = 'New URL found by %s plugin: %s' % (pname, url)
                om.out.information( msg )
        
        return new_fr
    
    def _remove_discovery_plugin(self, plugins_to_remove_list):            
        '''
        Remove plugins that don't want to be run anymore and raised a w3afRunOnce
        exception during the discovery phase.
        '''
        for plugin_to_remove in plugins_to_remove_list:
            if plugin_to_remove in self._w3af_core.plugins.plugins['discovery']:
                
                # Remove it from the plugin list, and run the end() method
                self._w3af_core.plugins.plugins['discovery'].remove( plugin_to_remove )
                msg = 'The discovery plugin: "%s" wont be run anymore.'
                om.out.debug( msg % plugin_to_remove.getName() )
                try:
                    plugin_to_remove.end()
                except Exception, e:
                    msg = 'The plugin "%s" raised an exception in the end() method: "%s"'
                    om.out.error( msg % (plugin_to_remove.getName(), str(e)) )
                        
    def _audit(self):
        om.out.debug('Called _audit()' )

        enabled_plugins = self._w3af_core.plugins.getEnabledPlugins('audit')
        audit_plugins = self._w3af_core.plugins.plugin_factory( enabled_plugins, 'audit')

        # For progress reporting
        self._w3af_core.status.set_phase('audit')
        amount_of_tests = len(audit_plugins) * len(self._fuzzable_request_set)
        self._w3af_core.progress.set_total_amount( amount_of_tests )

        # This two loops do all the audit magic [KISS]
        for plugin in audit_plugins:

            # For status
            self._w3af_core.status.set_running_plugin( plugin.getName() )

            # Before running each plugin let's make sure we're logged in
            self._auth_login()

            #TODO: This is a horrible thing to do, we consume lots of memory
            #      for just a loop. The issue is that we had some strange
            #      "RuntimeError: Set changed size during iteration" and I had
            #      no time to solve them.
            for fr in set(self._fuzzable_request_set):
                # Sends each fuzzable request to the plugin
                try:
                    self._w3af_core.status.set_current_fuzzable_request( fr )
                    plugin.audit_wrapper( fr )
                except w3afException, e:
                    om.out.error( str(e) )
                finally:
                    tm.join( plugin )
                
                # I performed one test
                self._w3af_core.progress.inc()
                    
            # Let the plugin know that we are not going to use it anymore
            try:
                plugin.end()
            except w3afException, e:
                om.out.error( str(e) )
            
    def _bruteforce(self, fuzzableRequestList):
        '''
        @parameter fuzzableRequestList: A list of fr's to be analyzed by the bruteforce plugins
        @return: A list of the URL's that have been successfully bruteforced
        '''
        res = []
        
        # Progress
        om.out.debug('Called _bruteforce()' )
        self._w3af_core.status.set_phase('bruteforce')
        amount_of_tests = len(self._w3af_core.plugins.plugins['bruteforce']) * len(fuzzableRequestList)
        self._w3af_core.progress.set_total_amount( amount_of_tests )
        
        for plugin in self._w3af_core.plugins.plugins['bruteforce']:
            # FIXME: I should remove this information lines, they duplicate
            #        functionality with the set_running_plugin
            om.out.information('Starting ' + plugin.getName() + ' plugin execution.')
            self._w3af_core.status.set_running_plugin( plugin.getName() )
            for fr in fuzzableRequestList:
                
                # Sends each url to the plugin
                try:
                    self._w3af_core.status.set_current_fuzzable_request( fr )
                    
                    frList = plugin.bruteforce_wrapper( fr )
                    tm.join( plugin )
                except w3afException, e:
                    tm.join( plugin )
                    om.out.error( str(e) )
                    
                # I performed one test (no matter if it failed or not)
                self._w3af_core.progress.inc()                    
                    
                try:
                    plugin.end()
                except w3afException, e:
                    om.out.error( str(e) )
                    
                res.extend( frList )
                
        return res


