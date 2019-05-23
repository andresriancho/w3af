/**
 *   Copyright 2018 Andres Riancho
 *
 *   This file is part of w3af, http://w3af.org/ .
 *
 *    w3af is free software; you can redistribute it and/or modify
 *    it under the terms of the GNU General Public License as published by
 *    the Free Software Foundation version 2 of the License.
 *
 *    w3af is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    GNU General Public License for more details.
 *
 *    You should have received a copy of the GNU General Public License
 *    along with w3af; if not, write to the Free Software
 *    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

var _DOMAnalyzer = _DOMAnalyzer || {
    /**
     *   Browser-side code that overrides addEventListener and setTimeout to store
     *   them and help the crawling process.
     */

    // Only initialize the analyzer once
    initialized: false,

    // Store timeouts and intervals
    set_timeouts: [],
    set_intervals: [],
    event_listeners: [],

    universally_valid_events: [
        "click",
        "dblclick",
        "mousedown",
        "mousemove",
        "mouseout",
        "mouseover",
        "mouseup"
    ],

    elements_allowed_to_inherit_events_from_ancestors: [
        "a",
        "div",
        "input",
        "textarea",
        "select",
        "form",
        "li",
        "span",
        "button"
    ],

    valid_events_per_element: {
        "body" : [
            "load"
        ],
        "button" : [
            "focus",
            "blur"
        ],
        "form" : [
            "submit",
            "reset"
        ],
        "input" : [
            "select",
            "change",
            "focus",
            "blur",
            "keydown",
            "keypress",
            "keyup",
            "input"
        ],
        "label" : [
            "focus",
            "blur"
        ],
        "textarea" : [
            "select",
            "change",
            "focus",
            "blur",
            "keydown",
            "keypress",
            "keyup",
            "input"
        ],
        "select" : [
            "change",
            "focus",
            "blur"
        ]
    },

    // window and document nodes allow only some events
    window_and_document_valid_events: [
        'blur',
        'change',
        'click',
        'dblclick',
        'focus',
        'input',
        'keydown',
        'keypress',
        'keyup',
        'load',
        'mousedown',
        'mousemove',
        'mouseout',
        'mouseover',
        'mouseup',
        'reset',
        'select',
        'submit'
    ],

    initialize: function () {
        if(_DOMAnalyzer.initialized) return;

        _DOMAnalyzer.initialized = true;

        _DOMAnalyzer.override_addEventListener();
        _DOMAnalyzer.override_setTimeout();
        _DOMAnalyzer.override_setInterval();
    },

    // Override window.setTimeout()
    override_setTimeout: function () {
        let original_setTimeout = window.setTimeout;

        window.setTimeout = function() {

            let function_ = arguments[0];
            let timeout = arguments[1];

            _DOMAnalyzer.set_timeouts.push({"function": function_,
                                            "timeout": timeout});
            original_setTimeout.apply(this, arguments);
        };
    },

    // Override window.setInterval()
    override_setInterval: function () {
        let original_setInterval = window.setInterval;

        window.setInterval = function() {

            let function_ = arguments[0];
            let timeout = arguments[1];

            _DOMAnalyzer.set_intervals.push({"function": function_,
                                             "timeout": timeout});
            original_setInterval.apply(this, arguments);
        };
    },

    /**
     * Override (window|document).addEventListener and Node.prototype.addEventListener
     *
     * https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
     */
    override_addEventListener: function () {
        // Override window.addEventListener
        let original_window_addEventListener = window.addEventListener;

        window.addEventListener = function (type, listener, useCapture) {
            _DOMAnalyzer.storeEventListenerData(window, type, listener, useCapture);
            original_window_addEventListener.apply(window, Array.prototype.slice.call(arguments));
        };

        // Override document.addEventListener
        let original_document_addEventListener = document.addEventListener;

        document.addEventListener = function (type, listener, useCapture) {
            _DOMAnalyzer.storeEventListenerData(document, type, listener, useCapture);
            original_document_addEventListener.apply(document, Array.prototype.slice.call(arguments));
        };

        //
        // Override Node.prototype.addEventListener, this allows us to intercept
        // calls to addEventListener when invoked without window or document object,
        // for example:
        //
        // var el = document.getElementById("outside");
        // el.addEventListener("click", modifyText, false);
        //
        let original_node_addEventListener = Node.prototype.addEventListener;

        Node.prototype.addEventListener = function (type, listener, useCapture) {
            _DOMAnalyzer.storeEventListenerData(this, type, listener, useCapture);
            original_node_addEventListener.apply(this, Array.prototype.slice.call(arguments));
        };

    },

    /**
     * Store event listener data
     *
     * The method handles two very different scenarios:
     *
     *      - element is window / document
     *
     *      - element is any other node
     *
     * window and document instances don't have tagName nor selector, and will
     * never return `false` for _DOMAnalyzer.elementIsHidden(element), thus
     * handling is completely different.
     *
     * @param element          element           window, document, node
     * @param type             string            The event type, eg. click
     * @param listener         function          The function that handles the event
     * @param useCapture       boolean           As defined in the addEventListener docs
     *
     * https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
     *
     */
    storeEventListenerData: function (element, type, listener, useCapture) {
        if (element.tagName){
            // Handle regular elements
            return _DOMAnalyzer.storeEventListenerDataForElement(element, type, listener, useCapture);
        } else {
            // Handle window or document
            return _DOMAnalyzer.storeEventListenerDataForWindowDocument(element, type, listener, useCapture);
        }
    },

    /**
     * See docs in storeEventListenerData()
     *
     * @param element          element           window, document, node
     * @param type             string            The event type, eg. click
     * @param listener         function          The function that handles the event
     * @param useCapture       boolean           As defined in the addEventListener docs
     * @returns {boolean}
     */
    storeEventListenerDataForWindowDocument: function (element, type, listener, useCapture) {
        if( !_DOMAnalyzer.eventIsValidForWindowDocument( type ) ) return false;

        let tag_name;
        let selector;
        let node_type;

        // TODO: This is a hack. I found not better way to create a "selector"
        //       or "tag_name" to represent the window and document instances
        //       without overlapping with real tags that are names the same.
        //
        //       If you're reading this and know a better way to do it, I would
        //       love to hear about it
        if (element === window){
            tag_name = "!window";
            selector = "!window";
            node_type = -1;
        } else {
            tag_name = "!document";
            selector = "!document";
            node_type = element.nodeType;
        }

        // node_type is https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType#Node_type_constants
        _DOMAnalyzer.event_listeners.push({"tag_name": tag_name,
                                           "node_type": node_type,
                                           "selector": selector,
                                           "event_type": type,
                                           "use_capture": useCapture});
    },

    /**
     * See docs in storeEventListenerData()
     *
     * @param element          element           window, document, node
     * @param type             string            The event type, eg. click
     * @param listener         function          The function that handles the event
     * @param useCapture       boolean           As defined in the addEventListener docs
     * @returns {boolean}
     */
    storeEventListenerDataForElement: function (element, type, listener, useCapture) {
        // The element might be hidden from the user's view
        if (_DOMAnalyzer.elementIsHidden(element)) return false;

        let tag_name = element.tagName.toLowerCase();

        if( !_DOMAnalyzer.eventIsValidForTagName( tag_name, type ) ) return false;

        let selector = OptimalSelect.select(element);

        // node_type is https://developer.mozilla.org/en-US/docs/Web/API/Node/nodeType#Node_type_constants
        _DOMAnalyzer.event_listeners.push({"tag_name": tag_name,
                                           "node_type": element.nodeType,
                                           "selector": selector,
                                           "event_type": type,
                                           "use_capture": useCapture,
                                           "text_content": _DOMAnalyzer.superTrim(element.textContent)});
    },

    /**
     * Get the element, window or document from the selector.
     *
     * Note that the selector parameter is a regular CSS selector BUT:
     *
     *   - When the window object should be returned !window is used
     *   - When the document object should be returned !document is used
     *
     * @param selector          string           CSS selector (with extras)
     */
    getObjectFromSelectorPlus: function (selector) {

        if (selector === "!window"){
            return window
        }

        if (selector === "!document") {
            return document;
        }

        let element = document.querySelector(selector);

        // The element might be hidden from the user's view
        if (_DOMAnalyzer.elementIsHidden(element)) return null;

        return element;
    },

    /**
     * Dispatch an event
     *
     * https://developer.mozilla.org/en-US/docs/Web/API/Document/createEvent
     * https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent
     */
    dispatchCustomEvent: function (selector, event_type) {

        let element = _DOMAnalyzer.getObjectFromSelectorPlus(selector);

        // The element might not exist anymore or be hidden from the user's view
        if (element == null) return false;

        let event = document.createEvent("Events");
        event.initEvent(event_type, true, true);
        event.altKey   = false;
        event.shiftKey = false;
        event.ctrlKey  = false;
        event.metaKey  = false;
        event.view     = window;

        element.dispatchEvent(event);

        return true;
    },

    /**
     * Element is hidden
     *
     */
    elementIsHidden: function(element) {
        // The element might have been removed from the DOM
        if( !element ) return true;

        // The element is not in the user's view
        if( element.offsetWidth <= 0 && element.offsetHeight <= 0 ) return true;

        return false;
    },


    /**
     * Not all events are valid for all elements. This function returns
     * true when the event is valid for the element.
     *
     * Important note!
     *
     *      This function is filtering lots of potentially invalid events
     *      that the browser might (or not) handle.
     *
     *      Events that do not pass this filter will be ignored in the rest
     *      of the process, so keep an eye on universally_valid_events and
     *      valid_events_per_element when testing and debugging.
     */
    eventIsValidForTagName: function (tag_name, attr_name) {
        if (_DOMAnalyzer.universally_valid_events.includes(attr_name)) return true;

        if (!_DOMAnalyzer.valid_events_per_element.hasOwnProperty(tag_name)) return false;

        return _DOMAnalyzer.valid_events_per_element[tag_name].includes(attr_name);
    },

     /**
     * Not all events are valid for `window` and `document`. This function returns
     * true when the event is valid for the element.
     *
     * Important note!
     *
     *      This function is filtering lots of potentially invalid events
     *      that the browser might (or not) handle.
     *
     *      Events that do not pass this filter will be ignored in the rest
     *      of the process!
     */
    eventIsValidForWindowDocument: function ( event_type ) {
        return _DOMAnalyzer.window_and_document_valid_events.includes(event_type);
    },

    /**
     * Extract the events and handlers from the element attributes and properties
     *
     * This function extracts event listeners from attributes:
     *
     *      <div onclick="x()">...</div>
     *
     * And properties:
     *
     *      var el = document.getElementById("selector");
     *      el.onclick = someFunction;
     *
     */
    extractEventsFromAttributesAndProperties: function (tag_name, element) {
        let events = [];
        let event_types = [];
        let selector = null;

        //
        //  First extract from attributes
        //
        let attributes  = element.attributes;
        let attr_length = attributes.length;

        for( let attr_it = 0; attr_it < attr_length; attr_it++ ){
            let attr_name = attributes[attr_it].nodeName;

            // Remove the 'on' from 'onclick'. This will also remove the first
            // two chars from any attribute name, but it will simply not pass
            // the eventIsValidForTagName filter below
            attr_name = attr_name.substr(2);

            if( !_DOMAnalyzer.eventIsValidForTagName( tag_name, attr_name ) ) continue;

            if( selector === null) { selector = OptimalSelect.select(element) }

            let edata = {
                "tag_name": tag_name,
                "node_type": element.nodeType,
                "selector": selector,
                "event_type": attr_name,
                "handler": attributes[attr_it].nodeValue,
                "text_content": _DOMAnalyzer.superTrim(element.textContent)
            };

            events.push(edata);
            event_types.push(attr_name);
        }

        //
        //  And then from properties
        //
        for( let property_name in element ) {

            //
            // PyCharm SCA recommends you add this check, and highlights all
            // usages of `property_name` with a warning unless you do.
            //
            // Adding this check will break test_onclick_event_set_attribute()
            // because hasOwnProperty() only returns `true` when the property
            // is in the class, not in a parent.
            //
            // if ( !element.hasOwnProperty(property_name) ) continue;
            //
            // noinspection JSUnfilteredForInLoop
            let property_value = element[property_name];

            if ( !property_value ) continue;

            // Remove the 'on' from 'onclick'. This will also remove the first
            // two chars from any attribute name, but it will simply not pass
            // the eventIsValidForTagName filter below
            //
            // noinspection JSUnfilteredForInLoop
            property_name = property_name.substr(2);

            // Prevent duplicates in some rare scenarios
            //
            // noinspection JSUnfilteredForInLoop
            if ( event_types.includes(property_name) ) continue;

            // Make sure that the event type is valid
            //
            // noinspection JSUnfilteredForInLoop
            if ( !_DOMAnalyzer.eventIsValidForTagName( tag_name, property_name ) ) continue;

            if( selector === null) { selector = OptimalSelect.select(element) }

            // noinspection JSUnfilteredForInLoop
            let edata = {
                "tag_name": tag_name,
                "node_type": element.nodeType,
                "selector": selector,
                "event_type": property_name,
                "handler": property_value,
                "text_content": _DOMAnalyzer.superTrim(element.textContent)
            };

            events.push(edata)
        }

        return events;
    },

    /**
     * Removes all new lines, tabs and spaces from the string.
     *
     * @param  {String}   string_to_trim     The string to super-trim
     * @return {String}                      String without new lines nor spaces
     *
     */
    superTrim: function ( string_to_trim ) {
        string_to_trim = string_to_trim.trim();
        return string_to_trim.replace(/[\r\n\t ]+/g,"");
    },

    /**
     * Get all of an element's parent elements up the DOM tree
     *
     * @param  {Node}   elem     The element
     * @param  {String} selector Selector to match against [optional]
     * @return {Array}           The parent elements
     *
     * https://gomakethings.com/climbing-up-and-down-the-dom-tree-with-vanilla-javascript/
     *
     */
    getAncestors: function (elem, selector) {

        // Element.matches() polyfill
        if (!Element.prototype.matches) {
            Element.prototype.matches =
                Element.prototype.matchesSelector ||
                Element.prototype.mozMatchesSelector ||
                Element.prototype.msMatchesSelector ||
                Element.prototype.oMatchesSelector ||
                Element.prototype.webkitMatchesSelector ||
                function(s) {
                    var matches = (this.document || this.ownerDocument).querySelectorAll(s),
                        i = matches.length;
                    while (--i >= 0 && matches.item(i) !== this) {}
                    return i > -1;
                };
        }

        // Setup parents array
        let parents = [];

        // Get matching parent elements
        for ( ; elem && elem !== document; elem = elem.parentNode ) {

            // Add matching parents to array
            if ( selector ) {
                if ( elem.matches( selector ) ) {
                    parents.push( elem );
                }
            } else {
                parents.push( elem );
            }

        }

        return parents;

    },

    /**
     * Elements inherit the events defined in their parent(s)
     *
     * For a subset of elements and events this function calculates the
     * inherited events and returns them.
     *
     */
    extractInheritedEvents: function (tag_name, element) {
        if( !_DOMAnalyzer.elements_allowed_to_inherit_events_from_ancestors.includes( tag_name ) ) return [];

        // TODO: extractInheritedEvents should also support dynamically added event
        //       handlers. Right now it goes up the DOM tree using elem.parentNode,
        //       but completely ignores any addEventListener calls that might have
        //       been made
        let ancestors = _DOMAnalyzer.getAncestors(element, null);
        let events = [];

        for( let ancestor_it = 0; ancestor_it < ancestors.length; ancestor_it++ ){
            let ancestor_elem = ancestors[ancestor_it];
            let ancestor_tag_name = ancestor_elem.tagName.toLowerCase();
            let ancestor_attribute_events = _DOMAnalyzer.extractEventsFromAttributesAndProperties(ancestor_tag_name, ancestor_elem);

            if (!ancestor_attribute_events.length) continue;

            // attribute_events holds the events associated with the ancestor element
            // those events are "scoped to the ancestor element", the following lines
            // change the scope to the child
            for( let event_it = 0; event_it < ancestor_attribute_events.length; event_it++ ){
                let ancestor_event = ancestor_attribute_events[event_it];

                ancestor_event.tag_name = tag_name;
                ancestor_event.selector = OptimalSelect.select(element);
                ancestor_event.node_type = element.nodeType;
                ancestor_event.text_content = _DOMAnalyzer.superTrim(element.textContent);

                events.push(ancestor_event);
            }
        }

        return events;
    },

    objectArrayUniq: function( array ) {
        let a = array.concat();

        for( let i = 0; i < a.length; ++i ) {

            let i_str = JSON.stringify(a[i]);

            for( let j = i + 1; j < a.length; ++j ) {
                if( i_str === JSON.stringify(a[j]) )
                    a.splice( j--, 1 );
            }
        }

        return a;
    },

    /**
     * Get event listeners in a paginated manner
     *
     * @param  {Array}   event_filter     If non-empty, only return these events in the result
     * @param  {Array}   tag_name_filter  If non-empty, only return events for these tag names
     * @param  {number}  start            Result index to start at when returning events
     * @param  {number}  count            How many events to return
     *
     */
    getEventListeners: function (event_filter, tag_name_filter, start, count) {
        let filtered_event_listeners = [];

        for(let elem_it = 0; elem_it < _DOMAnalyzer.event_listeners.length; elem_it++) {
            let event_listener = _DOMAnalyzer.event_listeners[elem_it];

            let tag_name = event_listener["tag_name"];
            let event_type = event_listener["event_type"];

            // Filter events by tag name (a, div, etc.)
            if( tag_name_filter.length > 0 && !tag_name_filter.includes(tag_name) ) continue;

            // Filter events by tag name (a, div, etc.)
            if( event_filter.length > 0 && !event_filter.includes(event_type) ) continue;

            filtered_event_listeners.push(event_listener);
        }

        return filtered_event_listeners.slice(start, start + count);
    },

    /**
     * Get set timeouts in a paginated manner
     *
     * @param  {number}  start            Result index to start at when returning events
     * @param  {number}  count            How many events to return
     *
     */
    getSetTimeouts: function (start, count) {
        return _DOMAnalyzer.set_timeouts.slice(start, start + count);
    },

    /**
     * Get set intervals in a paginated manner
     *
     * @param  {number}  start            Result index to start at when returning events
     * @param  {number}  count            How many events to return
     *
     */
    getSetIntervals: function (start, count) {
        return _DOMAnalyzer.set_intervals.slice(start, start + count);
    },

    /**
     * Get elements with event handlers
     *
     * @param  {Array}   event_filter     If non-empty, only return these events in the result
     * @param  {Array}   tag_name_filter  If non-empty, only return events for these tag names
     * @param  {number}  start            Result index to start at when returning events
     * @param  {number}  count            How many events to return
     *
     */
    getElementsWithEventHandlers: function (event_filter, tag_name_filter, start, count) {

        let all_elements = document.getElementsByTagName("*");
        let events = [];
        let ignored_events = 0;

        for(let elem_it = 0; elem_it < all_elements.length; elem_it++) {
            let element = all_elements[elem_it];

            if (_DOMAnalyzer.elementIsHidden(element)) continue;

            let tag_name = element.tagName.toLowerCase();

            // Filter events by tag name (a, div, etc.)
            if( tag_name_filter.length > 0 && !tag_name_filter.includes(tag_name) ) continue;

            // Get the element events
            let attribute_events = _DOMAnalyzer.extractEventsFromAttributesAndProperties(tag_name, element);
            let inherited_events = _DOMAnalyzer.extractInheritedEvents(tag_name, element);

            // Merge and unique
            let element_events = [];
            element_events = element_events.concat(attribute_events);
            element_events = element_events.concat(inherited_events);
            element_events = _DOMAnalyzer.objectArrayUniq(element_events);

            if (!element_events.length) continue;

            // Filter events by event type (click, hover, etc.)
            element_events = _DOMAnalyzer.filterByEventName(element_events, event_filter);

            // Pagination (1/2)
            let element_events_paginated = element_events.slice();

            while( true ){
                if (element_events_paginated.length === 0){
                    // This element has no more events
                    break
                }

                if (ignored_events < start){
                    element_events_paginated.splice(0, 1);
                    ignored_events += 1;
                } else break;
            }

            events = events.concat(element_events_paginated);

            // Pagination (2/2)
            if ( events.length >= count ){
                return events.splice(0, count);
            }
        }

        return events;
    },

    /**
     * Filter previously extracted events by event_type (click, hover, etc.)
     *
     * @param  {Array}   element_events   Events for a specific DOM element
     * @param  {Array}   event_filter     If non-empty, only return these events in the result
     *
     */
    filterByEventName: function (element_events, event_filter) {
        if( event_filter.length === 0 ) return element_events;

        return element_events.filter(function(event) {
            return event_filter.includes(event.event_type);
        });
    },

};

_DOMAnalyzer.initialize();