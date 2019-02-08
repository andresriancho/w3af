"""
exception_handler.py

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
import os
import random
import hashlib
import tempfile
import threading
import traceback

import w3af.core.data.kb.config as cf
import w3af.core.controllers.output_manager as om

from w3af.core.data.fuzzer.utils import rand_alnum
from w3af.core.controllers.misc.traceback_utils import get_exception_location
from w3af.core.controllers.core_helpers.status import CoreStatus
from w3af.core.controllers.exception_handling.cleanup_bug_report import cleanup_bug_report
from w3af.core.controllers.exceptions import (ScanMustStopException,
                                              ScanMustStopByUserRequest,
                                              HTTPRequestException,
                                              ScanMustStopByUnknownReasonExc)

DEBUG = os.environ.get('DEBUG', '0') == '1'


class ExceptionHandler(object):
    """
    This class handles exceptions generated while running plugins, usually
    the handling is just to store the traceback for later processing.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """

    MAX_EXCEPTIONS_PER_PLUGIN = 3
    NO_HANDLING = (MemoryError,
                   OSError,
                   IOError,
                   ScanMustStopByUnknownReasonExc,
                   ScanMustStopException,
                   ScanMustStopByUserRequest,
                   HTTPRequestException)

    if DEBUG:
        NO_HANDLING = list(NO_HANDLING)
        NO_HANDLING.append(Exception)
        NO_HANDLING = tuple(NO_HANDLING)

    def __init__(self):
        self._exception_data = []
        self._lock = threading.RLock()

        self._scan_id = None

    def handle_exception_data(self, exception_data):
        self.handle(exception_data.status,
                    exception_data.exception,
                    (_, _, exception_data.traceback),
                    exception_data.enabled_plugins)

    def handle(self, current_status, exception, exec_info, enabled_plugins):
        """
        This method stores the current status and the exception for later
        processing. If there are already too many stored exceptions for this
        plugin then no action is taken.

        :param current_status: Pointer to the core_helpers.status module
        :param exception: The exception that was raised
        :param exec_info: The exec info as returned by sys module. In some
                          scenarios the data can be (partially) incomplete.
                          except_type and except_class might be None; or all the
                          three fields might be None.
        :param enabled_plugins: A string as returned by helpers.pprint_plugins.
                                First I thought about getting the enabled_plugins
                                after the scan finished, but that proved to be
                                an incorrect approach since the UI and/or
                                strategy could simply remove that information as
                                soon as the scan finished.

        :return: None
        """
        except_type, except_class, tb = exec_info

        #
        # There are some exceptions, that because of their nature, can't be
        # handled here. Raise them so that w3afCore.py, most likely to the
        # except lines around self.strategy.start(), can decide what to do
        #
        if isinstance(exception, self.NO_HANDLING):
            raise exception, None, tb

        stop_on_first_exception = cf.cf.get('stop_on_first_exception')
        if stop_on_first_exception:
            raise exception, None, tb

        #
        # Now we really handle the exception that was produced by the plugin in
        # the way we want to.
        #
        with self._lock:
            edata = ExceptionData(current_status, exception, tb, enabled_plugins)

            count = 0
            for stored_edata in self._exception_data:
                if edata.plugin == stored_edata.plugin and \
                   edata.phase == stored_edata.phase:
                    count += 1

            if count < self.MAX_EXCEPTIONS_PER_PLUGIN:
                self._exception_data.append(edata)
                msg = edata.get_summary()
                msg += (' The scan will continue but some vulnerabilities might'
                        ' not be identified.')
                om.out.error(msg)

        filename = self.write_crash_file(edata)

        args = (edata.get_exception_class(), filename)
        om.out.debug('Logged "%s" to "%s"' % args)

        # Also send to the output plugins so they can store it the right way
        om.out.log_crash(edata.get_details())

    def write_crash_file(self, edata):
        """
        Writes the exception data to a random file in /tmp/ right after the
        exception is found.

        Very similar to the create_crash_file but for internal/debugging usage

        :return: None
        """
        filename = 'w3af-crash-%s.txt' % rand_alnum(5)
        filename = os.path.join(tempfile.gettempdir(), filename)
        crash_dump = file(filename, "w")
        crash_dump.write(edata.get_details())
        crash_dump.close()
        return filename

    def clear(self):
        self._exception_data = []

    def get_all_exceptions(self):
        return self._exception_data

    def get_unique_exceptions(self):
        """
        Filters the found exceptions to only show unique "bugs". We filter based
        on the lineno and filename of each ExceptionData stored in
        self._exception_data

        :return: A filtered exception list
        """
        filtered_exceptions = []

        for edata in self.get_all_exceptions():
            for unique in filtered_exceptions:
                if edata.lineno == unique.lineno and edata.filename == edata.filename:
                    break
            else:
                filtered_exceptions.append(edata)

        return filtered_exceptions

    def generate_summary_str(self):
        """
        :return: A string with a summary of the exceptions found during the
                 current scan. This is mostly used for printing in the console
                 but can be used anywhere.

        @see: generate_summary method for a way of getting a summary in a
              different format.
        """
        summary = self.generate_summary()

        if not summary['total_exceptions']:
            fmt_without_exceptions = 'No exceptions were raised during scan with id: %s.'
            without_exceptions = fmt_without_exceptions % self.get_scan_id()
            return without_exceptions

        fmt_with_exceptions = ('During the current scan (with id: %s) w3af'
                               ' caught %s exceptions in it\'s plugins. The'
                               ' scan was able to continue by ignoring those'
                               ' failures but the result is most likely'
                               ' incomplete.\n'
                               '\n'
                               'These are the phases and plugins that raised'
                               ' exceptions:\n'
                               '%s\n'
                               'We recommend you report these vulnerabilities'
                               ' to the developers in order to help increase'
                               ' the project\'s stability.\n'
                               '\n'
                               'To report these bugs just run the "report"'
                               ' command.')

        phase_plugin_str = ''

        for phase in summary['exceptions']:
            for plugin, fr, exception, _ in summary['exceptions'][phase]:
                phase_plugin_str += '- %s.%s\n' % (phase, plugin)

        with_exceptions = fmt_with_exceptions % (self.get_scan_id(),
                                                 summary['total_exceptions'],
                                                 phase_plugin_str)
        return with_exceptions

    def generate_summary(self):
        """
        :return: A dict with information about exceptions.
        """
        res = {'total_exceptions': len(self._exception_data), 'exceptions': {}}
        exception_dict = res['exceptions']

        for exception in self._exception_data:
            phase = exception.phase

            data = (exception.plugin,
                    exception.fuzzable_request,
                    exception.exception,
                    exception.traceback_str)

            if phase not in exception_dict:
                exception_dict[phase] = [data]
            else:
                exception_dict[phase].append(data)

        return res

    def get_scan_id(self):
        """
        :return: A scan identifier to bind all bug reports together so that we
                 can understand them much better when looking at the individual
                 Github bug reports.

                 Note that this will NOT leak any personal information to our
                 systems.
        """
        if not self._scan_id:
            hash_data = str(random.randint(1, 50000000) * random.randint(1, 50000000))

            m = hashlib.md5(hash_data)
            self._scan_id = m.hexdigest()[:10]

        return self._scan_id


class ExceptionData(object):
    def __init__(self, current_status, e, tb, enabled_plugins, store_tb=True):
        """
        :param current_status: The CoreStatus instance
        :param e: Exception instance
        :param tb: Traceback or None
        :param enabled_plugins: w3af enabled plugins
        :param store_tb: When the exception is raised in a consumer and needs to
                         be serialized to be sent to the main thread, it is
                         impossible to keep the traceback
        """
        assert isinstance(e, Exception)
        assert isinstance(current_status, CoreStatus)

        self.traceback = None
        self.traceback_str = None
        self.function_name = None
        self.lineno = None
        self.filename = None
        self.exception = None
        self.exception_msg = None
        self.exception_class = None
        self.phase = None
        self.plugin = None
        self.status = None
        self.fuzzable_request = None

        self._initialize(current_status, e, tb, enabled_plugins, store_tb)

    def _initialize(self, current_status, e, tb, enabled_plugins, store_tb):
        self._initialize_from_exception(e)
        self._initialize_from_traceback(tb, store_tb)
        self._initialize_from_status(current_status)
        self._initialize_from_plugins(enabled_plugins)

    def _initialize_from_exception(self, e):
        self.exception = e
        self.exception_msg = str(e)
        self.exception_class = e.__class__.__name__

    def _initialize_from_status(self, current_status):
        self.phase, self.plugin = current_status.latest_running_plugin()

        #
        # Do not save the CoreStatus instance here without cleaning it first,
        # it will break serialization since the CoreStatus instances have
        # references to a w3afCore instance, which points to a Pool instance
        # that is NOT serializable.
        #
        self.status = current_status
        self.status.set_w3af_core(None)

        self.fuzzable_request = current_status.get_current_fuzzable_request(self.phase)
        self.fuzzable_request = cleanup_bug_report(str(self.fuzzable_request))

    def _initialize_from_plugins(self, enabled_plugins):
        self.enabled_plugins = enabled_plugins

    def _initialize_from_traceback(self, tb, store_tb):
        if store_tb:
            #
            # According to [0] it is not a good idea to keep references to tracebacks:
            #
            #   > traceback refers to a linked list of frames, and each frame has references
            #   > to lots of other stuff like the code object, the global dict, local dict,
            #   > builtin dict, ...
            #
            # [0] https://bugs.python.org/issue13831
            #
            # TODO: Remove the next line:
            self.traceback = tb

        # Extract the filename and line number where the exception was raised
        path, filename, self.function_name, self.lineno = get_exception_location(tb)
        if path is not None:
            self.filename = os.path.join(path, filename)

        # See add_traceback_string()
        if hasattr(self.exception, 'original_traceback_string'):
            traceback_string = self.exception.original_traceback_string
        else:
            traceback_string = ''.join(traceback.format_tb(tb))
            self.exception.original_traceback_string = traceback_string

        self.traceback_str = cleanup_bug_report(traceback_string)

    def get_traceback_str(self):
        return self.traceback_str

    def get_summary(self):
        res = ('A "%s" exception was found while running %s.%s on "%s".'
               ' The exception was: "%s" at %s:%s():%s.')
        res = res % (self.get_exception_class(),
                     self.phase,
                     self.plugin,
                     self.fuzzable_request,
                     self.exception_msg,
                     self.filename,
                     self.function_name,
                     self.lineno)
        return res

    def get_exception_class(self):
        return self.exception_class

    def get_details(self):
        res = self.get_summary()
        res += ' The full traceback is:\n\n%s' % self.traceback_str
        return res

    def get_where(self):
        return '%s.%s:%s' % (self.phase, self.plugin, self.lineno)

    def to_json(self):
        return {'function_name': self.function_name,
                'lineno': self.lineno,
                'exception': self.exception_msg,
                'traceback': self.traceback_str,
                'plugin': str(self.plugin),
                'phase': str(self.phase)}

    def __str__(self):
        return self.get_details()

    def __repr__(self):
        return '<ExceptionData - %s:%s - "%s">' % (self.filename,
                                                   self.lineno,
                                                   self.exception_msg)
