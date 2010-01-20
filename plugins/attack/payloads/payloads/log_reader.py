#REQUIRE_LINUX
#This payload finds different readable logs on the filesystem.
import re

result = []
logs = []

logs.append('/var/log/kern.log')
logs.append('/var/log/debug')
logs.append('/var/log/dmesg')
logs.append('/var/log/syslog')
logs.append('/var/log/user.log')
logs.append('/var/log/apt/term.log')
logs.append('/var/log/Xorg.0.log')
logs.append('/var/log/dpkg.log')
logs.append('/var/log/auth.log')
logs.append('/var/log/daemon.log')
logs.append('/var/log/messages.log')
logs.append('/var/log/aptitude')
logs.append('/var/log/samba/log.nmbd')
logs.append('/var/log/gdm/:0.log')
logs.append('/var/log/message')
logs.append('/var/log/cron.log')
logs.append('/var/log/maillog')
logs.append('/var/log/qmail/')
logs.append('/var/log/httpd/')
logs.append('/var/log/lighttpd')
logs.append('/var/log/boot.log')
logs.append('/var/log/mysqld.log')
logs.append('/var/log/secure')
logs.append('/var/log/utmp')
logs.append('/var/log/qmail/')
logs.append('/var/log/wtmp')
logs.append('/var/log/yum.log')
logs.append('/var/log/mail.log')
logs.append('/var/log/faillog')
logs.append('/var/log/apache/access.log')
logs.append('/var/log/apache2/access.log')
logs.append('/var/log/apache/error.log')
logs.append('/var/log/apache2/error.log')




for i in xrange(10):
    ext = '.gz'
    if i==1:
        ext =''
    logs.append('/var/log/debug.'+str(i))
    logs.append('/var/log/daemon.log.'+str(i)+ext)
    logs.append('/var/log/auth.log.'+str(i)+ext)
    logs.append('/var/log/dmesg.'+str(i)+ext)
    logs.append('/var/log/kern.log.'+str(i)+ext)
    logs.append('/var/log/user.log.'+str(i)+ext)
    logs.append('/var/log/syslog.'+str(i)+ext)
    logs.append('/var/log/Xorg.'+str(i)+'.log')
    logs.append('/var/log/dpkg.log.'+str(i)+'.log')
    logs.append('/var/log/messages.log.'+str(i)+ext)
    logs.append('/var/log/gdm/:0.log.'+str(i))



def readable(log):
    if read(log):
        return True
    else:
        return False

def parse_apache_logs(config_file):
    error_log = re.search('(?<=ErrorLog )(.*?)\s', config_file)
    custom_log = re.search('(?<=CustomLog )(.*?)\s', config_file)
    if error_log and custom_log:
        return [error_log.group(1), custom_log.group(1)]
    elif error_log:
        return [error_log.group(1)]
    elif custom_log:
        return [custom_log.group(1)]
    else:
        return ''

config_file = run_payload('apache_config_files')
for config in config_file:
    apache_logs = parse_apache_logs(read(config))
    for log in apache_logs:
        result.append(log)

for log in logs:
    result.append(log)

result = [log for log in logs if readable(log)]


