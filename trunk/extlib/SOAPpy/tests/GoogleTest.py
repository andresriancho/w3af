from SOAPpy import WSDL
server = WSDL.Proxy('/home/warneg/src/google/googleapi/GoogleSearch.wsdl')
key = "6k0oDPZQFHL0zpjy6ZO6ufUVFKBgvqTo"

results = server.doGoogleSearch(key, 'warnes', 0, 10, False, "", 
                                False, "", "utf-8", "utf-8") 


for i in range(len(results.resultElements)):
  res = results.resultElements[i]
  print '%d: %s --> %s' % ( i, res.title, res.URL )
