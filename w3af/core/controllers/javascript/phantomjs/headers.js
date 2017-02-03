/**
  * Copyright 2015, Yahoo Inc. All rights reserved.
  * Use of this source code is governed by a BSD-style
  * license that can be found in the LICENSE file.
  *
  
*/

exports.init = function(phantom, page){

	function setReqHeaders(headers, cookieHostname){
		phantom.clearCookies();
		// console.log("DEBUG HEADERS... " + cookieHostname)

	  	// for(var i in headers) {
		  // 	console.log("headers " + i)
		  // 	console.log(headers[i])
  		// }


		if (!headers || typeof(headers) != 'object') return {};

		// avoid requesting for gzipped/compressed content, i.e., Accept-Encoding and Accept request headers unconfigurable
		// gzip decompression is problematic: https://github.com/ariya/phantomjs/issues/10930
		// the following headers modification is moved to phantomjs.py
		// headers['Accept-Encoding'] = "identity";
		// delete headers['Accept'];

		// make cookies available for subresources requests of the same hostname, otherwise, only the main page will receive cookie
		if (headers['Cookie']) {
			headers['Cookie'].split(';').forEach(function(cookie){
				var eqIndex = cookie.indexOf('=');
				phantom.addCookie({
					name: cookie.substr(0, eqIndex).trim(), 
					value: cookie.substr(eqIndex + 1).trim(),
					domain: cookieHostname, // already defaulted to hostname of current page
					path: '/', httponly: true, secure: false
				});
			});
			delete headers['Cookie'];
		}


		// User-Agent in request header must be explicitly configured thru settings.userAgent
		Object.keys(headers).forEach(function(headerName){
			if (headerName.toLowerCase() == 'user-agent') {
				page.settings.userAgent = headers[headerName];
				delete headers[headerName];
			}
		});

		return headers;
	}


	function getRespHeaders(headers) {
		var out = {};
		headers && headers.forEach(function(h){
			// the following headers are stripped to prevent decoding twice by scrapy
			var name = h.name.toLowerCase(), value = h.value.toLowerCase();
			if ((name == 'content-encoding' && ['gzip','deflate'].indexOf(value) != -1)
				|| (name == 'transfer-encoding' && value == 'chunked'))
				return;

			name = h.name;
			out[name] = out[name] || [];
			out[name].push(h.value);
		});
		return out;
	}


	return {
		'setReqHeaders': setReqHeaders,
		'getRespHeaders': getRespHeaders
	};
}