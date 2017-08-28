"""
status.py

Copyright 2012 Andres Riancho

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
import time

import w3af.core.controllers.output_manager as om

from w3af.core.controllers.misc.epoch_to_string import epoch_to_string
from w3af.core.controllers.misc.number_generator import consecutive_number_generator

PAUSED = 'Paused'
STOPPED = 'Stopped'
RUNNING = 'Running'


class w3af_core_status(object):
    """
    This class maintains the status of the w3afCore. During scan the different
    phases of the process will change the status (set) and the UI will be
    calling the different methods to (get) the information required.
    """
    def __init__(self, w3af_core, scans_completed=0):
        # Store the core to be able to access the queues to get status
        self._w3af_core = w3af_core
        
        # Init some internal values
        self._is_running = False
        self._paused = False
        self._start_time_epoch = None
        self.scans_completed = scans_completed
        
        # This indicates the plugin that is running right now for each
        # plugin_type
        self._running_plugin = {}
        self._latest_ptype, self._latest_pname = None, None
        
        # The current fuzzable request that the core is analyzing at each phase
        # where a phase means crawl/audit
        self._current_fuzzable_request = {}

    def pause(self, pause_yes_no):
        self._paused = pause_yes_no
        self._is_running = not pause_yes_no
        om.out.debug('The user paused/unpaused the scan.')

    def start(self):
        self._is_running = True
        self._start_time_epoch = time.time()

    def stop(self):
        # Now I'm definitely not running:
        self._is_running = False

    def get_status(self):
        """
        :return: A string representing the current w3af core status.
        """
        if self._paused:
            return PAUSED
        
        elif not self.is_running():
            return STOPPED
        
        else:
            crawl_plugin = self.get_running_plugin('crawl')
            audit_plugin = self.get_running_plugin('audit')
            
            crawl_fr = self.get_current_fuzzable_request('crawl')
            audit_fr = self.get_current_fuzzable_request('audit')
            
            if crawl_plugin == audit_plugin == crawl_fr == audit_fr == None:
                return 'Starting scan.'

            status_str = ''
            if crawl_plugin is not None and crawl_fr is not None:
                status_str += 'Crawling %s using %s.%s'
                status_str = status_str % (crawl_fr, 'crawl', crawl_plugin)

            if audit_plugin is not None and audit_fr is not None:
                if status_str:
                    status_str += '\n'
                
                status_str += 'Auditing %s using %s.%s' % (audit_fr, 'audit',
                                                           audit_plugin)
                
            status_str = status_str.replace('\x00', '')
            return status_str

    def set_running_plugin(self, plugin_type, plugin_name, log=True):
        """
        This method saves the phase and plugin name in order to be shown
        to the user.

        :param plugin_name: The plugin_type which the w3afCore is running
        :param plugin_name: The plugin_name which the w3afCore is running
        """
        self._running_plugin[plugin_type] = plugin_name
        self._latest_ptype, self._latest_pname = plugin_type, plugin_name

    def get_running_plugin(self, plugin_type):
        """
        :return: The plugin that the core is running when the method is called.
        """
        return self._running_plugin.get(plugin_type, None)

    def latest_running_plugin(self):
        """
        :return: Tuple with plugin_type and plugin_name for the latest running
                 plugin reported using set_running_plugin.
        """
        return self._latest_ptype, self._latest_pname

    def is_running(self):
        """
        :return: If the user has called start, and then wants to know if the
        core is still working, it should call is_running() to know that.
        """
        return self._is_running
    
    def is_paused(self):
        return self._paused
    
    def get_run_time(self):
        """
        :return: The time (in minutes) between now and the call to start().
        """
        if self._start_time_epoch is None:
            raise RuntimeError('Can NOT call get_run_time before start().')
        
        now = time.time()
        diff = now - self._start_time_epoch
        run_time = diff / 60
        return run_time

    def get_scan_time(self):
        """
        :return: The scan time in a format similar to:
                        3h 25m 32s
        """
        return epoch_to_string(self._start_time_epoch)

    def get_rpm(self):
        """
        :return: The number of HTTP requests per minute performed since the
                 start of the scan.
        """
        if self._start_time_epoch is None:
            raise RuntimeError('Can NOT call get_run_time before start().')
        
        now = time.time()
        diff = now - self._start_time_epoch
        run_time = diff / 60.0
        return int(consecutive_number_generator.get() / run_time)
    
    def scan_finished(self):
        self._is_running = False
        self._running_plugin = {}
        self._current_fuzzable_request = {}
        self.scans_completed += 1

    def get_current_fuzzable_request(self, plugin_type):
        """
        :return: The current fuzzable request that the w3afCore is working on.
        """
        return self._current_fuzzable_request.get(plugin_type, None)

    # pylint: disable=E0202
    def set_current_fuzzable_request(self, plugin_type, fuzzable_request):
        """
        :param fuzzable_request: The FuzzableRequest that the w3afCore is
        working on right now.
        """
        self._current_fuzzable_request[plugin_type] = fuzzable_request

    def get_crawl_input_speed(self):
        dc = self._w3af_core.strategy._discovery_consumer
        return None if dc is None else round_or_None(dc.in_queue.get_input_rpm())
    
    def get_crawl_output_speed(self):
        dc = self._w3af_core.strategy._discovery_consumer
        return None if dc is None else round_or_None(dc.in_queue.get_output_rpm())

    def get_crawl_qsize(self):
        dc = self._w3af_core.strategy._discovery_consumer
        return None if dc is None else dc.in_queue.qsize()

    def get_crawl_output_qsize(self):
        dc = self._w3af_core.strategy._discovery_consumer
        return None if dc is None else dc._out_queue.qsize()

    def get_crawl_worker_pool_queue_size(self):
        dc = self._w3af_core.strategy._discovery_consumer
        return None if dc is None else dc._threadpool._inqueue.qsize()

    def get_grep_qsize(self):
        dc = self._w3af_core.strategy._grep_consumer
        return None if dc is None else dc.in_queue.qsize()

    def get_crawl_current_fr(self):
        return self.get_current_fuzzable_request('crawl')

    def get_crawl_eta(self):
        input_speed = self.get_crawl_input_speed()
        output_speed = self.get_crawl_output_speed()
        current_size = self.get_crawl_qsize()

        if input_speed is None or output_speed is None:
            return None
            
        if input_speed >= output_speed:
            return None

        if current_size is None:
            return None

        # The speed is in URLs per minute that are processed by the framework
        speed = output_speed - input_speed
        eta_minutes = current_size / speed

        # TODO: Show this in h/m/s
        return '%s minutes' % eta_minutes

    def get_audit_input_speed(self):
        ac = self._w3af_core.strategy._audit_consumer
        return None if ac is None else round_or_None(ac.in_queue.get_input_rpm())
    
    def get_audit_output_speed(self):
        ac = self._w3af_core.strategy._audit_consumer
        return None if ac is None else round_or_None(ac.in_queue.get_output_rpm())

    def get_audit_qsize(self):
        ac = self._w3af_core.strategy._audit_consumer
        return None if ac is None else ac.in_queue.qsize()

    def get_audit_worker_pool_queue_size(self):
        ac = self._w3af_core.strategy._audit_consumer
        return None if ac is None else ac._threadpool._inqueue.qsize()

    def get_core_worker_pool_queue_size(self):
        return self._w3af_core.worker_pool._inqueue.qsize()

    def get_audit_current_fr(self):
        return self.get_current_fuzzable_request('audit')

    def get_audit_eta(self):
        input_speed = self.get_audit_input_speed()
        output_speed = self.get_audit_output_speed()

        if input_speed is None or output_speed is None:
            return None
        
        if input_speed >= output_speed:
            return None
        
        # The speed is in URLs per minute that are processed by the framework
        speed = output_speed - input_speed
        current_size = self.get_audit_qsize()
        
        eta_minutes = current_size / speed
        # TODO: Show this in h/m/s
        return '%s minutes' % eta_minutes

    def get_simplified_status(self):
        """
        :return: The status as a very simple string
        """
        if self.is_paused():
            return PAUSED

        elif not self.is_running():
            return STOPPED

        return RUNNING

    def get_status_as_dict(self):
        """
        :return: The status as a dict which I can use in JSON responses
        """
        def serialize_fuzzable_request(fuzzable_request):
            if fuzzable_request is None:
                return fuzzable_request

            return '%s %s' % (fuzzable_request.get_method(),
                              fuzzable_request.get_uri())

        crawl_fuzzable_request = self.get_current_fuzzable_request('crawl')
        crawl_fuzzable_request = serialize_fuzzable_request(crawl_fuzzable_request)

        audit_fuzzable_request = self.get_current_fuzzable_request('audit')
        audit_fuzzable_request = serialize_fuzzable_request(audit_fuzzable_request)

        data = {
                'status': self.get_simplified_status(),
                'is_paused': self.is_paused(),
                'is_running': self.is_running(),

                'active_plugin':
                    {'crawl': self.get_running_plugin('crawl'),
                     'audit': self.get_running_plugin('audit')}
                ,

                'current_request':
                    {'crawl': crawl_fuzzable_request,
                     'audit': audit_fuzzable_request},

                'queues':
                    {'crawl':
                        {'input_speed': self.get_crawl_input_speed(),
                         'output_speed': self.get_crawl_output_speed(),
                         'length': self.get_crawl_qsize()},
                     'audit':
                        {'input_speed': self.get_audit_input_speed(),
                         'output_speed': self.get_audit_output_speed(),
                         'length': self.get_audit_qsize()}
                    },

                'eta':
                    {'crawl': self.get_crawl_eta(),
                     'audit': self.get_audit_eta()},

                'rpm': self.get_rpm(),
                }
        return data

    def get_long_status(self):
        if not self.is_running():
            return self.get_status()
        
        data = {
                'status': self.get_status(),
                
                'cin': self.get_crawl_input_speed(),
                'cout': self.get_crawl_output_speed(),
                'clen': self.get_crawl_qsize(),
                'ceta': self.get_crawl_eta(),
                
                'ain': self.get_audit_input_speed(),
                'aout': self.get_audit_output_speed(),
                'alen': self.get_audit_qsize(),
                'aeta': self.get_audit_eta(),
                
                'rpm': self.get_rpm()
                }
        
        status_str = '%(status)s\n'
        
        status_str += 'Crawl phase: In (%(cin)s URLs/min)'\
                      ' Out (%(cout)s URLs/min) Pending (%(clen)s URLs)'\
                      ' ETA (%(ceta)s)\n'
                      
        status_str += 'Audit phase: In (%(ain)s URLs/min)'\
                      ' Out (%(aout)s URLs/min) Pending (%(alen)s URLs)'\
                      ' ETA (%(aeta)s)\n'
                      
        status_str += 'Requests per minute: %(rpm)s'
        
        return status_str % data


def round_or_None(float_or_none):
    if float_or_none is None:
        return None
    else:
        return round(float_or_none, 2)