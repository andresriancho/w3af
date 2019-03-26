"""
log_sink.py

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
import functools


class LogSink(object):
    """
    The log sink receives log messages in different threads/processes and sends
    them over a multiprocessing queue to the main process where they are handled
    by the output manager => output plugins.
    """
    ALLOWED_METHODS = {
        'debug',
        'information',
        'error',
        'vulnerability',
        'console',
        'log_http',
        'log_crash',
    }

    METHODS = None

    def __init__(self, om_queue):
        super(LogSink, self).__init__()
        self.om_queue = om_queue
        self.METHODS = dict((method, functools.partial(self._add_to_queue, method)) for method in self.ALLOWED_METHODS)

    def report_finding(self, info_inst):
        """
        The plugins call this in order to report an info/vuln object to the
        user. This is an utility function that simply calls information() or
        vulnerability() with the correct parameters, depending on the info_inst
        type and severity.

        :param info_inst: An Info class or subclass.
        """
        self.vulnerability(info_inst.get_desc(),
                           severity=info_inst.get_severity())

    def _add_to_queue(self, *args, **kwargs):
        try:
            self.om_queue.put((args, kwargs))
        except IOError:
            print('LogSink queue communication lost.'
                  ' Some log messages will be lost.')

    def __getattr__(self, name):
        """
        This magic method replaces all the previous debug/information/error ones
        It will basically return a func pointer to:

            self.add_to_queue('debug',  ...)

        Where "..." is completed later by the caller.

        @see: http://docs.python.org/library/functools.html for help on partial.
        @see: METHODS defined at the top of this class
        """
        method = self.METHODS.get(name, None)

        if method is None:
            msg = "'LogSink' object has no attribute '%s'"
            raise AttributeError(msg % name)

        return method
