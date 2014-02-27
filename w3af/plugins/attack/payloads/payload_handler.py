"""
payload_handler.py

Copyright 2009 Andres Riancho

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
import sys

from w3af import ROOT_PATH

PAYLOAD_PATH = os.path.join(ROOT_PATH, 'plugins', 'attack', 'payloads',
                            'payloads')


def payload_to_file(payload_name):
    """
    :param payload_name: The name of the payload.
    :return: The filename related to the payload.
    """
    return os.path.join(PAYLOAD_PATH, payload_name + '.py')


def is_payload(function_name):
    """
    :return: True if the function_name is referencing a payload.

    >>> is_payload('udp')
    True
    """
    return function_name in get_payload_list()


def exec_payload(shell_obj, payload_name, args=(), use_api=False):
    """
    Now I execute the payload, by providing the shell_obj.

    :param shell_obj: The shell object instance where I get the syscalls from.
                      If this is set to None, the handler will choose a shell
                      from the KB that provide the necessary syscalls.
    :param payload_name: The name of the payload I want to run.
    :param args: A tuple with the args (strings) the user typed.
    @use_api: Indicates if I need to use the API or not in this run. This is
              True when exec_payload is called from Payload.exec_payload()

    :return: The payload result.
    """
    payload_inst = get_payload_instance(payload_name, shell_obj)
    if use_api:
        result = payload_inst.run_api(*args)
    else:
        result = payload_inst.run(*args)
    return result


def runnable_payloads(shell_obj):
    """
    The payloads that can be run using this shell object.

    :return: A list with all runnable payload names.
    """
    result = []

    for payload_name in get_payload_list():
        payload = get_payload_instance(payload_name, shell_obj)
        if payload.can_run():
            result.append(payload_name)

    return result


def get_payload_instance(payload_name, shell_obj):
    """
    :return: A payload instance.
    """
    name = '.'.join(['w3af', 'plugins', 'attack', 'payloads', 'payloads',
                     payload_name])
    __import__(name)
    module = sys.modules[name]
    klass = getattr(module, payload_name)
    return apply(klass, (shell_obj, ))


def get_payload_desc(payload_name):
    """
    >>> get_payload_desc('tcp')
    'This payload shows TCP socket information'
    """
    class FakePayload(object):
        def __init__(self):
            self.worker_pool = None
            
    payload = get_payload_instance(payload_name, FakePayload())
    return payload.get_desc()


def get_payload_list():
    """
    :return: A list of the payload names in the payloads directory.

    >>> 'tcp' in get_payload_list()
    True
    """
    result = []
    py_list = [x for x in os.listdir(PAYLOAD_PATH) if 
               x.endswith('.py') and x != '__init__.py']
    for p in py_list:
        p = p.replace('.py', '')
        result.append(p)

    return result
