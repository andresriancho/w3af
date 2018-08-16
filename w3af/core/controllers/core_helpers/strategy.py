"""
strategy.py

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
import sys
import time
import Queue

from multiprocessing import TimeoutError

import w3af.core.data.kb.config as cf
import w3af.core.data.kb.knowledge_base as kb
import w3af.core.controllers.output_manager as om

from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.extended_urllib import MAX_ERROR_COUNT
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.info import Info

from w3af.core.controllers.core_helpers.consumers.grep import grep
from w3af.core.controllers.core_helpers.consumers.auth import auth
from w3af.core.controllers.core_helpers.consumers.audit import audit
from w3af.core.controllers.core_helpers.consumers.bruteforce import bruteforce
from w3af.core.controllers.core_helpers.consumers.seed import seed
from w3af.core.controllers.core_helpers.consumers.crawl_infrastructure import CrawlInfrastructure
from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.core_helpers.exception_handler import ExceptionData

from w3af.core.controllers.exceptions import (ScanMustStopException,
                                              ScanMustStopByUserRequest)


class CoreStrategy(object):
    """
    This is the simplest scan strategy which follows this logic:

        while new_things_found():
            discovery()
            bruteforce()
        audit(things)

    It has been w3af's main algorithm for a while, and what we want to do now
    is to decouple it from the core in order to make experiments and implement
    new / faster algorithms.

    Use this strategy as a base for your experiments!
    """
    def __init__(self, w3af_core):
        self._w3af_core = w3af_core
        
        # Consumer threads
        self._grep_consumer = None
        self._audit_consumer = None
        self._auth_consumer = None

        # Producer/consumer threads
        self._discovery_consumer = None
        self._bruteforce_consumer = None

        # Producer threads
        self._seed_producer = seed(self._w3af_core)

        # Also use this method to clear observers
        self._observers = []

    def get_grep_consumer(self):
        return self._grep_consumer

    def get_audit_consumer(self):
        return self._audit_consumer

    def get_discovery_consumer(self):
        return self._discovery_consumer

    def get_bruteforce_consumer(self):
        return self._bruteforce_consumer

    def set_consumers_to_none(self):
        # Consumer threads
        self._grep_consumer = None
        self._audit_consumer = None
        self._auth_consumer = None

        # Producer/consumer threads
        self._discovery_consumer = None
        self._bruteforce_consumer = None

        # Producer threads
        self._seed_producer = seed(self._w3af_core)

        # Also use this method to clear observers
        self._observers = []

    def start(self):
        """
        Starts the work!
        User interface coders: Please remember that you have to call
        core.plugins.init_plugins() method before calling start.

        :return: No value is returned.
        """
        try:
            self.verify_target_server_up()
            self.alert_if_target_is_301_all()
            
            self._setup_grep()
            self._setup_auth()
            self._setup_crawl_infrastructure()
            self._setup_audit()
            self._setup_bruteforce()

            self._setup_observers()
            self._setup_404_detection()

            self._seed_discovery()

            self._fuzzable_request_router()

        except Exception, e:

            om.out.debug('strategy.start() found exception "%s"' % e)
            exc_info = sys.exc_info()

            try:
                # Terminate the consumers, exceptions at this level stop the scan
                self.terminate()
            except Exception, e:
                msg = 'strategy.start() found exception while terminating workers "%s"'
                om.out.debug(msg % e)
            finally:
                # While the consumers might have finished, they certainly queue
                # tasks in the core's worker_pool, which need to be processed
                # too
                self._w3af_core.worker_pool.finish()

            raise exc_info[0], exc_info[1], exc_info[2]

        else:
            # Wait for all consumers to finish
            self.join_all_consumers()

            # While the consumers might have finished, they certainly queue
            # tasks in the core's worker_pool, which need to be processed too
            self._w3af_core.worker_pool.finish()

            # And also teardown all the observers
            self._teardown_observers()

    def stop(self):
        self.terminate()
        
    def pause(self, pause_yes_no):
        # FIXME: Consumers should have something to do with this, most likely
        # another constant similar to the poison pill
        pass

    def terminate(self):
        """
        Consume (without processing) all queues with data which are in
        the consumers and then send a poison-pill to that queue.
        """
        consumers = {'discovery', 'audit', 'auth', 'bruteforce', 'grep'}

        for consumer in consumers:

            consumer_inst = getattr(self, '_%s_consumer' % consumer)

            if consumer_inst is not None:
                om.out.debug('Calling terminate() on %s consumer' % consumer)
                start = time.time()

                # Set it immediately to None to avoid any race conditions where
                # the terminate() method is called twice (from different
                # threads) and before the first call finishes
                #
                # The getattr/setattr tricks are required to make sure that "the
                # real consumer instance" is set to None. Do not modify unless
                # you know what you're doing!
                setattr(self, '_%s_consumer' % consumer, None)

                try:
                    consumer_inst.terminate()
                except Exception, e:
                    msg = '%s consumer terminate() raised exception: "%s"'
                    om.out.debug(msg % e)
                else:
                    spent = time.time() - start
                    args = (consumer, spent)
                    om.out.debug('terminate() on %s consumer took %.2f seconds' % args)

        self.set_consumers_to_none()

    def join_all_consumers(self):
        """
        Wait for the consumers to process all their work, the order seems to be
        important (not actually verified nor tested) but basically we first
        finish the consumers that generate URLs and then the ones that consume
        them.
        """
        om.out.debug('Joining all consumers (teardown phase)')

        self._teardown_crawl_infrastructure()        
        
        self._teardown_audit()
        self._teardown_bruteforce()
                
        self._teardown_auth()
        self._teardown_grep()

    def clear_queue_speed_data(self):
        """
        When one of the consumers finishes its work the speed of all queues is
        heavily impacted. A few examples:
            * Crawl finishes: The audit input queue speed goes to zero
            * Crawl and audit finish: The grep input queue speed goes to zero

        In order to quickly clear the previous state of the queue and reflect
        the new speed, it is important to clear the old (now useless data) which
        is used to calculate the input / output speeds and is now useless since
        the number of consumers has changed.
        """
        consumers = [
            self.get_grep_consumer(),
            self.get_audit_consumer(),
            self.get_discovery_consumer(),
            self.get_bruteforce_consumer()
        ]

        consumers = [c for c in consumers if c is not None]
        [c.in_queue.clear() for c in consumers]

    def add_observer(self, observer):
        self._observers.append(observer)

    def _setup_observers(self):
        """
        "Forward" the observer to the consumers
        :return: None
        """
        for consumer in {self._audit_consumer,
                         self._bruteforce_consumer,
                         self._discovery_consumer,
                         self._grep_consumer}:
            if consumer is not None:
                for observer in self._observers:
                    consumer.add_observer(observer)

    def _fuzzable_request_router(self):
        """
        This is one of the most important methods, it will take things from the
        discovery Queue and store them in one or more Queues (audit, bruteforce,
        etc).

        Also keep in mind that is one of the only methods that will be run in
        the "main thread" and lives during the whole scan process.
        """
        _input = [self._seed_producer,
                  self._discovery_consumer,
                  self._bruteforce_consumer]
        _input = filter(None, _input)

        output = [self._audit_consumer,
                  self._discovery_consumer,
                  self._bruteforce_consumer]
        output = filter(None, output)

        # Only check if these have exceptions and bring them to the main
        # thread in order to be handled by the ExceptionHandler and the
        # w3afCore
        _other = [self._audit_consumer,
                  self._auth_consumer,
                  self._grep_consumer]
        _other = filter(None, _other)

        finished = set()
        consumer_forced_end = set()

        while True:
            # Get results and handle exceptions
            self._handle_all_consumer_exceptions(_other)

            # Route fuzzable requests
            route_result = self._route_one_fuzzable_request_batch(_input,
                                                                  output,
                                                                  finished,
                                                                  consumer_forced_end)

            if route_result is None:
                break

            finished, consumer_forced_end = route_result

    def _route_one_fuzzable_request_batch(self, _input, output, finished,
                                          consumer_forced_end):
        """
        Loop once through all input consumers and route their results.

        :return: (finished, consumer_forced_end) or None if we shouldn't call
                 this method anymore.
        """
        for url_producer in _input:

            if len(_input) == len(finished | consumer_forced_end):
                return

            # No more results in the output queue, and had no pending work on
            # the previous loop.
            if url_producer in finished:
                continue

            # Did the producer send a POISON_PILL?
            if url_producer in consumer_forced_end:
                continue

            try:
                result_item = url_producer.get_result(timeout=0.1)
            except (TimeoutError, Queue.Empty) as _:
                if not url_producer.has_pending_work():
                    # This consumer is saying that it doesn't have any
                    # pending or in progress work
                    finished.add(url_producer)
                    om.out.debug('Producer %s has finished' % url_producer.get_name())
            else:
                if result_item == POISON_PILL:
                    # This consumer is saying that it has finished, so we
                    # remove it from the list.
                    consumer_forced_end.add(url_producer)
                    om.out.debug('Producer %s has finished' % url_producer.get_name())
                elif isinstance(result_item, ExceptionData):
                    self._handle_consumer_exception(result_item)
                else:
                    _, _, fuzzable_request_inst = result_item

                    # Safety check, I need these to be FuzzableRequest objects
                    # if not, the url_producer is doing something wrong and I
                    # don't want to do anything with this data
                    fmt = ('%s is returning objects of class %s instead of'
                           ' FuzzableRequest.')
                    msg = fmt % (url_producer, type(fuzzable_request_inst))
                    assert isinstance(fuzzable_request_inst, FuzzableRequest), msg

                    for url_consumer in output:
                        url_consumer.in_queue_put(fuzzable_request_inst)

                    # This is rather complex to digest... so pay attention :)
                    #
                    # A consumer might be 100% idle (no tasks in input or
                    # output queues, no in progress work) and we still need
                    # to keep it alive, because output from another producer
                    # will be sent to that consumer and make it work again
                    #
                    # So, when one producer returns something, we set the
                    # finished list to empty in order to make them work again
                    finished = set()

        return finished, consumer_forced_end

    def _handle_all_consumer_exceptions(self, _other):
        """
        Get the exceptions raised by the consumers that do not return any
        data under normal circumstances, for example: grep and auth and handle
        them properly.
        """
        for other_consumer in _other:
            try:
                result_item = other_consumer.get_result(timeout=0.2)
            except TimeoutError:
                pass
            except Queue.Empty:
                pass
            else:
                if isinstance(result_item, ExceptionData):
                    self._handle_consumer_exception(result_item)

    def _handle_consumer_exception(self, exception_data):
        """
        Give proper handling to an exception that was raised by one of the
        consumers. Usually this means calling the ExceptionHandler which
        will decide what to do with it.

        Please note that ExtendedUrllib can raise a ScanMustStopByUserRequest
        which should get through this piece of code and be re-raised in order to
        reach the try/except clause in w3afCore's start.
        """
        self._w3af_core.exception_handler.handle_exception_data(exception_data)

    def verify_target_server_up(self):
        """
        Well, it is more common than expected that the user configures a target
        which is offline, is not a web server, etc. So we're going to verify
        all that before even starting our work, and provide a nice error message
        so that users can change their config if needed.
        
        Note that we send MAX_ERROR_COUNT tests to the remote end in order to
        trigger any errors in the remote end and have the Extended URL Library
        error handle return errors.
        
        :raises: A friendly exception with lots of details of what could have
                 happen.
        """
        sent_requests = 0
        
        msg = ('The remote web server is not answering our HTTP requests,'
               ' multiple errors have been found while trying to GET a response'
               ' from the server.\n\n'
               'In most cases this means that the configured target is'
               ' incorrect, the port is closed, there is a firewall blocking'
               ' our packets or there is no HTTP daemon listening on that'
               ' port.\n\n'
               'Please verify your target configuration and try again. The'
               ' tested targets were:\n\n'
               ' %s\n')

        targets = cf.cf.get('targets')

        while sent_requests < MAX_ERROR_COUNT * 1.5:
            for url in targets:
                try:
                    self._w3af_core.uri_opener.GET(url, cache=False)
                except ScanMustStopByUserRequest:
                    # Not a real error, the user stopped the scan
                    raise
                except Exception, e:
                    dbg = 'Exception found during verify_target_server_up: "%s"'
                    om.out.debug(dbg % e)

                    target_list = '\n'.join(' - %s\n' % url for url in targets)

                    raise ScanMustStopException(msg % target_list)
                else:
                    sent_requests += 1

    def alert_if_target_is_301_all(self):
        """
        Alert the user when the configured target is set to a site which will
        301 redirect all requests to https://

        :see: https://github.com/andresriancho/w3af/issues/14976
        :return: True if the site returns 301 for all resources. Also an Info
                 instance is saved to the KB in order to alert the user.
        """
        site_does_redirect = False
        msg = ('The configured target domain redirects all HTTP requests to a'
               ' different location. The most common scenarios are:\n\n'
               ''
               '    * HTTP redirect to HTTPS\n'
               '    * domain.com redirect to www.domain.com\n\n'
               ''
               'While the scan engine can identify URLs and vulnerabilities'
               ' using the current configuration it might be wise to start'
               ' a new scan setting the target URL to the redirect target.')

        targets = cf.cf.get('targets')

        for url in targets:
            # We test if the target URLs are redirecting to a different protocol
            # or domain.
            try:
                http_response = self._w3af_core.uri_opener.GET(url, cache=False)
            except ScanMustStopByUserRequest:
                # Not a real error, the user stopped the scan
                raise
            except Exception, e:
                emsg = 'Exception found during alert_if_target_is_301_all(): "%s"'
                emsg %= e

                om.out.debug(emsg)
                raise ScanMustStopException(emsg)
            else:
                if 300 <= http_response.get_code() <= 399:

                    # Get the redirect target
                    lower_headers = http_response.get_lower_case_headers()
                    redirect_url = None

                    for header_name in ('location', 'uri'):
                        if header_name in lower_headers:
                            header_value = lower_headers[header_name]
                            header_value = header_value.strip()
                            try:
                                redirect_url = URL(header_value)
                            except ValueError:
                                # No special invalid URL handling required
                                continue

                    if not redirect_url:
                        continue

                    # Check if the protocol was changed:
                    target_proto = url.get_protocol()
                    redirect_proto = redirect_url.get_protocol()

                    if target_proto != redirect_proto:
                        site_does_redirect = True
                        break

                    # Check if the domain was changed:
                    target_domain = url.get_domain()
                    redirect_domain = redirect_url.get_domain()

                    if target_domain != redirect_domain:
                        site_does_redirect = True
                        break

        if site_does_redirect:
            name = 'Target redirect'
            info = Info(name, msg, http_response.id, name)
            info.set_url(url)
            info.add_to_highlight(http_response.get_redir_url().url_string)

            kb.kb.append_uniq('core', 'core', info)
            om.out.report_finding(info)

        return site_does_redirect

    def _setup_404_detection(self):
        #
        #    NOTE: I need to perform this test here in order to avoid some weird
        #    thread locking that happens when the webspider calls is_404, and
        #    because I want to initialize the is_404 database in a controlled
        #    try/except block.
        #
        from w3af.core.controllers.core_helpers.fingerprint_404 import is_404
        targets_with_404 = []

        for url in cf.cf.get('targets'):
            try:
                response = self._w3af_core.uri_opener.GET(url, cache=True)
            except ScanMustStopByUserRequest:
                raise
            except Exception, e:
                msg = ('Failed to send HTTP request to the configured target'
                       ' URL "%s", the original exception was: "%s" (%s).')
                args = (url, e, e.__class__.__name__)
                raise ScanMustStopException(msg % args)

            try:
                current_target_is_404 = is_404(response)
            except ScanMustStopByUserRequest:
                raise
            except Exception, e:
                msg = ('Failed to initialize the 404 detection using HTTP'
                       ' response from "%s", the original exception was: "%s"'
                       ' (%s).')
                args = (url, e, e.__class__.__name__)
                raise ScanMustStopException(msg % args)
            else:
                if current_target_is_404:
                    targets_with_404.append(url)

        if targets_with_404:
            urls = ' - %s\n'.join(u.url_string for u in targets_with_404)
            om.out.information('w3af identified the following user-configured'
                               ' targets as non-existing pages (404). This could'
                               ' result in a scan with low coverage: not all'
                               ' areas of the application are scanned. Please'
                               ' manually verify that these URLs exist and, if'
                               ' required, run the scan again.\n'
                               '\n'
                               '%s\n' % urls)

    def _setup_crawl_infrastructure(self):
        """
        Setup the crawl and infrastructure consumer:
            * Retrieve all plugins from the core,
            * Create the consumer instance and more,
        """
        crawl_plugins = self._w3af_core.plugins.plugins['crawl']
        infrastructure_plugins = self._w3af_core.plugins.plugins['infrastructure']

        if crawl_plugins or infrastructure_plugins:
            discovery_plugins = infrastructure_plugins
            discovery_plugins.extend(crawl_plugins)

            self._discovery_consumer = CrawlInfrastructure(discovery_plugins,
                                                           self._w3af_core,
                                                           cf.cf.get('max_discovery_time'))
            self._discovery_consumer.start()

    def _setup_grep(self):
        """
        Setup the grep consumer:
            * Create a Queue,
            * Set the Queue in xurllib
            * Start the consumer
        """
        grep_plugins = self._w3af_core.plugins.plugins['grep']

        if grep_plugins:
            self._grep_consumer = grep(grep_plugins, self._w3af_core)
            self._w3af_core.uri_opener.set_grep_queue_put(self._grep_consumer.grep)
            self._grep_consumer.start()

    def _teardown_grep(self):
        if self._grep_consumer is not None:
            self._grep_consumer.join()
            self._grep_consumer = None

    def _teardown_audit(self):
        if self._audit_consumer is not None:
            # Wait for all the in_queue items to get() from the queue
            self._audit_consumer.join()
            self._audit_consumer = None

    def _teardown_auth(self):
        if self._auth_consumer is not None:
            self._auth_consumer.join()
            self._auth_consumer = None

    def _teardown_bruteforce(self):
        if self._bruteforce_consumer is not None:
            self._bruteforce_consumer.join()
            self._bruteforce_consumer = None

    def _teardown_crawl_infrastructure(self):
        if self._discovery_consumer is not None:
            self._discovery_consumer.join()
            self._discovery_consumer = None

    def _teardown_observers(self):
        for observer in self._observers:
            observer.end()

    def _seed_discovery(self):
        """
        Create the first fuzzable request objects based on the targets and put
        them in the CrawlInfrastructure consumer Queue.

        This will start the whole discovery process, since plugins are going
        to consume from that Queue and then put their results in it again in
        order to continue discovering.
        """
        #
        #    GET the initial target URLs in order to save them
        #    in a list and use them as our bootstrap URLs
        #
        self._seed_producer.seed_output_queue(cf.cf.get('targets'))

    def _setup_bruteforce(self):
        """
        Create a bruteforce consumer instance with the bruteforce plugins
        and initialize it in order to start taking work from the input Queue.

        The input queue for this consumer is populated by the fuzzable request
        router.
        """
        bruteforce_plugins = self._w3af_core.plugins.plugins['bruteforce']

        if bruteforce_plugins:
            self._bruteforce_consumer = bruteforce(bruteforce_plugins,
                                                   self._w3af_core)
            self._bruteforce_consumer.start()

    def force_auth_login(self):
        """Force a login in a sync way
        :return: None.
        """
        if self._auth_consumer is not None:
            self._auth_consumer.force_login()

    def _setup_auth(self, timeout=5):
        """
        Start the thread that will make sure the xurllib always has a "fresh"
        session. The thread will call is_logged() and login() for each enabled
        auth plugin every "timeout" seconds.

        If there is a specific need to make sure that the session is fresh before
        performing any step, the developer needs to run the force_auth_login()
        method.
        """
        auth_plugins = self._w3af_core.plugins.plugins['auth']

        if auth_plugins:
            self._auth_consumer = auth(auth_plugins, self._w3af_core, timeout)
            self._auth_consumer.start()
            self._auth_consumer.force_login()

    def _setup_audit(self):
        """
        Starts the audit plugin consumer
        """
        om.out.debug('Called _setup_audit()')

        audit_plugins = self._w3af_core.plugins.plugins['audit']

        if audit_plugins:
            self._audit_consumer = audit(audit_plugins, self._w3af_core)
            self._audit_consumer.start()
