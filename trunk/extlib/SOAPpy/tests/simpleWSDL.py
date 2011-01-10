import sys

sys.path.insert(1, "..")
import SOAPpy

url = 'http://www.xmethods.org/sd/2001/TemperatureService.wsdl'
zip = '06340'
proxy = SOAPpy.WSDL.Proxy(url)
temp = proxy.getTemp(zip)
print 'Temperature at', zip, 'is', temp
