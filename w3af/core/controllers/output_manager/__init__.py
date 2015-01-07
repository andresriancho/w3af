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
    return manager


def log_sink_factory(om_queue):
    """
    Creates a new "out" instance at the module level.

    :return: A reference to the newly created instance
    """
    global out
    out = LogSink(om_queue)
    return out


# Create the default manager and out instances, we'll be creating others later
# most likely for the log sink, which will be replaced in each sub-process
manager = OutputManager()
out = log_sink_factory(manager.get_in_queue())
