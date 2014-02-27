from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class hosts(Payload):
    """
    This payload shows the hosts allow and deny files.
    """
    def api_read(self):
        result = {}
        hosts = []

        hosts.append('/etc/hosts')
        hosts.append('/etc/hosts.allow')
        hosts.append('/etc/hosts.deny')

        for file in hosts:
            content = self.shell.read(file)
            if content:
                result[file] = content
        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'Hosts files not found.'
        else:
            rows = []
            rows.append(['Host file', 'Content'])
            rows.append([])
            for file in api_result:
                rows.append([file, api_result[file]])
                rows.append([])

            result_table = table(rows[:-1])
            result_table.draw(160)
            return rows
