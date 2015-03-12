"""
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
import logging

from .manager import OutputManager
from .log_sink import LogSink

from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL

# https://pypi.python.org/pypi/stopit#logging
# The stopit named logger emits a warning each time a block of code execution
# exceeds the associated timeout. To turn logging off, just:
stopit_logger = logging.getLogger('stopit')
stopit_logger.setLevel(logging.ERROR)


def fresh_output_manager_inst():
    """
    Creates a new "manager" instance at the module level.

    :return: A reference to the newly created instance
    """
    global manager

    #
    #   Stop the old instance thread
    #
    if manager.is_alive():
        manager.in_queue.put(POISON_PILL)
        manager.join()

    #
    #   Create the new instance
    #
    manager = OutputManager()
    manager.start()
    return manager


def log_sink_factory(om_queue):
    """
    Creates a new "out" instance at the module level.

    :return: A reference to the newly created instance
    """
    global out
    out = LogSink(om_queue)
    return out


# Create the default manager and out instances, we'll be creating others later:
# most likely for the log sink, which will be replaced in each sub-process
manager = OutputManager()

# Logs to into the logging process through out.debug() , out.error() , etc.
out = log_sink_factory(manager.get_in_queue())
