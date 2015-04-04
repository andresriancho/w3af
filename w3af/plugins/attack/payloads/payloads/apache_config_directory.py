import re

from w3af.plugins.attack.payloads.base_payload import Payload, read_error_handler
from w3af.core.ui.console.tables import table
from w3af.core.controllers.exceptions import BaseFrameworkException


class apache_config_directory(Payload):
    """
    This payload finds Apache's config directories.
    """
    def fname_generator(self):
        def parse_apache2_init(apache_file_read):
            directory = re.search('(?<=APACHE_PID_FILE needs to be defined in )(.*?)envvars',
                                  apache_file_read)
            if directory:
                return directory.group(1)
            else:
                return ''

        def parse_apache_init(apache_file_read):
            directory = re.search('(?<=APACHE_HOME=")(.*?)\"', apache_file_read)
            if directory:
                return directory.group(1)
            else:
                return ''

        paths = ['/etc/apache2/',
                 '/etc/apache/',
                 '/etc/httpd/',
                 '/usr/local/apache2/conf/',
                 '/usr/local/apache/conf/',
                 '/usr/local/etc/apache/',
                 '/usr/local/etc/apache2/',
                 '/opt/apache/conf/',
                 '/etc/httpd/conf/',
                 '/usr/pkg/etc/httpd/',
                 '/usr/local/etc/apache22/']

        try:
            parsed_1 = parse_apache2_init(self.shell.read('/etc/init.d/apache2'))
            parsed_2 = parse_apache_init(self.shell.read('/etc/init.d/apache'))
        except BaseFrameworkException:
            parsed_1 = None
            parsed_2 = None

        for parsed_path in (parsed_1, parsed_2):
            if parsed_path:
                paths.append(parsed_path)

        for path in paths:
            yield path + 'httpd.conf'
            yield path + 'apache2.conf'

    def api_read(self):
        result = {'apache_directory': []}

        fname_iter = self.fname_generator()
        for file_path, content in self.read_multi(fname_iter,
                                                  error_handler=read_error_handler):
            for keyword in ('#', 'NCSA', 'Global'):
                if keyword in content:
                    file_path = file_path.replace('httpd.conf', '')
                    file_path = file_path.replace('apache2.conf', '')
                    result['apache_directory'].append(file_path)
                    break

        result['apache_directory'] = list(set(result['apache_directory']))

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['apache_directory']:
            return 'Apache configuration directory not found.'
        else:
            rows = [['Apache directories', ], []]
            for key_name in api_result:
                for path in api_result[key_name]:
                    rows.append([path, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
