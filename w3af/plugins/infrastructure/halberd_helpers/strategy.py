"""
strategy.py

Copyright 2014 Andres Riancho

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
import Halberd

from Halberd.shell import UniScanStrategy


class CustomScanStrategy(UniScanStrategy):
    def _scan(self):
        """
        Allocates a work crew of scanners and launches them on the target.
        """
        assert self.task.url and self.task.addr

        self.task.clues = []
        self.task.analyzed = []
        crew = Halberd.crew.WorkCrew(self.task)

        # This is why I override the scan method, to disable the signal handling
        # that halberd uses, which doesn't allow me to run it in a thread.
        crew._setupSigHandler = lambda: None
        crew._restoreSigHandler = lambda: None

        self.task.clues = crew.scan()