/**
  * Copyright 2015, Yahoo Inc. All rights reserved.
  * Use of this source code is governed by a BSD-style
  * license that can be found in the LICENSE file.
  *
  
*/

var re_hostname = /^(?:https?|ftp):\/\/([^:\/\?]+)/i,
	re_extensionFilter = /\.(?:css|pdf|svg|ttf|zip|tar|gz|pkg|exe)(?:[\?#;][^\?#;]*)?$/i,
	re_jsAnalyticsFilter = /^https?:\/\/(?:\w+\.)?yimg\.com\/mi(?:\/[^\/]+)?\/ywa\.js$/i,
	re_whitelistedRedirectionDomains = /(?:yahoo\.com?(?:\.\w\w)?|yimg\.com|flickr\.com|y-cloud\.net|yahoodns\.net|yahoofs\.com|zenfs\.com)$/;

exports.getHostname = function(url) {
	url = url.match(re_hostname);
	return url ? url[1] : null;
}
exports.invalidUrl = function(url, allowedDomains) {
	url = exports.getHostname(url);
	return (url === null || (allowedDomains && allowedDomains.indexOf(url) === -1));
}
exports.blacklistedUrl = function(url) {
	return re_extensionFilter.test(url) || re_jsAnalyticsFilter.test(url);
}
exports.whitelistedRedirectionDomains = function(url) {
	return re_whitelistedRedirectionDomains.test(exports.getHostname(url));
}

exports.cleanResponseBody = function(body) {
	return (body == '<html><head></head><body></body></html>') ? '' : body;
}

// to repackage headers as a dict format, as required by scrappy
exports.prepareResponse = function(response, headersFilter) {
	return {
		headers: headersFilter(response.headers),
		contentType: response.contentType,
		status: response.status,
		url: response.url
	}
}

// TODO: add to redis
exports.pageChanges = (function() {
	var changes = {};
	return {
		fetch: function(eventName) {
			var ret = changes[eventName] || [];
			changes[eventName] = [];
			return ret;
		},
		fetchAll: function() {
			var ret = changes;
			changes = {};
			return ret;
		},
		push: function(eventName, obj) {
			changes[eventName] = changes[eventName] || [];
			changes[eventName].push(obj);
		}
	}
})();

var JSONSignature = '==lXlKfYWch7H9VdJgPCmJ==';

exports.printJSON = function(type, output) {
	output['msgType'] = type;
	output['signature'] = JSONSignature;
	console.log(JSON.stringify(output));
	// console.log(['{'+type, JSON.stringify(output), type+'}'].join(JSONSignature));
}