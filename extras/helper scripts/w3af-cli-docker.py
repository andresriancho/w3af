import subprocess, json
stdout = subprocess.check_output( "docker inspect w3af", shell=True)
ip_address = json.loads(stdout)[0]["NetworkSettings"]["IPAddress"]
subprocess.call(["ssh","-t","-t","-X", "root@" + ip_address, "/home/w3af/w3af/w3af_console"])
