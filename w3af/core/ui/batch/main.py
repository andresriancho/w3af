# encoding: utf-8
# vim: ft=python
"""
main.py

Copyright 2015 Andres Riancho

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
import logging
import argparse
import signal
import time
import threading as th
import multiprocessing as mp
import multiprocessing.dummy as mpd

from Queue import Empty as EmptyQueue
from w3af.core.controllers.dependency_check.dependency_check import dependency_check


DEFAULT_TIMEOUT = 300  # in seconds
WAIT_TIMEOUT = 30      # in seconds
STOPSCAN = mp.Event()


def _process_arguments():
    parser = argparse.ArgumentParser(description='Helper script to run w3af'\
                                                 ' with multiple target web'\
                                                 ' applications.')
    parser.add_argument('-l', default=None, dest='logconfig',
                        help='Config file for Python\'s logging module')
    parser.add_argument('-n', dest='workers', type=int,
                        default=mp.cpu_count(),
                        help='Number of worker processes '
                             '(default: number of CPUs)')
    parser.add_argument('-t', default=DEFAULT_TIMEOUT, dest='timeout', type=int,
                        help='Target scan timeout in seconds (default: 300)')
    parser.add_argument('-p', dest='profile', required=True,
                        help='Builtin profile name or path to pw3af file')
    parser.add_argument('targets', type=argparse.FileType(),
                        help='Path to file with list of targets')
    return parser.parse_args()


def _get_logger():
    return logging.getLogger(__name__)


def _configure_logging(logconfig):
    if logconfig is not None:
        from logging.config import fileConfig
        fileConfig(logconfig, disable_existing_loggers=False)


class Worker(object):
    """Container for Worker related functions."""

    @staticmethod
    def run(job, timeout=DEFAULT_TIMEOUT, report_queue=None, **kwargs):
        """Call start() for job object.

        After timeout seconds stop() method of job object is called.
        """
        worker_job = job(**kwargs)
        timer = th.Timer(timeout, Worker._stop_job, args=(worker_job,))
        timer.start()
        worker_job.start()
        timer.cancel()
        if report_queue is not None:
            report_queue.put(worker_job.result())

    @staticmethod
    def _stop_job(job):
        job.stop()


class Manager(object):
    """Container for Manager related functions."""

    @staticmethod
    def run(wait_timeout=WAIT_TIMEOUT, **kwargs):
        wait_timeout = kwargs.get('timeout', DEFAULT_TIMEOUT) + wait_timeout
        process = mp.Process(target=Worker.run, kwargs=kwargs)
        finished = th.Event()
        stopper = th.Thread(target=Manager._stopper, args=(process, finished))
        stopper.start()
        timer = th.Timer(wait_timeout, Manager._terminate_worker,
                         args=(process,))
        timer.start()
        process.start()
        process.join()
        finished.set()
        stopper.join()
        timer.cancel()

    @staticmethod
    def _terminate_worker(process):
        if process.is_alive():
            process.terminate()

    @staticmethod
    def _stopper(subject, finished):
        while True:
            if finished.wait(0.1):
                break
            if STOPSCAN.is_set():
                subject.terminate()


class Pool(object):
    """Container for Pool related functions."""

    @staticmethod
    def run(targets, report_queue=None, workers=mpd.cpu_count(), **kwargs):
        signal.signal(signal.SIGINT, Pool._signal_handler)
        pool = mpd.Pool(workers)
        finished = th.Event()
        stopper = th.Thread(target=Pool._stopper, args=(pool, finished))
        stopper.start()
        
        if report_queue is not None:
            kwargs['report_queue'] = report_queue
        
        for line in targets:
            target = line.rstrip()
            target_kwargs = kwargs.copy()
            target_kwargs['target'] = target
            pool.apply_async(Manager.run, kwds=target_kwargs)
        
        pool.close()
        pool.join()
        finished.set()
        stopper.join()

    @staticmethod
    def _stopper(pool, finished):
        while True:
            if finished.wait(0.1):
                break
            if STOPSCAN.is_set():
                pool.terminate()

    @staticmethod
    def _signal_handler(*args):
        STOPSCAN.set()


class W3afJob(object):
    """Create w3afCore object and start w3af scan."""

    def __init__(self, target, profile):
        """W3afJob constructor.

        :param target: target URI
        :param profile: internal w3af profile name or path to *.pw3af file
        """
        from w3af.core.controllers.w3afCore import w3afCore
        from w3af.core.controllers.exceptions import BaseFrameworkException

        self._target = target
        self._profile = profile
        scanner = w3afCore()
        scanner.profiles.use_profile(profile)
        option_list = scanner.target.get_options()
        option_list['target'].set_value(target)
        scanner.target.set_options(option_list)
        scanner.plugins.init_plugins()
        self.scanner = scanner

        _get_logger().debug('Init scan for %s', target)

    def start(self):
        self.scanner.start()
        _get_logger().debug('Start scan for %s', self._target)

    def stop(self):
        self.scanner.stop()

    def result(self):
        """Return result scan."""
        from w3af.core.data.kb.knowledge_base import kb
        return (self._target, kb.get_all_vulns())


def main():
    """
    Scan a of list of targets from file in parallel.  A pool of manager
    threads is created. Each thread receives a target to scan. Manager
    thread executes scan in a separate process. Scanner process will
    try to stop w3af after timeout seconds. In addition manager thread
    will terminate the child process after WAIT_TIMEOUT seconds.

    :author: https://github.com/skoval00
    """
    # Check if I have all needed dependencies
    dependency_check()

    args = _process_arguments()
    _configure_logging(args.logconfig)
    report_queue = mp.Queue()
    Pool.run(targets=args.targets, job=W3afJob, profile=args.profile,
             timeout=args.timeout, report_queue=report_queue)
    
    while True:
        try:
            target, result = report_queue.get_nowait()
        except EmptyQueue:
            return 1
        else:
            _get_logger().info('%s: %s', target, result)

    return 0