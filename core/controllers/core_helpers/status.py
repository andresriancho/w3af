'''
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

'''
import core.controllers.output_manager as om


class w3af_core_status(object):
    '''
    This class maintains the status of the w3afCore. During scan the different
    phases of the process will change the status (set) and the UI will be calling
    the different methods to (get) the information required.
    '''
    def __init__(self):
        # Init some internal values
        self._is_running = False
        self._paused = False
        
        # This indicates if we are doing discovery/audit/exploit/etc...
        self._current_phase = ''
        # This indicates the plugin that is running right now
        self._running_plugin = ''
        # The current fuzzable request that the core is analyzing
        self._current_fuzzable_request = ''

    def pause(self, pause_yes_no):
        self._paused = pause_yes_no
        self._is_running = not pause_yes_no
        om.out.debug('The user paused/unpaused the scan.')

    def start(self):
        self._is_running = True

    def stop(self):
        # Now I'm definitely not running:
        self._is_running = False

    def get_status(self):
        '''
        @return: A string representing the current w3af core status.

        >>> s = w3af_core_status()

        >>> s.get_status()
        'Stopped.'
        >>> s.start()
        >>> s.get_status()
        'Starting scan.'
        >>> s.set_phase('crawl')
        >>> s.set_running_plugin('doctest_plugin')
        >>> s.set_current_fuzzable_request('doctest_request')
        >>> s.get_status()
        'Running crawl.doctest_plugin on doctest_request.'

        '''
        if self._paused:
            return 'Paused.'
        elif not self.is_running():
            return 'Stopped.'
        else:
            if self.get_phase() != '' and self.get_running_plugin() != '':
                running = 'Running %s.%s on %s.'
                fr_str = str(
                    self.get_current_fuzzable_request()).replace('\x00', '')
                return running % (self.get_phase(), self.get_running_plugin(), fr_str)
            else:
                return 'Starting scan.'

    def get_phase(self):
        '''
        @return: The phase which the core is running.
        '''
        return self._current_phase

    def set_phase(self, phase):
        '''
        This method saves the phase (discovery/audit/exploit), so in the future
        the UI can use the getPhase() method to show it.

        @param phase: The phase which the w3afCore is running in a given moment
        '''
        self._current_phase = phase

    def set_running_plugin(self, plugin_name, log=True):
        '''
        This method saves the phase, so in the future the UI can use the
        getPhase() method to show it.

        @param plugin_name: The plugin_name which the w3afCore is running in
        a given moment
        '''
        if log:
            om.out.debug('Starting plugin: ' + plugin_name)
        self._running_plugin = plugin_name

    def get_running_plugin(self):
        '''
        @return: The plugin that the core is running when the method is called.
        '''
        return self._running_plugin

    def is_running(self):
        '''
        @return: If the user has called start, and then wants to know if the
        core is still working, it should call is_running() to know that.
        '''
        return self._is_running
    
    def scan_finished(self):
        self._is_running = False

    def get_current_fuzzable_request(self):
        '''
        @return: The current fuzzable request that the w3afCore is working on.
        '''
        return self._current_fuzzable_request

    # pylint: disable=E0202
    def set_current_fuzzable_request(self, fuzzable_request):
        '''
        @param fuzzable_request: The FuzzableRequest that the w3afCore is
        working on right now.
        '''
        self._current_fuzzable_request = fuzzable_request
