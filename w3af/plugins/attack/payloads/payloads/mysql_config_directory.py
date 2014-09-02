import re

from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class mysql_config_directory(Payload):
    """
    This payload finds MySQL configuration directory.
    """
    def api_read(self):
        result = {'directory': []}
        paths = []

        def parse_mysql_init(mysql_init):
            directory = re.search(
                '(?<=$0: WARNING: )(.*?)my.cnf cannot', mysql_init)
            if directory:
                return directory.group(1)
            else:
                return ''

        def check_mysql_config_dir(mysql):
            my = self.shell.read(mysql + 'my.cnf')
            if my != '':
                return True
            else:
                return False

        paths.append(parse_mysql_init(self.shell.read('/etc/init.d/mysql')))
        paths.append('/etc/mysql/')
        paths.append('/etc/')
        paths.append('/opt/local/etc/mysql5/')
        paths.append('/var/lib/mysql/')

        folders = self.exec_payload('users')
        for folder in folders:
            paths.append(folder)

        for path in paths:
            if check_mysql_config_dir(path):
                result['directory'].append(path)

        result['directory'] = list(set(result['directory']))
        result['directory'] = [p for p in result['directory'] if p != '']
        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No MySQL configuration directories were found.'
        else:
            rows = [['MySQL configuration directory'], []]
            for directory in api_result['directory']:
                rows.append([directory, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
