import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class apache_run_user(Payload):
    """
    Get apache process user.
    """
    def api_read(self):
        result = {}
        result['apache_run_user'] = []

        def parse_user_envvars(envvars_file):
            user = re.search('(?<=APACHE_RUN_USER=)(.*)', envvars_file)
            if user:
                return user.group(1)
            else:
                return None

        apache_dir = self.exec_payload(
            'apache_config_directory')['apache_directory']

        if apache_dir:
            for dir in apache_dir:
                user = parse_user_envvars(self.shell.read(dir + 'envvars'))
                if user:
                    result['apache_run_user'].append(user)

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['apache_run_user']:
            return 'Apache run user not found.'
        else:
            rows = []
            rows.append(['Apache run user'])
            rows.append([])
            for key_name in api_result:
                for user in api_result[key_name]:
                    rows.append([user, ])
            result_table = table(rows)
            result_table.draw(80)
            return rows
