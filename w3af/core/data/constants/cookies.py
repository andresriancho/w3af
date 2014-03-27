"""
cookies.py

Copyright 2006 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import operator

GENERIC_COOKIES = set(['JServSessionID',
                       'JWSESSIONID',
                       'SESSID',
                       'SESSION',
                       'session_id'])


COOKIE_FINGERPRINT = (
        ('st8id', 'Teros web application firewall'),
        ('ASINFO', 'F5 TrafficShield'),
        ('NCI__SessionId', 'Netcontinuum'),

        # oracle
        ('$OC4J_', 'Oracle container for java'),

        # Java
        ('JSESSIONID', 'Jakarta Tomcat / Apache'),
        ('JServSessionIdroot', 'Apache JServ'),

        # ASP
        ('ASPSESSIONID', 'ASP'),
        ('ASP.NET_SessionId', 'ASP.NET'),

        # PHP
        ('PHPSESSID', 'PHP'),
        ('PHPSESSION', 'PHP'),

        # SAP
        ('sap-usercontext=sap-language=', 'SAP'),

        # Others
        ('WebLogicSession', 'BEA Logic'),
        ('SaneID', 'Sane NetTracker'),
        ('ssuid', 'Vignette'),
        ('vgnvisitor', 'Vignette'),
        ('SESSION_ID', 'IBM Net.Commerce'),
        ('NSES40Session', 'Netscape Enterprise Server'),
        ('iPlanetUserId', 'iPlanet'),
        ('RMID', 'RealMedia OpenADStream'),
        ('cftoken', 'Coldfusion'),
        ('PORTAL-PSJSESSIONID', 'PeopleSoft'),
        ('WEBTRENDS_ID', 'WebTrends'),
        ('sesessionid', 'IBM WebSphere'),
        ('CGISESSID', 'Perl CGI::Session'),
        ('GX_SESSION_ID', 'GeneXus'),
        ('SESSIONID', 'Apache'),
        ('WC_SESSION_ESTABLISHED', 'WSStore'),

    )

ALL_COOKIES = set(map(operator.itemgetter(0), COOKIE_FINGERPRINT))
ALL_COOKIES.update(GENERIC_COOKIES)