import os

import w3af.core.controllers.output_manager as om

from w3af import ROOT_PATH
from w3af.core.ui.console.tables import table
from w3af.core.controllers.threads.threadpool import return_args
from w3af.plugins.attack.payloads.base_payload import Payload


class rootkit_hunter(Payload):
    """
    This payload checks for current rootkits, trojans, backdoors and local
    xploits installed on system.
    """
    def _read_with_progress(self, filename):
        #   "progress bar"
        self.k -= 1
        if self.k == 0:
            om.out.console('.', new_line=False)
            self.k = 400
        #   end "progress bar"

        content = self.shell.read(filename)

        return content

    def fname_generator(self):
        #    Rootkit information taken from:
        #    Rootkit Hunter Shell Script by Michael Boelen
        #
        #    TODO: Find a way to keep the DB updated!
        for fname in file(os.path.join(ROOT_PATH, 'plugins', 'attack',
                                       'payloads', 'payloads', 'rootkit_hunter',
                                       'rootkit_hunter_files.db')):
            fname = fname.strip()
            if fname and not fname.startswith('#'):
                yield fname

    def _check_kernel_modules(self):
        # Known bad Linux kernel modules
        bad_kernel_modules = []
        bad_kernel_modules.append('adore.o')
        bad_kernel_modules.append('bkit-adore.o')
        bad_kernel_modules.append('cleaner.o')
        bad_kernel_modules.append('flkm.o')
        bad_kernel_modules.append('knark.o')
        bad_kernel_modules.append('modhide.o')
        bad_kernel_modules.append('mod_klgr.o')
        bad_kernel_modules.append('phide_mod.o')
        bad_kernel_modules.append('vlogger.o')
        bad_kernel_modules.append('p2.ko')
        bad_kernel_modules.append('rpldev.o')
        bad_kernel_modules.append('xC.o')
        bad_kernel_modules.append('rpldev.o')
        bad_kernel_modules.append('strings.o')
        bad_kernel_modules.append('wkmr26.ko')
        bad_kernel_modules.append('backd00r')
        bad_kernel_modules.append('backdoor')
        bad_kernel_modules.append('darkside')
        bad_kernel_modules.append('nekit')
        bad_kernel_modules.append('rpldev')
        bad_kernel_modules.append('rpldev_mod')
        bad_kernel_modules.append('spapem_core')
        bad_kernel_modules.append('spapem_genr00t')

        kernel_modules = self.exec_payload('list_kernel_modules')
        for module in bad_kernel_modules:
            if module in kernel_modules:
                self.result['bad_kernel_modules'].append(module)

    def api_read(self):
        self.result = {}
        self.result['bad_kernel_modules'] = []
        self.result['backdoor_files'] = []
        self.k = 400

        self._check_kernel_modules()

        read_file = return_args(self._read_with_progress)
        fname_iter = self.fname_generator()
        for (file_name,), content in self.worker_pool.imap_unordered(read_file, fname_iter):
            if content:
                self.result['backdoor_files'].append(file_name)

        return self.result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'Rootkit hunter failed to run.'
        else:
            rows = []
            rows.append(['Description', 'Value'])
            rows.append([])
            for key in api_result:
                for value in api_result[key]:
                    rows.append([key, value])

            result_table = table(rows)
            result_table.draw(80)
            return rows
