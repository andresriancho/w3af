'''
utils.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.
    
w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
'''
#Keys representing CSP headers for manipulations (values from W3C Specs).
CSP_HEADER_W3C = "Content-Security-Policy"
CSP_HEADER_FIREFOX = "X-Content-Security-Policy"
CSP_HEADER_CHROME = "X-WebKit-CSP"
CSP_HEADER_IE = "X-Content-Security-Policy"
CSP_HEADER_W3C_REPORT_ONLY = "Content-Security-Policy-Report-Only"

#Keys representing CSP directives names for manipulations (values from W3C Specs).
CSP_DIRECTIVE_DEFAULT = "default-src"
CSP_DIRECTIVE_SCRIPT = "script-src"
CSP_DIRECTIVE_OBJECT = "object-src"
CSP_DIRECTIVE_STYLE = "style-src"
CSP_DIRECTIVE_IMAGE = "img-src"
CSP_DIRECTIVE_MEDIA = "media-src"
CSP_DIRECTIVE_FRAME = "frame-src"
CSP_DIRECTIVE_FONT = "font-src"
CSP_DIRECTIVE_CONNECTION = "connect-src"
CSP_DIRECTIVE_REPORT_URI = "report-uri"

#Keys representing CSP directives values for manipulations (values from W3C Specs).
CSP_DIRECTIVE_VALUE_UNSAFE_INLINE = "unsafe-inline"


def unsafe_inline_enabled(response):
    '''
    Method to detect if CSP Policies are specified for Script/Style, 
    to allow unsafe inline content to be loaded.
    
    @param response: A HTTPResponse object.
    @return: True if CSP Policies are specified for Script/Style to allow 
             unsafe inline content to be loaded, False otherwise. 
    '''
    ##Extract and merge all policies
    non_report_only_policies = retrieve_csp_policies(response)
    report_only_policies = retrieve_csp_policies(response, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    #Parse policies dictionary : Iterate on Values
    if(len(policies_all) > 0):
        for directive_name in policies_all:
            #Apply check only on Script and Style directives in order to be 
            #coherent with the W3C Specs, because only theses 2 directives 
            #supports the "unsafe-inline" directive value...
            if (directive_name.lower() != CSP_DIRECTIVE_SCRIPT 
                and directive_name.lower() != CSP_DIRECTIVE_STYLE):
                continue
            #Iterate on Directive values (normally values here are all URI)
            for directive_value in policies_all[directive_name]:               
                if directive_value.strip().lower() == CSP_DIRECTIVE_VALUE_UNSAFE_INLINE:
                    #Return directly to enhance performance...
                    return True
    return False
    

def provides_csp_features(response):
    '''
    Method to detect if url provides CSP features.
    
    @param response: A HTTPResponse object.
    @return: True if the URL provides CSP features, False otherwise. 
    '''
    return ((len(retrieve_csp_policies(response)) 
             + len(retrieve_csp_policies(response, True))) > 0)

def retrieve_csp_report_uri(response):
    '''
    Method to retrieve all report uri from CSP Policies specified into a HTTP 
    response through CSP headers.
       
    @param response: A HTTPResponse object.      
    @return: A set of URIs
    ''' 
    uri_set = set()
    ##Extract and all merge policies
    non_report_only_policies = retrieve_csp_policies(response)
    report_only_policies = retrieve_csp_policies(response, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    #Iterate on Directives
    if(len(policies_all) > 0):
        for directive_name in policies_all:
            if directive_name.lower() != CSP_DIRECTIVE_REPORT_URI:
                continue
            #Iterate on Directive values (normally values here are all URI)
            for directive_value in policies_all[directive_name]:               
                uri = directive_value.strip().lower()
                uri_set.add(uri)                       
    return uri_set

def retrieve_csp_policies(response, select_only_reportonly_policies=False):
    '''
    Method to retrieve all CSP Policies specified into a HTTP response 
    through CSP headers.
       
    @param response: A HTTPResponse object.
    @param select_only_reportonly_policies: Optional parameter to indicate to 
                                            method to retrieve only REPORT-ONLY 
                                            CSP policies (default is False).      
    @return: A dictionary in which KEY is a CSP directive and VALUE is the 
             list of associated policies.
    '''   
    headers = response.get_headers()
    policies = {}
     
    for header_name in headers:
        header_name_upperstrip = header_name.upper().strip()
        #Define header processing condition according to 
        #"select_only_reportonly_policies" parameter value 
        if not select_only_reportonly_policies:
            if (header_name_upperstrip != CSP_HEADER_W3C.upper() 
                and header_name_upperstrip != CSP_HEADER_FIREFOX.upper() 
                and header_name_upperstrip != CSP_HEADER_CHROME.upper() 
                and header_name_upperstrip != CSP_HEADER_IE.upper()):
                continue
        else:
            if header_name_upperstrip != CSP_HEADER_W3C_REPORT_ONLY.upper():
                continue                              
        #Process header value	                   	
        #Retrieve the CSP directive list : A Policy is defined by a directive 
        #name and one or several associated values
        directive_list = headers[header_name].strip()
        #Parse CSP directives list using W3C Specs algorithm : 
        #A CSP header value can specify several directives using ";" separator
        directives = directive_list.split(";")
        #For each directive we extract the directive name and is values 
        #(several can be specified)
        for directive in directives:
            directive_strip = directive.strip()
            #Manage empty case
            if len(directive_strip) <= 0:
                continue
            #Directive name and value are separated by a single space 
            #Value can itself contains several sub values separated by a space
            parts = directive_strip.split(" ")
            #There must exists at least 2 parts otherwise we ignore the value...
            if len(parts) < 2:
                continue
            #Retrieve directive name
            directive_name = parts[0].lower()
            #Retrieve directive valueS
            parts.pop(0)
            directive_values = parts
            #Add policy to dictionary
            if directive_name not in policies:
                policies[directive_name] = []
            for directive_value in directive_values:
                #Remove quote and double quote from value to unify result 
                #string content
                tmp_value = directive_value.replace("'", "")
                tmp_value = tmp_value.replace('"', '')             			
                policies[directive_name].append(tmp_value)
    return policies

def merge_policies_dict(non_report_only_policies_dict, report_only_policies_dict):
    '''
    Method to merge 2 Policies dictionaries to a single.
               
    @param non_report_only_policies_dict: A dictionary with all non 
                                          REPORT-ONLY Policies 
                                          (return of method "retrieve_csp_policies").
    @param report_only_policies_dict: A dictionary with all REPORT-ONLY 
                                      Policies 
                                      (return of method "retrieve_csp_policies").      
    @return: A merged dictionary in which KEY is a CSP directive 
             and VALUE is the list of associated policies.
    '''
    #Short circuit precheck...
    if(non_report_only_policies_dict is None 
       or len(non_report_only_policies_dict) == 0):
        return report_only_policies_dict
    if(report_only_policies_dict is None 
       or len(report_only_policies_dict) == 0):
        return non_report_only_policies_dict
    
    merged_policies = {}
    #Create a list from union of directives names (remove duplicate items)
    directives_names = list(set(non_report_only_policies_dict.keys() 
                                + report_only_policies_dict.keys()))
    #Parse it to merge list of values for each key (remove duplicate items)
    for k in directives_names:
        values = []
        if k in non_report_only_policies_dict:
            values.extend(non_report_only_policies_dict[k])
        if k in report_only_policies_dict:
            values.extend(report_only_policies_dict[k])
        merged_policies[k] = list(set(values))        
    return merged_policies
