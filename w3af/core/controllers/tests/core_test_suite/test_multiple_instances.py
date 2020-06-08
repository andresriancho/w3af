"""
test_multiple_instances.py

Copyright 2011 Andres Riancho

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
import unittest
import threading

from multiprocessing.dummy import DummyProcess
from nose.plugins.attrib import attr

from w3af.core.controllers.w3afCore import w3afCore


def start_w3af_core(exception_handler):
    try:
        w3afCore()
    except Exception, e:
        if exception_handler:
            exception_handler(e)


@attr('smoke')
class TestW3afCore(unittest.TestCase):

    def setUp(self):
        self._exceptions = []

    def _exception_handler(self, exp):
        self._exceptions.append(exp)

    def test_multiple_instances(self):
        """
        Just making sure nothing crashes if I have more than 1 instance of
        w3afCore
        """
        instances = []
        for _ in xrange(5):
            instances.append(w3afCore())

    def test_multiple_instances_in_different_dummy_processes(self):
        """
        Create different w3afCore instances, in different threads.

        https://github.com/andresriancho/w3af-module/issues/5
        """
        t = DummyProcess(target=start_w3af_core,
                         args=(self._exception_handler,))
        t.start()
        t.join()

        self.assertEqual(self._exceptions, [])

    def test_dummy_in_dummy(self):
        """
        Create different w3afCore instances, in different threads.

        https://github.com/andresriancho/w3af-module/issues/5
        """
        def outer():
            t = DummyProcess(target=start_w3af_core,
                             args=(self._exception_handler,))
            t.start()
            t.join()

        t = DummyProcess(target=outer)
        t.start()
        t.join()

        self.assertEqual(self._exceptions, [])

    def test_dummy_in_thread(self):
        """
        Remember me?
        AttributeError: 'Worker' object has no attribute '_children'

        http://bugs.python.org/issue14881
        """
        def outer():
            try:
                t = DummyProcess(target=start_w3af_core,
                                 args=(self._exception_handler,))
                t.start()
            except AttributeError:
                pass

        t = threading.Thread(target=outer)
        t.start()
        t.join()

        self.assertEqual(self._exceptions, [])
