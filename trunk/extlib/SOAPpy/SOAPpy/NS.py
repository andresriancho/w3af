"""
################################################################################
#
# SOAPpy - Cayce Ullman       (cayce@actzero.com)
#          Brian Matthews     (blm@actzero.com)
#          Gregory Warnes     (Gregory.R.Warnes@Pfizer.com)
#          Christopher Blunck (blunck@gst.com)
#
################################################################################
# Copyright (c) 2003, Pfizer
# Copyright (c) 2001, Cayce Ullman.
# Copyright (c) 2001, Brian Matthews.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# Neither the name of actzero, inc. nor the names of its contributors may
# be used to endorse or promote products derived from this software without
# specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
"""

from __future__ import nested_scopes

ident = '$Id: NS.py,v 1.4 2005/02/15 16:32:22 warnes Exp $'
from version import __version__

##############################################################################
# Namespace Class
################################################################################
def invertDict(dict):
    d = {}

    for k, v in dict.items():
        d[v] = k

    return d

class NS:
    XML  = "http://www.w3.org/XML/1998/namespace"

    ENV  = "http://schemas.xmlsoap.org/soap/envelope/"
    ENC  = "http://schemas.xmlsoap.org/soap/encoding/"

    XSD  = "http://www.w3.org/1999/XMLSchema"
    XSD2 = "http://www.w3.org/2000/10/XMLSchema"
    XSD3 = "http://www.w3.org/2001/XMLSchema"

    XSD_L = [XSD, XSD2, XSD3]
    EXSD_L= [ENC, XSD, XSD2, XSD3]

    XSI   = "http://www.w3.org/1999/XMLSchema-instance"
    XSI2  = "http://www.w3.org/2000/10/XMLSchema-instance"
    XSI3  = "http://www.w3.org/2001/XMLSchema-instance"
    XSI_L = [XSI, XSI2, XSI3]

    URN   = "http://soapinterop.org/xsd"

    # For generated messages
    XML_T = "xml"
    ENV_T = "SOAP-ENV"
    ENC_T = "SOAP-ENC"
    XSD_T = "xsd"
    XSD2_T= "xsd2"
    XSD3_T= "xsd3"
    XSI_T = "xsi"
    XSI2_T= "xsi2"
    XSI3_T= "xsi3"
    URN_T = "urn"

    NSMAP       = {ENV_T: ENV, ENC_T: ENC, XSD_T: XSD, XSD2_T: XSD2,
                    XSD3_T: XSD3, XSI_T: XSI, XSI2_T: XSI2, XSI3_T: XSI3,
                    URN_T: URN}
    NSMAP_R     = invertDict(NSMAP)

    STMAP       = {'1999': (XSD_T, XSI_T), '2000': (XSD2_T, XSI2_T),
                    '2001': (XSD3_T, XSI3_T)}
    STMAP_R     = invertDict(STMAP)

    def __init__(self):
        raise Error, "Don't instantiate this"



