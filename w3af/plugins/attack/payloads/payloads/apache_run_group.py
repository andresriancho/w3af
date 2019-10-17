import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class apache_run_group(Payload):
    """
    Get apache process group.
    """

    def api_read(self):
        result = {}
        result['apache_run_group'] = []

        def parse_group_envvars(envvars_file):
            user = re.search('(?<=APACHE_RUN_GROUP=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return None

        apache_dir = self.exec_payload(
            'apache_config_directory')['apache_directory']

        if apache_dir:
            for dir in apache_dir:
                group = parse_group_envvars(self.shell.read(dir + 'envvars'))
                if group:
                    result['apache_run_group'].append(group)

                # TODO:
                # group.append(parse_group_environ(open('/proc/PIDAPACHE/environ').read()))

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['apache_run_group']:
            return 'Apache run group not found.'
        else:
            rows = []
            rows.append(['Apache run group'])
            rows.append([])
            for key_name in api_result:
                for group in api_result[key_name]:
                    rows.append([group, ])
            result_table = table(rows)
            result_table.draw(80)
            return rows
