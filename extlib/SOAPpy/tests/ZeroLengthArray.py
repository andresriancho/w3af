import sys
sys.path.insert(1, "..")
from SOAPpy import *

one = typedArrayType(data=[1],typed=type(1))
tmp = typedArrayType(data=[], typed=type(1))
print buildSOAP( one )
print buildSOAP( tmp )
