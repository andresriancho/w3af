# -*- coding: utf8 -*-
"""
ajax_export.py

Copyright 2009 Andres Riancho

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
from w3af.core.data.parsers.doc.http_request_parser import http_request_parser


def ajax_escape_string(str_in):
    str_out = str_in.replace('"', '\\"')
    return str_out


def ajax_export(request_string):
    """
    :param request_string: The string of the request to export
    :return: A javascript that will perform the same HTTP request.
    """
    # get the header and the body
    splitted_request = request_string.split('\n\n')
    header = splitted_request[0]
    body = '\n\n'.join(splitted_request[1:])

    http_request = http_request_parser(header, body)

    # Now I do the real magic...
    # This is the header, to include the AJAX stuff:
    res = """/* Init AJAX stuff */

var xmlhttp = false;
/*@cc_on @*/
/*@if (@_jscript_version >= 5)
// JScript gives us Conditional compilation, we can cope with old IE versions.
// and security blocked creation of the objects.
try {
    xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
} catch (e) {
    try {
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    } catch (E) {
        xmlhttp = false;
    }
}
@end @*/

if (!xmlhttp && typeof XMLHttpRequest != 'undefined') {
    try {
        xmlhttp = new XMLHttpRequest();
    } catch (e) {
        xmlhttp = false;
    }
}
if (!xmlhttp && window.createRequest) {
    try {
        xmlhttp = window.createRequest();
    } catch (e) {
        xmlhttp = false;
    }
}
/* Finished AJAX initialization */

/* Create the request, please remember the same-origin policy, which might
affect how and if this request is sent by the browser */
"""

    # Set the method and the path
    res += 'xmlhttp.open("' + http_request.get_method() + '", "'
    res += ajax_escape_string(
        http_request.get_uri().url_string) + '", true);\n'

    # For debugging
    res += """
/* Debugging code, this should be removed for real life XSS exploits */
xmlhttp.onreadystatechange = function() {
    if (xmlhttp.readyState == 4 ) {
        alert(xmlhttp.responseText);
    }
}


/* Add headers to the request and send it, please note that custom headers
might be removed by the browser and/or generate an exception that will
make the request fail */
"""

    # Now I add the headers:
    headers = http_request.get_headers()
    for header_name, header_value in headers.iteritems():
        res += 'xmlhttp.setRequestHeaders("' + ajax_escape_string(
            header_name) + '", "'
        res += ajax_escape_string(header_value) + '");\n'

    # And finally the post data (if any)
    if http_request.get_data() and http_request.get_data() != '\n':
        res += 'var post_data = (<r><![CDATA[' + str(
            http_request.get_data()) + ']]></r>).toString();\n'
        res += 'xmlhttp.send(post_data);\n'
    else:
        res += 'xmlhttp.send(null);\n'

    return res
