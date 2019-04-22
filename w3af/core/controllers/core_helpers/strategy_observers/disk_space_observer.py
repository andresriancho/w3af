"""
disk_space_observer.py

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
import errno

from time import time
from psutil import disk_usage

from .strategy_observer import StrategyObserver
from w3af.core.controllers.misc.home_dir import get_home_dir


class DiskSpaceObserver(StrategyObserver):
    """
    Monitor free disk space and raise an exception if it's too low.

    The goal is to prevent issues such as "DBException: database or disk is
    full" and malformed sqlite databases which might be related to no free
    space left.

    The best way to do this was with fanotify (linux kernel FS monitor [0]) but
    it's linux-specific and with hard install dependencies such as the kernel
    headers.

    [0] http://man7.org/linux/man-pages/man7/fanotify.7.html
    :see: https://github.com/andresriancho/w3af/issues/5343
    """
    MIN_FREE_MB = 100
    MIN_FREE_BYTES = MIN_FREE_MB * 1024 * 1024
    ANALYZE_EVERY = 5
    LOW_DISK_SPACE_MESSAGE = ('Detected that "%s" has only %s MB of free disk'
                              ' space. The scan will stop.')

    def __init__(self):
        super(DiskSpaceObserver, self).__init__()
        self.last_call = 0

    def analyze_disk_space(self, *args):
        # Don't measure disk usage each time we get called, in some platforms
        # it's expensive to call disk_usage
        current_time = time()
        if current_time - self.last_call < self.ANALYZE_EVERY:
            return

        self.last_call = current_time

        # Get the disk usage, ignore any errors
        try:
            usage = disk_usage(get_home_dir())
        except:
            return

        # Raise an exception if there is no enough space
        if usage.free < self.MIN_FREE_BYTES:
            free_mb = usage.free / 1024 / 1024
            msg = self.LOW_DISK_SPACE_MESSAGE % (get_home_dir(), free_mb)
            raise IOError(errno.ENOSPC, msg)

    crawl = audit = bruteforce = grep = analyze_disk_space
