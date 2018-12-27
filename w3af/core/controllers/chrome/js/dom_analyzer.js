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

    selector_generator: new CssSelectorGenerator,

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

            _DOMAnalyzer.set_timeouts.push([function_, timeout]);
            original_setTimeout.apply(this, arguments);
        };
    },

    // Override window.setInterval()
    override_setInterval: function () {
        let original_setInterval = window.setInterval;

        window.setInterval = function() {

            let function_ = arguments[0];
            let timeout = arguments[1];

            _DOMAnalyzer.set_intervals.push([function_, timeout]);
            original_setInterval.apply(this, arguments);
        };
    },

    /**
     * Override window.addEventListener and Node.prototype.addEventListener
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
            _DOMAnalyzer.storeEventListenerData(document, event, listener, useCapture);
            original_document_addEventListener.apply(document, Array.prototype.slice.call(arguments));
        };

        // Override Node.prototype.addEventListener
        let original_node_addEventListener = Node.prototype.addEventListener;

        Node.prototype.addEventListener = function (type, listener, useCapture) {
            _DOMAnalyzer.storeEventListenerData(this, type, listener, useCapture);
            original_node_addEventListener.apply(this, Array.prototype.slice.call(arguments));
        };
    },

    /**
     * Store event listener data
     *
     * @param element          element           window, document, node
     * @param type             string            The event type, eg. onclick
     * @param listener         function          The function that handles the event
     * @param useCapture       boolean           As defined in the addEventListener docs
     *
     * https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/addEventListener
     *
     */
    storeEventListenerData: function (element, type, listener, useCapture) {

        // TODO: Research why storing element and listener and then reading it
        //       with the chrome protocol will return {}, which is useless for
        //       all cases.

        let selector = _DOMAnalyzer.selector_generator.getSelector(element);

        _DOMAnalyzer.event_listeners.push([element.tagName.toLowerCase(),
                                           element.nodeType,
                                           selector,
                                           type,
                                           useCapture]);
    },

    /**
     * Dispatch an event
     *
     * https://developer.mozilla.org/en-US/docs/Web/API/Document/createEvent
     * https://developer.mozilla.org/en-US/docs/Web/API/EventTarget/dispatchEvent
     */
    dispatchCustomEvent: function (index) {

        // TODO: For now we use the index in event_listeners
        [element, type, listener, useCapture] = _DOMAnalyzer.event_listeners[index];

        if (_DOMAnalyzer.elementIsHidden(element)) return false;

        let event = document.createEvent("Events");
        event.initEvent(type, true, true);
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
     * Get elements with events
     *
     */
    getElementsWithEventHandlers: function (index) {

        let all_elements = document.getElementsByTagName("*");

        for(let i = 0; i < length; i++) {
            let element = all_elements[i];

            if (_DOMAnalyzer.elementIsHidden(element)) return false;

            var tag_name = element.tagName.toLowerCase();

        }


    },

};

_DOMAnalyzer.initialize();