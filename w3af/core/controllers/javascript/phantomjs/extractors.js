/**
  * Copyright 2015, Yahoo Inc. All rights reserved.
  * Use of this source code is governed by a BSD-style
  * license that can be found in the LICENSE file.
  *
  
*/

// to call back phantom
function phantomCallback(action, data) {
    if (window.callPhantom) {
        data = data || {};
        data.action = action;
        window.callPhantom(data);
    }
}

// timer as a reason to wait
var _gryffin_setTimeout = window.setTimeout, _gryffin_setInterval = window.setInterval;
window.setTimeout = function(f, t){return phantomCallback('waitTimer', {timeout:t}) || _gryffin_setTimeout.call(this, f, t)};
window.setInterval = function(f, t){return phantomCallback('waitTimer', {timeout:t}) || _gryffin_setInterval.call(this, f, t)};


// Derived from casperjs
function triggerMouseEvent(el, type) {

    try {
        var evt = document.createEvent("MouseEvents"), center_x = 1, center_y = 1;
        try {
            var pos = el.getBoundingClientRect();
            center_x = Math.floor((pos.left + pos.right) / 2);
            center_y = Math.floor((pos.top + pos.bottom) / 2);
        } catch(e) {}
        evt.initMouseEvent(type, true, true, window, 1, 1, 1, center_x, center_y, false, false, false, false, 0, el);
        // dispatchEvent return value is false if at least one of the event
        // handlers which handled this event called preventDefault;
        // so we cannot returns this results as it cannot accurately informs on the status
        // of the operation
        // let's assume the event has been sent ok it didn't raise any error
        el.dispatchEvent(evt);
        return true;
    } catch (e) {
        return false;
    }
};

// function getElementByXPath(expression) {
//     var a = document.evaluate(expression, document.body, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
//     if (a.snapshotLength > 0) {
//         return a.snapshotItem(0);
//     }
// };

// other candidates: focus, input, keydown, keypress, keyup, blur
var jsLinks, jsLinkEvents = ['click', 'dblclick', 'change', 'submit', 'scroll', 'mousemove', 'mouseover', 'mousedown', 'mouseup', 'mouseout'],
    attributeFilter = ['href', 'action'].concat(jsLinkEvents.map(function(x){return 'on' + x})),
    re_js_links = /^javascript:/i, 
    re_urls = /^(?:https?|ftp):\/\//i,
    re_absoluteUrls = /(?:https?|ftp):\/\/[^\s]+/ig,
    re_relativeUrls = /[^\s]+\.(?:php[s\d]?|s?html?|aspx?|jsp|cfm)[^\s]*/ig;

jsLinks = (function(){

    function getxpath(el) {
        if (el===document.body) return 'body';
        if (el.id !== '') return "//*[@id='"+el.id+"']";
        if (!el.parentNode) return el.toString();

        for (var i = 0, s, cnt = 0, p = el.parentNode, siblings = p.childNodes; s = siblings[i]; i++) {
            if (s === el) return [getxpath(p), el.tagName.toLowerCase() + '[' + (cnt + 1) + ']'].join('/');
            if (s.nodeType === 1 && s.tagName === el.tagName) cnt++;
        }
    };

    var jsLinkCaptured = {'root':{'jsLinks':[],'trigger':function(){},'parent':null,'arrPtr':0,'key':'root'}}, 
        triggeringElement = jsLinkCaptured['root'],
        elementProto = (window.EventTarget? window.EventTarget : window.HTMLElement ? window.HTMLElement : window.Element).prototype,
        elementProtoMethods = {'addEventListener': elementProto.addEventListener};

    // extract DOM Level 0 events
    function extractDOM0Events(el) {
        el = el || document.body;
        function getJsLink(element) {
            jsLinkEvents.forEach(function(evt){
                element['on' + evt] && jsLinks.add(evt, element, 'dom0');
            });
        }
        getJsLink(el);
        [].forEach.call(el.getElementsByTagName('*'), getJsLink);
    }

    // extract DOM Level 2 events
    elementProto.addEventListener = function(type, fn, capture) {
        if (jsLinkEvents.indexOf(type.toLowerCase()) !== -1)
            jsLinks.add(type, this, 'addEventListener');
        return elementProtoMethods.addEventListener.call(this, type, fn, capture);
    };

    return {
        add: function(eventType, node, triggerSource) {
            eventType = eventType.toLowerCase();
            var key = getxpath(node);

            if (jsLinkCaptured[key]) {
                if (jsLinkCaptured[key]['events'].indexOf(eventType) === -1)
                    jsLinkCaptured[key]['events'].push(eventType);
                jsLinkCaptured[key]['src'].push(triggerSource);
            } else {
                jsLinkCaptured[key] = {
                    'key': key,
                    'keyChain': function() {
                        var trace = [], element = this;
                        do {
                            trace.push(element.key);
                        } while (element = element.parent);
                        return trace.reverse();
                    },
                    'events': [eventType],
                    'trigger': function(onTriggered, delay){
                        var self = this, i = 0,
                                eventsString = self.events.join('|'),
                                results = {'keyChain':self.keyChain(), 'events': self.events};
                        
                        if (node) {
                            phantomCallback('element.triggering', results);

                            // simulate scroll event
                            if (self.events.indexOf('scroll') !== -1)
                                _gryffin_setTimeout.call(window, function(){
                                    try {node.scrollTop = node.scrollHeight} catch(e) {}
                                }, i++ * delay);

                            // group all mouse and (dbl)click events as follows
                            if (/(?:click|mouse|change)/.test(eventsString)) {
                                _gryffin_setTimeout.call(window, function(){
                                    try {node.focus()} catch(e) {};
                                    triggerMouseEvent(node, 'mousemove');
                                    triggerMouseEvent(node, 'mouseenter');
                                    triggerMouseEvent(node, 'mouseover');
                                    triggerMouseEvent(node, 'mousemove');
                                    triggerMouseEvent(node, 'mousedown')
                                    triggerMouseEvent(node, 'mouseup');
                                }, i * delay);
                                if (self.events.indexOf('click') !== -1) 
                                    _gryffin_setTimeout.call(window, function(){
                                        triggerMouseEvent(node, 'click');
                                    }, i++ * delay);
                                if (self.events.indexOf('dblclick') !== -1) 
                                    _gryffin_setTimeout.call(window, function(){
                                        triggerMouseEvent(node, 'dblclick');
                                    }, i++ * delay);
                                if (self.events.indexOf('change') !== -1) {
                                    // for select element
                                    if (node.options)
                                        for (var j = 0, len = node.options.length; j < len; j++)
                                            // cycle through every option
                                            _gryffin_setTimeout.call(window, function(){
                                                node.selectedIndex = (node.selectedIndex + 1) % node.options.length;
                                                node.dispatchEvent(new Event('change', {bubbles: true, cancelable: true}));
                                            }, i++ * delay);
                                    // for other elements
                                    else
                                        _gryffin_setTimeout.call(window, function(){
                                            node.dispatchEvent(new Event("change", {bubbles: true, cancelable: true}));
                                        }, i++ * delay);
                                }
                                _gryffin_setTimeout.call(window, function(){
                                    triggerMouseEvent(node, 'mouseout');
                                    triggerMouseEvent(node, 'mouseleave');
                                }, i++ * delay);
                            }

                            // simulate submit event
                            if (self.events.indexOf('submit') !== -1)
                                _gryffin_setTimeout.call(window, function(){
                                    node.dispatchEvent(new Event("submit", {bubbles: true, cancelable: true}));
                                    // dynamically evaluate jsurl of node.action
                                    // TODO: url resolved, enumerate multi-valued form elements?
                                    if (re_js_links.test(node.action))
                                        (function(){eval(this.action.substring(11));this.submit()}).call(node);
                                    else
                                        node.submit();
                                }, i++ * delay);
                        
                            // append discovered links/forms
                            _gryffin_setTimeout.call(window, function(){
                                phantomCallback('element.triggered', results);
                            }, i * delay);
                        }

                        jsLinks.getData = function() {
                            // append discovered links/forms
                            if (self.links.length)
                                results.links = self.links;
                            if (self.forms.length)
                                results.forms = self.forms;

                            // trigger next element's events
                            onTriggered && _gryffin_setTimeout.call(window, onTriggered, 10);
                            return results;
                        };
                    },
                    'jsLinks': [],
                    'arrPtr': 0,
                    'parent': triggeringElement,
                    'src': [triggerSource],
                    'links': [],
                    'forms': []
                };
                triggeringElement.jsLinks.push(jsLinkCaptured[key]);
            }
        },
        depthFirstTrigger: function(element, delay){
            triggeringElement = element;
            triggeringElement.trigger(function() {
                var nextElement, parentTriggerElement = triggeringElement.parent;
                parentTriggerElement.arrPtr++;

                // depth-first approach: go one depth deeper if available
                // no more child, execute the immediate sibling
                // no more immediate sibling, execute the parent's sibling
                nextElement = triggeringElement.jsLinks[0] 
                        || parentTriggerElement.jsLinks[parentTriggerElement.arrPtr]
                        || (parentTriggerElement.parent && parentTriggerElement.parent.jsLinks[parentTriggerElement.parent.arrPtr]);

                if (nextElement)
                    jsLinks.depthFirstTrigger(nextElement, delay);
                else
                    phantomCallback('done');

            }, delay);
        },
        triggerAll: function(delay) {
            observeDOMChanges(function(newNode){
                extractDOM0Events(newNode);
                // append the newly discovered static links and forms
                extractRequests(triggeringElement, newNode);
            });

            // extract jsLinks
            extractDOM0Events();

            if (triggeringElement.jsLinks[0])
                jsLinks.depthFirstTrigger(triggeringElement.jsLinks[0], delay);
            else
                phantomCallback('done');
        }
    };
})();


function observeDOMChanges(onNewNode) {
    // create an observer instance
    var observer = new window.MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            onNewNode && [].forEach.call(mutation.addedNodes || [mutations.target], function(node){
                node && (node.nodeType === 1) && onNewNode.call(this, node, observer);
            });
        });
    });

    // monitor new nodes and attribute changes that involve URLs
    observer.observe(document.body, {
        subtree: true, 
        childList: true, 
        attributes: true, 
        attributeFilter: attributeFilter
    });

    return observer;
}

function arrayUnique(arr) {
    var result = [], i = 0, key, lastKey, sorted = arr.sort(), len = sorted.length;
    for (;key = sorted[i];i++)
        if (lastKey !== key)
            result.push(lastKey = key);
    return result;
}


function extractRequests(sink, el) {
    sink.links = sink.links || [];
    sink.forms = sink.forms || [];
    el = el || document.body;
    var links = sink.links, forms = sink.forms;
    
    function getLink(a) {
        if (a.hasAttribute('href') || a.href) {
            var href = a.href;
            if (re_js_links.test(href))
                jsLinks.add('click', a, 'jsurl');
            else if (re_urls.test(href))
                links.push({'url':href, 'text':(a.textContent || a.innerText).replace(/\s+/g, ' ').trim()});
        }
    }

    // TODO: ajax forms extractions
    function getForm(f) {
        var method = f.method ? f.method.toLowerCase() : 'get',
            url = f.action,
            urlparams = [], a,
            values = [], submits = [], multiDefaults = {}, dataType = {}, j = 0, input;

        // for javascript-uri submissions, yielding FormRequest with invalid url is meaningless
        if (re_js_links.test(url) || typeof url === 'object') {
            jsLinks.add('submit', f, 'jsurl');
            return;
        }

        for (; input = f.elements[j]; j++) {
            var name = encodeURIComponent(input.name), 
                value = encodeURIComponent(input.value),
                nodeName = input.nodeName.toLowerCase(), 
                type = input.type ? input.type.toLowerCase() : nodeName;

            if (!name) continue;

            // <input type=submit|image>, <button type=submit|image>
            if (['input','button'].indexOf(nodeName) !== -1 && ['submit','image'].indexOf(type) !== -1) {
                submits.push([[name, value].join('=')]);

            // <input type!=reset|button>, <textarea>, <keygen> element
            } else if ((nodeName === 'input' && ['reset','button'].indexOf(type) === -1)
                    || ['textarea','keygen'].indexOf(nodeName) !== -1) {
                
                if (typeof(f[name].length) === 'undefined') // an unique element with such a 'name'
                    values.push([name, value].join('='));
                else if (!dataType[name]) // i.e., radio/checkbox, and the first time being recorded
                    multiDefaults[name] = [].map.call(f[name], function(opt){return [name, encodeURIComponent(opt.value)].join('=')});

            // <select> element
            } else if (nodeName === 'select') {
                
                if (input.options.length)
                    multiDefaults[name] = [].map.call(f[name], function(opt){return [name, encodeURIComponent(opt.value)].join('=')});
                else
                    values.push(name + '=');
            }

            // TODO: if no default value, supply one depending on type? (e.g., email)
            dataType[name] = type;
        }

        // for unknown/empty urls
        if (!re_urls.test(url))
            url = window.location.href;

        a = document.createElement('a');
        a.href = url;
        // process any parameters given as part of the url
        if (a.search.length > 1) {
            // url's params will be later combined with those collected in form, and used for deduplication
            urlparams = a.search.substring(1).split('&');

            // url's params are considered of hidden types
            urlparams.forEach(function(param){
                if (param = param.split('=')[0])
                    dataType[param] = 'hidden';
            });

            // for GET method, transfer url's params to values for deduplication
            if (method === 'get') {
                values = urlparams.concat(values);
                a.search = '';
                url = a.href;
            }
        }

        // in case no name for submit button, simply let other values be serialized
        if (submits.length === 0)
            submits.push([]);

        // enumerate all possibilities for every multiDefaults, with submits as default
        // Example: 
        //  - submits = [['submit=save'], ['submit=send']]
        //  - multiDefaults = {'sex':['sex=M', 'sex=F'], 'relationship': ['relationship=complicated', 'relationship=single', 'relationship=married']}
        // results: [
        //         ["submit=save", "sex=M", "relationship=complicated"],
        //         ["submit=save", "sex=M", "relationship=single"],
        //         ["submit=save", "sex=M", "relationship=married"],
        //         ["submit=save", "sex=F", "relationship=complicated"],
        //         ["submit=save", "sex=F", "relationship=single"],
        //         ["submit=save", "sex=F", "relationship=married"],
        //         ["submit=send", "sex=M", "relationship=complicated"],
        //         ["submit=send", "sex=M", "relationship=single"],
        //         ["submit=send", "sex=M", "relationship=married"],
        //         ["submit=send", "sex=F", "relationship=complicated"],
        //         ["submit=send", "sex=F", "relationship=single"],
        //         ["submit=send", "sex=F", "relationship=married"]
        // ]
        multiDefaults = Object.keys(multiDefaults).reduce(function(previousValues, currentKey){
            var currentValues = multiDefaults[currentKey];
            return previousValues.map(function(previousValue){
                return currentValues.map(function(currentValue){return previousValue.concat(currentValue)});
            }).reduce(function(a, b){return a.concat(b)});
        }, submits);

        // each submit button can correspond to a different name/value pair to submit
        // then, concat all params collected, de-duplicate tuples of "[key]=[value]", finally join with &
        multiDefaults.forEach(function(combinator){
            forms.push({
                method: method,
                url: url,
                data: arrayUnique(values.concat(combinator)).join('&'),
                dataType: dataType
            });
        });
    }

    function getCommentedLinks(comment) {
        var commentedLinks;
        // for absolute URLs 
        if (commentedLinks = comment.match(re_absoluteUrls))
            commentedLinks.forEach(function(url){links.push({'url':url, 'text':'__comments'})});

        // for relative URLs - to avoid false positives, must ends with extensions known to give html
        if (commentedLinks = comment.match(re_relativeUrls)) {
            var a = document.createElement('a');
            commentedLinks.forEach(function(url){
                if (!re_urls.test(url)) {
                    a.href = url;
                    links.push({'url': a.href, 'text':'__comments'})
                }
            });
        }
    }


    // the el itself could be a link
    getLink(el);
    // links extraction from a/area tags
    [].forEach.call(el.getElementsByTagName('a'), getLink);
    [].forEach.call(el.getElementsByTagName('area'), getLink)


    // the el itself could be a form
    if (el.tagName.toLowerCase() == 'form')
        getForm(el);
    // forms extraction
    [].forEach.call(el.getElementsByTagName('form'), getForm);
}

window._gryffin_onMainFrameReady = function() {
    // a page may have no document.body
    if (!document.body) 
        return {};

    var results = {
        'jsLinkFeedback': true     // always true now because we now hardcoded (at least) the scroll event 
    };
    extractRequests(results);

    jsLinks.add('scroll', document.body, 'hardcoded');
    jsLinks.triggerAll(250);

    return results;
}

