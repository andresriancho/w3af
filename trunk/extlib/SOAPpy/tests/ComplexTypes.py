import sys
sys.path.insert(1, "..")

import SOAPpy

import time
dep = SOAPpy.dateTimeType((2004, 3, 24, 12, 30, 59, 4, 86, 0))
ret = SOAPpy.dateTimeType((2004, 3, 26, 12, 30, 59, 4, 86, 0))

in0 = SOAPpy.structType()
in0._addItem('outwardDate', dep)
in0._addItem('returnDate', ret)
in0._addItem('originAirport', 'den')
in0._addItem('destinationAirport', 'iad')


x = SOAPpy.buildSOAP(
              in0,
              method="getAirFareQuote",
              namespace="urn:SBGAirFareQuotes.sbg.travel.ws.dsdata.co.uk"
              )
              

wsdl = 'http://www.xmethods.net/sd/2001/TemperatureService.wsdl'
proxy = SOAPpy.WSDL.Proxy(wsdl)

