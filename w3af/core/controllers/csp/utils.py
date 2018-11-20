"""
utils.py

Copyright 2012 Andres Riancho

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
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
"""
from mimetypes import MimeTypes
from collections import namedtuple

import w3af.core.data.constants.severity as severity

# Keys representing CSP headers for manipulations
# (values from W3C Specs).
CSP_HEADER_W3C = "Content-Security-Policy"
CSP_HEADER_FIREFOX = "X-Content-Security-Policy"
CSP_HEADER_CHROME = "X-WebKit-CSP"
CSP_HEADER_IE = "X-Content-Security-Policy"
CSP_HEADER_W3C_REPORT_ONLY = "Content-Security-Policy-Report-Only"

# Keys representing CSP directives names for manipulations
# (values from W3C Specs).
CSP_DIRECTIVE_DEFAULT = "default-src"
CSP_DIRECTIVE_SCRIPT = "script-src"
CSP_DIRECTIVE_OBJECT = "object-src"
CSP_DIRECTIVE_STYLE = "style-src"
CSP_DIRECTIVE_IMAGE = "img-src"
CSP_DIRECTIVE_MEDIA = "media-src"
CSP_DIRECTIVE_FRAME = "frame-src"
CSP_DIRECTIVE_FRAME_ANCESTORS = "frame-ancestors"
CSP_DIRECTIVE_FONT = "font-src"
CSP_DIRECTIVE_CONNECTION = "connect-src"
CSP_DIRECTIVE_REPORT_URI = "report-uri"
CSP_DIRECTIVE_FORM = "form-action"
CSP_DIRECTIVE_SANDBOX = "sandbox"
CSP_DIRECTIVE_SCRIPT_NONCE = "script-nonce"
CSP_DIRECTIVE_PLUGIN_TYPES = "plugin-types"
CSP_DIRECTIVE_XSS = "reflected-xss"

# Keys representing key used to store misspelled directives name
# in extraction dictionary
CSP_MISSPELLED_DIRECTIVES = "misspelled-directives-name"

# Keys representing CSP directives values for manipulations
# (values from W3C Specs).
CSP_DIRECTIVE_VALUE_UNSAFE_INLINE = "unsafe-inline"
CSP_DIRECTIVE_VALUE_UNSAFE_EVAL = "unsafe-eval"
CSP_DIRECTIVE_VALUE_ALLOW_FORMS = "allow-forms"
CSP_DIRECTIVE_VALUE_ALLOW_SAME_ORIGIN = "allow-same-origin"
CSP_DIRECTIVE_VALUE_ALLOW_SCRIPTS = "allow-scripts"
CSP_DIRECTIVE_VALUE_ALLOW_TOP_NAV = "allow-top-navigation"
CSP_DIRECTIVE_VALUE_XSS_BLOCK = "block"
CSP_DIRECTIVE_VALUE_XSS_ALLOW = "allow"
CSP_DIRECTIVE_VALUE_XSS_FILTER = "filter"

# Note: Special directive refer to directive for which empty value specify a
# behavior, on W3C CSP Specs v1.1 theses directives are:
# -> sandbox
# -> script-nonce

# Valid Mime Types list
MIME_TYPES = MimeTypes().types_map[1].values()

# Define NamedTuple tuple subclass to represents a CSP vulnerability.
# Declare type here in order to expose it with project visibility
# and permit cPickle processing to see it. See link below:
# http://stackoverflow.com/questions/4677012/python-cant-pickle-type-x-attribute-lookup-failed
CSPVulnerability = namedtuple('CSPVulnerability', ['desc', 'severity'])            


def site_protected_against_xss_by_csp(response,
                                      allow_unsafe_inline=False,
                                      allow_unsafe_eval=False):
    """
    Method to analyze if a site is protected against XSS vulns type using
    CSP policies.
    
    :param response: A HTTPResponse object.
    :param allow_unsafe_eval: Allow inline javascript code block.
    :param allow_unsafe_eval: Allow use of the java "eval()" function in
                              javascript code block.  
    :return: True only if the site is protected, False otherwise.  
    """
    protected = True
    
    if not provides_csp_features(response):
        protected = False
    else:
        # Try to find vulns on CSP policies related to Script
        vulns = find_vulns(response)
        if CSP_DIRECTIVE_SCRIPT in vulns:            
            protected = False
        else:
            # Check Script dedicated directive value for
            # - inline javascript code block
            # - "eval()" javascript function
            if not allow_unsafe_inline and unsafe_inline_enabled(response):
                protected = False
            if not allow_unsafe_eval and unsafe_eval_enabled(response):
                protected = False
    
    return protected


def find_vulns(response):
    """
    Method to find vulnerabilities into CSP policies from an HTTP response,
    analyze directives for permissive/invalid configuration and misspelled
    directive names.
    
    :param response: A HTTPResponse object.
    :return: A dictionary in which KEY is a CSP directive and VALUE is the 
             list of vulnerabilities found for the associated directive.
             A vulnerability is represented as NamedTuple exposing properties
             "desc" and "severity", both as String data type.
             Access example: vulns[CSP_DIRECTIVE_DEFAULT][0].desc
    """
    vulns = {}
    
    # Extract and merge all policies
    non_report_only_policies = retrieve_csp_policies(response, False, True)
    report_only_policies = retrieve_csp_policies(response, True, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    
    # Quick exit to enhance performance
    if len(policies_all) == 0:
        return vulns
        
    # Analyze each policy in details.
    # Code analyse each directive independently in order to prepare algorithm to
    # be enhanced with CSP specs evolution !
    # Directive "default-src"
    if CSP_DIRECTIVE_DEFAULT in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_DEFAULT]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'default-src' allows all sources.",
                                        severity.HIGH)
            vulns_lst = [csp_vuln]
            vulns[CSP_DIRECTIVE_DEFAULT] = vulns_lst
    # Directive "script-src"
    if CSP_DIRECTIVE_SCRIPT in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_SCRIPT]
        vulns_lst = []
        warn_msg = ""        
        # We do not check for 'unsafe-inline' and 'unsafe-eval' values because:
        # =>Many site use inline javascript code block
        # =>Some popular javascript API (ex: JQueryUI/ExtJS) use eval() function
        if "*" in directive_values:
            warn_msg = "Directive 'script-src' allows all javascript sources."
            csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
            vulns_lst.append(csp_vuln)   
        if CSP_DIRECTIVE_SCRIPT_NONCE not in policies_all:
            warn_msg = ("Directive 'script-src' is defined but no directive"
                        " 'script-nonce' is defined to protect javascript"
                        " resources.")
            csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
            vulns_lst.append(csp_vuln)                
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_SCRIPT] = vulns_lst            
    # Directive "object-src"
    if CSP_DIRECTIVE_OBJECT in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_OBJECT]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'object-src' allows all plugin sources.",
                                        severity.HIGH)            
            vulns_lst = [csp_vuln]
            vulns[CSP_DIRECTIVE_OBJECT] = vulns_lst
    # Directive "style-src"
    if CSP_DIRECTIVE_STYLE in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_STYLE]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'style-src' allows all CSS sources.",
                                        severity.LOW)            
            vulns_lst = [csp_vuln]
            vulns[CSP_DIRECTIVE_STYLE] = vulns_lst
    # Directive "img-src"
    if CSP_DIRECTIVE_IMAGE in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_IMAGE]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'img-src' allows all image sources.",
                                        severity.LOW)               
            vulns_lst = [csp_vuln]
            vulns[CSP_DIRECTIVE_IMAGE] = vulns_lst
    # Directive "media-src"
    if CSP_DIRECTIVE_MEDIA in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_MEDIA]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'media-src' allows all audio/video sources.",
                                        severity.HIGH)            
            vulns_lst = [csp_vuln]
            vulns[CSP_DIRECTIVE_MEDIA] = vulns_lst
    # Directive "frame-src"
    if CSP_DIRECTIVE_FRAME in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_FRAME]
        vulns_lst = []
        warn_msg = ""
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'frame-src' allows all sources.",
                                        severity.HIGH)            
            vulns_lst.append(csp_vuln)
        if CSP_DIRECTIVE_SANDBOX not in policies_all:
            warn_msg = "Directive 'frame-src' is defined but no directive " \
            "'sandbox' is defined to protect resources. Perhaps sandboxing " \
            "is defined at html attribute level ?"
            csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
            vulns_lst.append(csp_vuln)                
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_FRAME] = vulns_lst
    # Directive "font-src"
    if CSP_DIRECTIVE_FONT in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_FONT]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'font-src' allows all font sources.",
                                        severity.MEDIUM)               
            vulns_lst = [csp_vuln]            
            vulns[CSP_DIRECTIVE_FONT] = vulns_lst
    # Directive "connect-src"
    if CSP_DIRECTIVE_CONNECTION in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_CONNECTION]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'connect-src' allows all connection sources.",
                                        severity.HIGH)               
            vulns_lst = [csp_vuln]                        
            vulns[CSP_DIRECTIVE_CONNECTION] = vulns_lst
    # Directive "form-action"
    if CSP_DIRECTIVE_FORM in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_FORM]
        if "*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'form-action' allows all action target.",
                                        severity.HIGH)               
            vulns_lst = [csp_vuln]                                    
            vulns[CSP_DIRECTIVE_FORM] = vulns_lst  
    # Directive "sandbox"
    if CSP_DIRECTIVE_SANDBOX in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_SANDBOX]
        warn_msg = ""
        vulns_lst = []
        if "allow-*" in directive_values:
            csp_vuln = CSPVulnerability("Directive 'sandbox' apply no restrictions.",
                                        severity.HIGH)            
            vulns_lst.append(csp_vuln)
        if (CSP_DIRECTIVE_VALUE_ALLOW_FORMS in directive_values and
            CSP_DIRECTIVE_VALUE_ALLOW_SAME_ORIGIN in directive_values and
            CSP_DIRECTIVE_VALUE_ALLOW_SCRIPTS in directive_values and
            CSP_DIRECTIVE_VALUE_ALLOW_TOP_NAV in directive_values):
            csp_vuln = CSPVulnerability("Directive 'sandbox' apply no restrictions.",
                                        severity.HIGH)            
            vulns_lst.append(csp_vuln) 
        # Search invalid directive values
        valid_values = []
        valid_values.append("")
        valid_values.append("allow-*")
        valid_values.append(CSP_DIRECTIVE_VALUE_ALLOW_FORMS)
        valid_values.append(CSP_DIRECTIVE_VALUE_ALLOW_SAME_ORIGIN)
        valid_values.append(CSP_DIRECTIVE_VALUE_ALLOW_SCRIPTS)
        valid_values.append(CSP_DIRECTIVE_VALUE_ALLOW_TOP_NAV)
        for value in directive_values:
            if value not in valid_values:
                warn_msg = "Directive 'sandbox' specify invalid value: "\
                "'" + value + "'."
                csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
                vulns_lst.append(csp_vuln)                
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_SANDBOX] = vulns_lst                     
    # Directive "script-nonce"
    if CSP_DIRECTIVE_SCRIPT_NONCE in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_SCRIPT_NONCE]
        warn_msg = ""
        vulns_lst = []        
        # Search invalid directive values
        for nonce in directive_values:            
            if len(nonce.strip()) == 0:
                warn_msg = "Directive 'script-nonce' is defined "\
                           "but nonce is empty."
                csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
                vulns_lst.append(csp_vuln)
            elif nonce.count(",") > 0 or nonce.count(";") > 0:
                warn_msg = "Directive 'script-nonce' is defined "\
                           "but nonce contains invalid character (','|';')."
                csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
                vulns_lst.append(csp_vuln)                                             
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_SCRIPT_NONCE] = vulns_lst                 
    # Directive "plugin-types"
    if CSP_DIRECTIVE_PLUGIN_TYPES in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_PLUGIN_TYPES]
        warn_msg = ""
        vulns_lst = []        
        if "*" in directive_values:
            warn_msg = "Directive 'plugin-types' allows all plugins types."
            csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
            vulns_lst.append(csp_vuln)            
        # Search invalid directive values
        for mtype in directive_values:
            if mtype != "*" and mtype.lower() not in MIME_TYPES:
                warn_msg = "Directive 'plugin-types' specify invalid mime " \
                           "type: '" + mtype + "'."
                csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
                vulns_lst.append(csp_vuln)              
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_PLUGIN_TYPES] = vulns_lst                
    # Directive "reflected-xss"
    if CSP_DIRECTIVE_XSS in policies_all:        
        directive_values = policies_all[CSP_DIRECTIVE_XSS]
        warn_msg = ""
        vulns_lst = []
        if CSP_DIRECTIVE_VALUE_XSS_ALLOW in directive_values:
            warn_msg = "Directive 'reflected-xss' instruct user agent to "\
                       "disable its active protections against reflected XSS."
            csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
            vulns_lst.append(csp_vuln) 
        # Search invalid directive values
        valid_values = []
        valid_values.append(CSP_DIRECTIVE_VALUE_XSS_ALLOW)
        valid_values.append(CSP_DIRECTIVE_VALUE_XSS_BLOCK)
        valid_values.append(CSP_DIRECTIVE_VALUE_XSS_FILTER)
        for value in directive_values:
            if value not in valid_values:
                warn_msg = "Directive 'reflected-xss' specify invalid value: "\
                "'" + value + "'."
                csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
                vulns_lst.append(csp_vuln)
        if len(vulns_lst) > 0:
            vulns[CSP_DIRECTIVE_XSS] = vulns_lst  
    
    # Check if misspelled directives name exists
    if CSP_MISSPELLED_DIRECTIVES in policies_all:        
        directive_values = policies_all[CSP_MISSPELLED_DIRECTIVES]                                                                                      
        warn_msg = "Some directives are misspelled: " + ', '.join(directive_values)
        csp_vuln = CSPVulnerability(warn_msg, severity.HIGH)            
        vulns[CSP_MISSPELLED_DIRECTIVES] = [csp_vuln]
                                 
    return vulns


def unsafe_inline_enabled(response):
    """
    Method to detect if CSP Policies are specified for Script/Style, 
    to allow unsafe inline content to be loaded.
    
    :param response: A HTTPResponse object.
    :return: True if CSP Policies are specified for Script/Style to allow 
             unsafe inline content to be loaded, False otherwise. 
    """
    # Extract and merge all policies
    non_report_only_policies = retrieve_csp_policies(response)
    report_only_policies = retrieve_csp_policies(response, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    # Parse policies dictionary : Iterate on Values
    if len(policies_all) > 0:
        for directive_name in policies_all:
            # Apply check only on Script and Style directives in order to be
            # coherent with the W3C Specs, because only theses 2 directives
            # supports the "unsafe-inline" directive value...
            if (directive_name.lower() != CSP_DIRECTIVE_SCRIPT 
                and directive_name.lower() != CSP_DIRECTIVE_STYLE):
                continue
            # Iterate on Directive values (normally values here are all URI)
            for directive_value in policies_all[directive_name]:               
                if directive_value.strip().lower() == CSP_DIRECTIVE_VALUE_UNSAFE_INLINE:
                    # Return directly to enhance performance...
                    return True
    return False


def unsafe_eval_enabled(response):
    """
    Method to detect if CSP Policies are specified for Script, 
    to allow use of the javascript "eval()" function.
    
    :param response: A HTTPResponse object.
    :return: True if CSP Policies are specified for Script to allow 
             use of the javascript "eval()" function, False otherwise. 
    """
    # Extract and merge all policies
    non_report_only_policies = retrieve_csp_policies(response)
    report_only_policies = retrieve_csp_policies(response, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    # Parse policies dictionary : Iterate on Values
    if len(policies_all) > 0:
        for directive_name in policies_all:
            # Apply check only on Script directive in order to be
            # coherent with the W3C Specs, because only this directive
            # supports the "unsafe-eval" directive value...
            if directive_name.lower() != CSP_DIRECTIVE_SCRIPT:
                continue
            # Iterate on Directive values (normally values here are all URI)
            for directive_value in policies_all[directive_name]:               
                if directive_value.strip().lower() == CSP_DIRECTIVE_VALUE_UNSAFE_EVAL:
                    # Return directly to enhance performance...
                    return True
    return False
    

def provides_csp_features(response):
    """
    Method to detect if url provides CSP features.
    
    :param response: A HTTPResponse object.
    :return: True if the URL provides CSP features, False otherwise. 
    """
    return ((len(retrieve_csp_policies(response)) 
             + len(retrieve_csp_policies(response, True))) > 0)


def retrieve_csp_report_uri(response):
    """
    Method to retrieve all report uri from CSP Policies specified into a HTTP 
    response through CSP headers.
       
    :param response: A HTTPResponse object.      
    :return: A set of URIs
    """ 
    uri_set = set()
    # Extract and all merge policies
    non_report_only_policies = retrieve_csp_policies(response)
    report_only_policies = retrieve_csp_policies(response, True)
    policies_all = merge_policies_dict(non_report_only_policies, report_only_policies)
    # Iterate on Directives
    if len(policies_all) > 0:
        for directive_name in policies_all:
            if directive_name.lower() != CSP_DIRECTIVE_REPORT_URI:
                continue
            # Iterate on Directive values (normally values here are all URI)
            for directive_value in policies_all[directive_name]:               
                uri = directive_value.strip().lower()
                uri_set.add(uri)                       
    return uri_set


def retrieve_csp_policies(response, select_only_reportonly_policies=False,
                          select_also_misspelled_directives=False):
    """
    Method to retrieve all CSP Policies specified into a HTTP response 
    through CSP headers.
       
    :param response: A HTTPResponse object.
    :param select_only_reportonly_policies: Optional parameter to indicate to 
                                            method to retrieve only REPORT-ONLY 
                                            CSP policies (default is False).
    :param select_also_misspelled_directives: Optional parameter to indicate to 
                                            method to retrieve also list of 
                                            misspelled directives name
                                            (default is False). List is saved 
                                            in a dedicated KEY, see global var 
                                            named "CSP_MISSPELLED_DIRECTIVES".       
    :return: A dictionary in which KEY is a CSP directive and VALUE is the 
             list of associated policies.
    """   
    headers = response.get_headers()
    policies = {}
    
    # List of allowed CSP directive names
    directive_allowed_names = [CSP_DIRECTIVE_DEFAULT, CSP_DIRECTIVE_SCRIPT,
                               CSP_DIRECTIVE_OBJECT, CSP_DIRECTIVE_STYLE,
                               CSP_DIRECTIVE_IMAGE, CSP_DIRECTIVE_MEDIA,
                               CSP_DIRECTIVE_FRAME, CSP_DIRECTIVE_FRAME_ANCESTORS,
                               CSP_DIRECTIVE_FONT,
                               CSP_DIRECTIVE_CONNECTION,
                               CSP_DIRECTIVE_REPORT_URI, CSP_DIRECTIVE_FORM,
                               CSP_DIRECTIVE_SANDBOX,
                               CSP_DIRECTIVE_SCRIPT_NONCE,
                               CSP_DIRECTIVE_PLUGIN_TYPES, CSP_DIRECTIVE_XSS]

    # Misspelled directives name list
    misspelled_directives_name = []
         
    for header_name in headers:
        header_name_upperstrip = header_name.upper().strip()
        # Define header processing condition according to
        # "select_only_reportonly_policies" parameter value
        if not select_only_reportonly_policies:
            if (header_name_upperstrip != CSP_HEADER_W3C.upper() 
                and header_name_upperstrip != CSP_HEADER_FIREFOX.upper() 
                and header_name_upperstrip != CSP_HEADER_CHROME.upper() 
                and header_name_upperstrip != CSP_HEADER_IE.upper()):
                continue
        else:
            if header_name_upperstrip != CSP_HEADER_W3C_REPORT_ONLY.upper():
                continue                              
        # Process header value
        # Retrieve the CSP directive list : A Policy is defined by a directive
        # name and one or several associated values
        directive_list = headers[header_name].strip()
        # Parse CSP directives list using W3C Specs algorithm :
        # A CSP header value can specify several directives using ";" separator
        directives = directive_list.split(";")
        # For each directive we extract the directive name and is values
        # (several can be specified)
        for directive in directives:
            directive_strip = directive.strip()
            # Manage empty case
            if len(directive_strip) <= 0:
                continue            
            # Directive name and value are separated by a single space
            # Value can itself contains several sub values separated by a space
            parts = directive_strip.split(" ")            
            # Manage special directives cases
            if (_contains_special_directive(directive_strip) 
                and len(parts) == 1):
                directive_name = parts[0].lower() 
                policies[directive_name] = [""]
                continue                        
            # There must exists at least 2 parts otherwise we ignore the value...
            if len(parts) < 2:
                continue
            # Retrieve directive name
            directive_name = parts[0].lower()
            # Check directive name is in allowed list of directives
            if directive_name not in directive_allowed_names:
                if (select_also_misspelled_directives and
                    directive_name not in misspelled_directives_name):
                    misspelled_directives_name.append(directive_name)
                #Next directive...
                continue
            # Retrieve directive valueS
            parts.pop(0)
            directive_values = parts
            # Add policy to dictionary
            if directive_name not in policies:
                policies[directive_name] = []
            for directive_value in directive_values:
                # Remove quote and double quote from value to unify result
                # string content
                tmp_value = directive_value.replace("'", "")
                tmp_value = tmp_value.replace('"', '')
                # Avoid empty value
                if len(tmp_value.strip()) > 0:             			
                    policies[directive_name].append(tmp_value)
    
    # Do cleanup: Remove directive name without any policies
    policies = dict((k, v) for k, v in policies.iteritems() if len(v) > 0)
    
    # Add misspelled directives names list if dedicated flag is set
    if (select_also_misspelled_directives 
        and len(misspelled_directives_name) > 0):
        policies[CSP_MISSPELLED_DIRECTIVES] = misspelled_directives_name
                    
    return policies


def merge_policies_dict(non_report_only_policies_dict, report_only_policies_dict):
    """
    Method to merge 2 Policies dictionaries to a single.
               
    :param non_report_only_policies_dict: A dictionary with all non 
                                          REPORT-ONLY Policies 
                                          (return of method "retrieve_csp_policies").
    :param report_only_policies_dict: A dictionary with all REPORT-ONLY 
                                      Policies 
                                      (return of method "retrieve_csp_policies")
    :return: A merged dictionary in which KEY is a CSP directive 
             and VALUE is the list of associated policies.
    """
    # Short circuit precheck...
    if(non_report_only_policies_dict is None 
       or len(non_report_only_policies_dict) == 0):
        return report_only_policies_dict
    if(report_only_policies_dict is None 
       or len(report_only_policies_dict) == 0):
        return non_report_only_policies_dict
    
    merged_policies = {}
    # Create a list from union of directives names (remove duplicate items)
    directives_names = list(set(non_report_only_policies_dict.keys() 
                                + report_only_policies_dict.keys()))
    # Parse it to merge list of values for each key (remove duplicate items)
    for k in directives_names:
        values = []
        if k in non_report_only_policies_dict:
            values.extend(non_report_only_policies_dict[k])
        if k in report_only_policies_dict:
            values.extend(report_only_policies_dict[k])
        merged_policies[k] = list(set(values))        
    return merged_policies


def _contains_special_directive(directive_definition):
    """
    Internal method to detect in a directive specification if
    a "special" directive is used.
    
    :param directive_definition: Content of the directive (name + values).
    
    :return: TRUE only if a special directive is detected. 
    """
    # Manage empty cases
    if directive_definition is None:
        return False

    if len(directive_definition.strip()) == 0:
        return False
    
    # List of directives for which empty value is a behavior specification
    special_directive_names = [CSP_DIRECTIVE_SANDBOX,
                               CSP_DIRECTIVE_SCRIPT_NONCE]

    tmp = directive_definition.lower()
    for special_directive in special_directive_names:
        if special_directive in tmp:
            return True
    
    return False
