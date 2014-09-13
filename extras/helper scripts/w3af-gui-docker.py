import subprocess, json
stdout = subprocess.check_output( "docker inspect w3af", shell=True)
ip_address = json.loads(stdout)[0]["NetworkSettings"]["IPAddress"]
p = subprocess.Popen(["ssh","-t","-t","-X", "root@" + ip_address, "/home/w3af/w3af/w3af_gui"], stdin=subprocess.PIPE)
p.communicate()
try: 
  p.close()
except:
  pass

