## Debugging

Debugging the `dom_analyzer.js` is a difficult task, but there are two main
ways to do it:

 * Add `console.log()` to the part of the JavaScript code you want to debug 
   and then use `instrumented_chrome.get_console_messages()` to the Python
   code to read all messages.
   
 * In `process.py` comment out the line that makes the Chrome process run in
   headless mode: `--headless`, run the unittest and then just consume the
   `DOMAnalyzer` using the browser JavaScript console:
   
   ```javascript
   window._DOMAnalyzer.getEventListeners([], [], 0, 20);

   ...

   window._DOMAnalyzer.extractEventsFromAttributesAndProperties('div', document.getElementsByClassName("item")[0]);
   ```
