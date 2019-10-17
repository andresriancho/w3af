from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class netcat_installed(Payload):
    """
    This payload verifies if Netcat is installed and supports "-e filename" (program to exec after connect)
    """

    def api_read(self):
        files = []
        files.append('/bin/netcat')
        files.append('/etc/alternative/netcat')
        files.append('/bin/nc')

        #     init variables
        installed = False
        support = False
        path = None

        for _file in files:
            file_content = self.shell.read(_file)

            if file_content:
                installed = True
                path = _file

                if '-e filename' in file_content:
                    support = True

                break

        result = {'netcat_installed': installed,
                  'supports_shell_bind': support,
                  'path': path}

        return result

    def run_read(self):
        api_result = self.api_read()

        rows = []
        rows.append(['Description', 'Value'])
        rows.append([])
        for key in api_result:
            rows.append([key, str(api_result[key])])

        result_table = table(rows)
        result_table.draw(80)
        return rows
