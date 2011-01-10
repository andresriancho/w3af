#!/usr/bin/env python

import string
import cgi

ident = '$Id: interop2html.py,v 1.1.1.1 2001/06/27 21:36:14 cullman Exp $'

lines = open('output.txt').readlines()
#preserve the tally
tally = lines[-6:]
#whack the tally from lines
lines = lines[:-6]
table={}
for line in lines:
  if line[:3] == '   ' or line == '>\n' : continue
  line = line[:-1]  #delete end of line char
  row = [line[:line.find(': ')], line[line.find(': ')+2:]]  #split server name from rest of line
  restofrow = row[1].split(' ',3)  #break out method name, number, status code, status comment
  if len(restofrow) > 3:
    if restofrow[3].find('as expected') != -1:
      restofrow[2] = restofrow[2] + ' (as expected)'
    elif restofrow[3][:2] == '- ' :
      restofrow[3] = restofrow[3][2:] 
  try: table[row[0]].append([restofrow[0],restofrow[2:]])
  except KeyError: table[row[0]] = [[restofrow[0],restofrow[2:]]]

print "<html><body>"
print "<script>function popup(text) {"
print "text = '<html><head><title>Test Detail</title></head><body><p>' + text + '</p></body></html>';"
print "newWin=window.open('','win1','location=no,menubar=no,width=400,height=200');"
print "newWin.document.open();"
print "newWin.document.write(text);"
print "newWin.focus();  } </script>"
print "<br><table style='font-family: Arial; color: #cccccc'><tr><td colspan=2><font face=arial color=#cccccc><b>Summary</b></font></td></tr>"
for x in tally:
  z = x[:-1].split(":",1)
  print "<tr><td><font face=arial color=#cccccc>",z[0],"</font></td><td><font face=arial color=#cccccc>",z[1],"</font></td></tr>"
print "</table><br>"
c = 0
totalmethods = len(table[table.keys()[0]])
while c < totalmethods:
  print "<br><table width='95%' style='font-family: Arial'>"
  print "<tr><td width='27%' bgcolor='#cccccc'></td>"
  cols = [c, c + 1, c + 2]
  if c != 16:
    cols += [c + 3]
  for i in cols:
    try: header = table[table.keys()[0]][i][0]
    except: break
    print "<td width ='17%' align='center' bgcolor='#cccccc'><b>",header,"</b></td>"
  print "</tr>"
  l = table.keys()
  l.sort()
  for key in l:
    print "<tr><td bgcolor='#cccccc'>", key , "</td>"
    for i in cols:
      try: status = table[key][i][1][0]
      except: break
      if status.find("succeed") != -1:
        bgcolor = "#339900"
        status = "Pass"
      elif status.find("expected") != -1:
        bgcolor = "#FF9900"
        hreftitle = table[key][i][1][1].replace("'","") # remove apostrophes from title properties
        popuphtml = '"' + cgi.escape(cgi.escape(table[key][i][1][1]).replace("'","&#39;").replace('"',"&#34;")) + '"'
        status = "<a title='" + hreftitle + "' href='javascript:popup(" + popuphtml + ")'>Failed (expected)</a>"
      else:
        bgcolor = "#CC0000"
        hreftitle = table[key][i][1][1].replace("'","") # remove apostrophes from title properties
        popuphtml = '"' + cgi.escape(cgi.escape(table[key][i][1][1]).replace("'","&#39;").replace('"',"&#34;")) + '"'
        status = "<a title='" + hreftitle + "' href='javascript:popup(" + popuphtml + ")'>Failed</a>"
      print "<td align='center' bgcolor=" , bgcolor , ">" , status , "</td>"
    print "</tr>"
  print "</table>"
  c = c + len(cols)
print "</body></html>"
