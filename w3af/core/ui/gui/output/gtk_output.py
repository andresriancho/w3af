"""
gtk_output.py

Copyright 2008 Andres Riancho

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
import weakref

import w3af.core.data.constants.severity as severity
import w3af.core.controllers.output_manager as om

from w3af.core.controllers.plugins.output_plugin import OutputPlugin

DEBUG = 'debug'
INFORMATION = 'information'
ERROR = 'error'
VULNERABILITY = 'vulnerability'
CONSOLE = 'console'
LOG_HTTP = 'log_http'


observers = set()


class GtkOutput(OutputPlugin):
    """
    This is an observer which exposes an OutputPlugin API in order to be added
    to the output manager as one more plugin.
    
    Please note that this is NOT a real plugin, as it can't be enabled/disabled
    by a user.
    
    Any part of the GTK ui can subscribe to the messages that this object
    receives, and will get all data that is sent to the output manager. 

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self):
        pass

    def debug(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for debug messages.
        """
        #
        #   I don't really want to add debug messages to the queue, as they are
        #   only used in the time graph that's displayed under the log. In order
        #   to save some memory. I'm only creating the object, but without any
        #   msg.
        #
        m = Message(DEBUG, '', new_line)
        self._send_to_observers(m)

    def information(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for informational messages.
        """
        m = Message(INFORMATION, self._clean_string(msg_string), new_line)
        self._send_to_observers(m)

    def error(self, msg_string, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action for error messages.
        """
        m = Message(ERROR, self._clean_string(msg_string), new_line)
        self._send_to_observers(m)

    def vulnerability(self, msg_string, new_line=True, severity=severity.MEDIUM):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take an
        action when a vulnerability is found.
        """
        m = Message(VULNERABILITY, self._clean_string(msg_string), new_line)
        m.set_severity(severity)
        self._send_to_observers(m)

    def console(self, msg_string, new_line=True):
        """
        This method is used by the w3af console to print messages to the outside
        """
        m = Message(CONSOLE, self._clean_string(msg_string), new_line)
        self._send_to_observers(m)

    def _send_to_observers(self, m):
        """
        Adds a message object to the queue.
        """
        to_remove = set()
        
        for observer in observers.copy():
            try:
                observer(m)
            except Exception, e:
                msg = 'Observer function at "%s" failed with exception "%s".'\
                      ' Removing observer from list.'
                om.out.error(msg % (observer, e))
                to_remove.add(observer)
        
        for broken_obs in to_remove:
            observers.remove(broken_obs)
    
    def subscribe(self, observer):
        observers.add(observer)

    def unsubscribe(self, observer):
        if observer in observers:
            observers.remove(observer)

    def end(self):
        global observers
        observers = set()


#pylint: disable=E1103
def subscribe_to_messages(observer_function):
    """
    Subscribe observer_function to the GtkOutput messages
    """
    all_output_plugins = om.manager.get_output_plugin_inst()
    for plugin_inst in all_output_plugins:
        if isinstance(plugin_inst, GtkOutput):
            plugin_inst.subscribe(observer_function)
            break
    else:
        gtk_output = GtkOutput()
        om.manager.set_output_plugin_inst(gtk_output)
        gtk_output.subscribe(observer_function)


def unsubscribe_to_messages(observer_function):
    """
    Unsubscribe observer_function to the GtkOutput messages
    """
    all_output_plugins = om.manager.get_output_plugin_inst()
    for plugin_inst in all_output_plugins:
        if isinstance(plugin_inst, GtkOutput):
            plugin_inst.unsubscribe(observer_function)
            break
#pylint: enable=E1103


class Message(object):
    def __init__(self, msg_type, msg, new_line=True):
        """
        :param msg_type: console, information, vulnerability, etc
        :param msg: The message itself
        :param new_line: Should I print a newline ? True/False
        """
        self._type = msg_type
        self._msg = msg
        self._new_line = new_line
        self._time = time.time()
        self._severity = None

    def get_severity(self):
        return self._severity

    def set_severity(self, the_severity):
        self._severity = the_severity

    def get_msg(self):
        return self._msg

    def get_type(self):
        return self._type

    def get_new_line(self):
        return self._new_line

    def get_real_time(self):
        return self._time

    def get_time(self):
        return time.strftime("%c", time.localtime(self._time))
