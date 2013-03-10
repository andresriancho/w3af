'''
disk_csp_vuln_store_item.py

Copyright 2013 Andres Riancho

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

'''
from core.data.db.disk_item import DiskItem

class DiskCSPVulnStoreItem(DiskItem):
    '''
    This is a class to store CSP vulnerabilities found 
    for a URL (URL+ID) in a DiskList or DiskSet.
    '''

    '''
    Constructor.
    @param r_url: HTTP reponse url
    @param r_id: HTTP reponse ID
    @param r_vulns: CSP vulnerabilities found
    '''
    def __init__(self, r_url, r_id, r_vulns):
    	self.url = r_url
    	self.resp_id = r_id
    	self.csp_vulns = r_vulns

    '''
    Implements method from base class.
    '''
    def get_eq_attrs(self):
        return ['url','resp_id']