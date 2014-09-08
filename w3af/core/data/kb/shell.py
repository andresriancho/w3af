"""
shell.py

Copyright 2007 Andres Riancho

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
import w3af.plugins.attack.payloads.payload_handler as payload_handler
import w3af.core.controllers.output_manager as om

from w3af.core.data.kb.vuln import Vuln
from w3af.core.data.kb.exploit_result import ExploitResult


class Shell(ExploitResult):
    """
    This class represents the output of an attack plugin that gives a shell to
    the w3af user.

    :author: Andres Riancho (andres.riancho@gmail.com)
    """
    def __init__(self, vuln, uri_opener, worker_pool):
        ExploitResult.__init__(self)
        
        if not isinstance(vuln, Vuln):
            raise TypeError('Expected Vuln instance in Shell ctor.')
        
        self.set_url_opener(uri_opener)
        self.set_worker_pool(worker_pool)
        self._vuln = vuln
        
        self._rOS = None
        self._rSystem = None
        self._rUser = None
        self._rSystemName = None
        self.id = 0
    
    def get_remote_os(self):
        return self._rOS

    def get_remote_system(self):
        """
        :return: dz0@sock3t:~/w3af$ uname -o -r -n -m -s
        Linux sock3t 2.6.15-27-686 i686 GNU/Linux
        """
        return self._rSystem

    def get_remote_user(self):
        return self._rUser

    def get_remote_system_name(self):
        """
        :return: dz0@sock3t:~/w3af$ uname -n
        sock3t
        """
        return self._rSystemName

    def set_url_opener(self, uo):
        self._uri_opener = uo

    def get_url_opener(self):
        return self._uri_opener

    def set_worker_pool(self, worker_pool):
        self.worker_pool = worker_pool
    
    def get_worker_pool(self):
        return self.worker_pool

    def help(self, command):
        """
        :return: A string with the 
        """
        raise NotImplementedError('Please implement the help() method.')

    def generic_user_input(self, command, params):
        """
        This is the method that is called when a user wants to execute
        something in the shell.

        First, I trap the requests for starting the virtual daemon and
        the w3afAgent, and if this is not the case, I forward the request
        to the specific_user_input method which should be implemented by
        all shellAttackPlugins.
        """
        #
        #    Commands that are common to all shells:
        #
        if command.strip() == 'help':
            help_command = None
            if len(params) >= 1:
                help_command = params[0]
            return self.help(help_command)

        elif command == 'payload':
            #
            #    Run the payload
            #
            if params:
                return self._payload(params)

        elif command == 'lsp':
            #
            #    Based on the syscalls that we have available, list the payloads
            #    that can be run
            #
            return self._print_runnable_payloads()

        #
        #    Call the shell subclass method if needed
        #
        elif hasattr(self, 'specific_user_input'):
            # forward to the plugin
            response = self.specific_user_input(command, params)

            if response is None:
                return 'Command "%s" not found. Please type "help".' % command
            else:
                return response

    def end_interaction(self):
        """
        When the user executes "exit" in the console, this method is called.
        Basically, here we handle WHAT TO DO in that case. In most cases (and
        this is why we implemented it this way here) the response is "yes, do
        it end me" that equals to "return True".

        In some other cases, the shell prints something to the console and then
        exists, or maybe some other, more complex, thing.
        """
        return True

    def specific_user_input(self, command, parameters):
        """
        This method is called when a user writes a command in the shell and hits
        enter.

        Recommendation: Overwrite this in your customized shells

        Before calling this method, the framework calls the generic_user_input
        method from the shell class.

        :param command: The command to handle ( ie. "read", "exec", etc ).
        :param parameters: A list with the parameters for @command
        :return: The result of the command.
        """
        pass

    def _payload(self, parameters):
        """
        Handle the payload command:
            - payload desc list_processes -> return payload description
            - payload list_processes      -> run payload

        :param payload_name: The name of the payload I want to run.
        :param parameters: The parameters as sent by the user.
        """
        #
        #    Handle payload desc xyz
        #
        if len(parameters) == 2:
            if parameters[0] == 'desc':
                payload_name = parameters[1]

                if payload_name not in payload_handler.get_payload_list():
                    return 'Unknown payload name: "%s"' % payload_name

                return payload_handler.get_payload_desc(payload_name)

        #
        #    Handle payload xyz
        #
        payload_name = parameters[0]
        parameters = parameters[1:]

        if payload_name not in payload_handler.get_payload_list():
            return 'Unknown payload name: "%s"' % payload_name

        if payload_name in payload_handler.runnable_payloads(self):
            om.out.debug(
                'Payload %s can be run. Starting execution.' % payload_name)

            # Note: The payloads are actually writing to om.out.console
            # so there is no need to get the result. If someone wants to
            # get the results in a programatic way they should execute the
            # payload with use_api=True.
            try:
                payload_handler.exec_payload(self, payload_name, parameters)
                result = None
            except TypeError:
                # We get here when the user calls the payload with an incorrect
                # number of parameters:
                payload = payload_handler.get_payload_instance(
                    payload_name, self)
                result = payload.get_desc()
            except ValueError, ve:
                # We get here when one of the parameters provided by the user is
                # not of the correct type, or something like that.
                result = str(ve)
        else:
            result = ('The payload could not be run because the current shell'
                      ' doesn\'t have the required capabilities.')

        return result

    def _print_runnable_payloads(self):
        """
        Print the payloads that can be run using this exploit.

        :return: A list with all runnable payloads.
        """
        payloads = payload_handler.runnable_payloads(self)
        payloads.sort()
        return '\n'.join(payloads)

    def end(self):
        """
        This method is called when the shell is not going to be used anymore.
        It should be used to remove the auxiliary files (local and remote)
        generated by the shell.

        :return: None
        """
        pass
    
    def get_name(self):
        """
        This method is called when the shell is used, in order to create a prompt
        for the user.

        :return: The name of the shell ( os_commanding_shell, dav, etc )
        """
        msg = 'You should implement the get_name method for classes that'\
              'inherit from "shell"'
        raise NotImplementedError(msg)

    def identify_os(self):
        """
        Identify the remote operating system and get some remote variables to
        show to the user.
        
        Internally it needs to set the following attributes which are None by
        default:
            self._rOS = None
            self._rSystem = None
            self._rUser = None
            self._rSystemName = None

        """
        msg = 'Shell instances need to implement the identify_os method.'
        raise NotImplementedError(msg)

    def __repr__(self):
        if not self._rOS:
            self.identify_os()
        fmt = '<%s object (ruser: "%s" | rsystem: "%s")>'
        return fmt % (self.get_name(), self.get_remote_user(),
                      self.get_remote_system())

    __str__ = __repr__
    
    def __getattr__(self, name):
        """
        All the other methods are forwarded to the vuln object except for
        the magic methods.
        """
        if name.startswith('__'):
            raise AttributeError("%s instance has no attribute '%s'" %
                                (self.__class__.__name__, name))
        return getattr(self._vuln, name)
    
    def __setitem__(self, key, value):
        self._vuln[key] = value
    
    def __getitem__(self, key):
        return self._vuln[key]

    def __reduce__(self):
        """
        This basically means:
            * The constructor for this Class is self.__class__
            * The parameters for that constructor are:
                - A vulnerability
                - None: replacing the ExtendedUrllib we don't want to pickle
                - None: replacing the Pool we don't want to pickle
        
        When unpickling cPickle will create the Shell using:
            Shell(vuln, None, None)
        
        So, the UI has the responsibility to assign a ExtendedUrllib and a
        Pool to the Shell before it is used again.
        """
        class_name = self.__class__.__name__
        if class_name != 'Shell':
            msg = 'You need to implement __reduce__ for the Shell subclass' \
                  ' "%s". See #2181 for more details.'
            raise NotImplementedError(msg % class_name)

        return self.__class__, (self._vuln, None, None)
    
    def __eq__(self, other):
        return self._vuln == other._vuln