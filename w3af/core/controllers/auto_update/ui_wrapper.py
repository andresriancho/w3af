"""
auto_update.py

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
import os

from w3af.core.controllers.misc.home_dir import (verify_dir_has_perm,
                                                 W3AF_LOCAL_PATH)
from w3af.core.controllers.auto_update.version_manager import VersionMgr
from w3af.core.controllers.auto_update.utils import is_git_repo


class UIUpdater(object):
    """
    Base class that provides an API for UI update workers.
    """

    def __init__(self, force=False, ask=None, logger=None):
        self._force_upd = force
        self._ask = ask
        self._logger = logger
        self._callbacks = {'callback_onupdate_confirm': ask}
        self._registries = {}

    @property
    def _vmngr(self):
        vmngr = getattr(self, '__vmngr', None)
        if vmngr is None:
            vmngr = VersionMgr(log=self._logger)
            [setattr(vmngr, n, c) for n, c in self._callbacks.items()]
            [vmngr.register(ev, val[0], val[1]) for ev, val in
             self._registries.items()]
            setattr(self, '__vmngr', vmngr)
        return vmngr

    def _add_callback(self, callback_name, callback):
        self._callbacks[callback_name] = callback

    def _register(self, event, func, msg):
        self._registries[event] = (func, msg)

    def update(self):
        if self._force_upd in (None, True) and is_git_repo() and \
        verify_dir_has_perm(W3AF_LOCAL_PATH, os.W_OK, levels=1):
            try:
                resp = self._call_update()
                self._handle_update_output(resp)
            except KeyboardInterrupt:
                pass
            except Exception, ex:
                self._logger('An error occurred while updating: "%s"' % ex)

            # TODO: Please read https://github.com/andresriancho/w3af/issues/6
            # for more information on what's missing here 
            """
            if repo_has_conflicts():
                self._log("Oops!... w3af can't be started. It seems that the "
                          "last auto update process was unsuccessful.\n\n"
                          "Please update manually by executing a regular 'git pull' "
                          "in the w3af installation directory.\n")
                sys.exit(1)
            """

    def _call_update(self):
        return self._vmngr.update(self._force_upd)

    def _handle_update_output(self, resp):
        raise NotImplementedError("Must be implemented by subclass")

    def _log(self, msg):
        print msg
