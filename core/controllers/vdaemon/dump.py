import sys
res = 'fileDump = \''

for i in file(sys.argv[1]).read():
  res += '\\x' + hex(ord(i))[2:].zfill(2)

res += '\''
print res
