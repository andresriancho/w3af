/** 
  * Copyright 2015, Yahoo Inc. All rights reserved.
  * Use of this source code is governed by a BSD-style
  * license that can be found in the LICENSE file.
  *
  * @author Adon adon@yahoo-inc.com
  * @desc this module exposes more usable events, and a better event handling logic
  *
  *  Event Flow:
  * ===================
  * onNavigationRequested
  * onResourceRequested
  * onNavigationRequested + onResourceRequested -> onNavigate, onMainFrameNavigate, onMainFramePreRedirection, onChildFrameNavigate
  * onLoadStarted
  *
  * onResourceReceived 
  * onResourceReceived + mainFrame -> onMainFrameResourceReceived
  * [onResourceTimeout/onResourceError] + mainFrame -> onMainFrameError, onMainFrameResourceError
  *
  * onInitialized
  * 
  * onMainFrameNavigationsEnded
  * 
  * onSubResourceRequested
  * [onMainFramePostRedirection]
  *
  * onLoadFinished
  * onLoadFinished + status=='success' -> onMainFrameLoadSuccess
  * onLoadFinished + status=='fail' -> onMainFrameLoadFailed, onMainFrameError
  *
  * [onMainFrameLoadSuccess] + steadyLogic() -> onMainFrameSteady

ResourceError Codes
# errorMessage[1] = "Connection Refused Error";
# errorMessage[2] = "RemoteHost Closed Error";
# errorMessage[3] = "Host Not Found Error";
# errorMessage[4] = "Timeout Error";
# errorMessage[5] = "Operation Canceled Error";
# errorMessage[6] = "Ssl Handshake Failed Error";
# errorMessage[7] = "Temporary Network Failure Error";
# errorMessage[8] = "Network Session Failed Error";
# errorMessage[9] = "Background Request Not Allowed Error";
# errorMessage[99] = "Unknown Network Error";
# errorMessage[101] = "ProxyConnectionRefusedError";
# errorMessage[102] = "ProxyConnectionClosedError";
# errorMessage[103] = "ProxyNotFoundError";
# errorMessage[104] = "ProxyTimeoutError";
# errorMessage[105] = "ProxyAuthenticationRequiredError";
# errorMessage[199] = "UnknownProxyError";
# errorMessage[201] = "ContentAccessDenied";
# errorMessage[202] = "ContentOperationNotPermittedError";
# errorMessage[203] = "ContentNotFoundError";
# errorMessage[204] = "AuthenticationRequiredError";
# errorMessage[205] = "ContentReSendError";
# errorMessage[299] = "UnknownContentError";
# errorMessage[301] = "ProtocolUnknownError";  // after networkRequest.abort()
# errorMessage[302] = "ProtocolInvalidOperationError";
# errorMessage[399] = "ProtocolFailure";

*/

exports.init = function(phantom, page) {

    var callbackList = {},
        resourceDetails = {},
        navigationalRequests = {},
        mainFrameStatus = {},
        mainFrameNetwork = {},
        timerCounter = 0;

    // patch response.redirectURL to take the URL (can be relative) in Location header 
    function patchRedirectURL(response) {
        // we honor the location header only if response.status = 3xx
        !response.redirectURL && response.status 
        && response.status >= 300 && response.status < 400 
        && response.headers && response.headers.some(function(h){
            if (h.name.toLowerCase() == 'location') {
                response.redirectURL = h.value;
                return true;
            }
        });
    }

    // a shortcut to invoke the customized listeners
    function invokeListeners(eventName) {
        // copy arguments to a new array, and removes the first element
        var i = 0, key, args = [], handler;
        for (key in arguments)
            args[i++] = arguments[key];
        args.shift();

        handler = page[eventName] || queuedEventCallbacks(eventName);
        return handler && handler.apply(page, args);
    }


    // when all handlers of an event returns false, give up the event listener
    function queuedEventCallbacks(eventName) {
        return function() {
            // disable executing any more event handlers when an error was once thrown
            if (mainFrameStatus.error)
                return;
            
            // (eventName == 'onCallback') ? console.log(JSON.stringify(arguments[0])) : console.log('debug: ' + eventName + ' ' + (/^onSteady-/.test(eventName) ? arguments[0] + ' ' + JSON.stringify(mainFrameNetwork.outstanding) : arguments[0]&&arguments[0].url));
            // mainFrameStatus.externalError && console.log('extern:' + JSON.stringify(mainFrameStatus.externalError));

            // if an externalError was ever raised, instead of invoking the following events, we raise an onMainFrameError
            if (mainFrameStatus.externalError
                    && ['onMainFrameResourceReceived', 'onLoadStarted', 'onInitialized', 
                        'onLoadFinished', 'onMainFrameLoadSuccess', 'onMainFrameSteady'].indexOf(eventName) !== -1) {
                var response = mainFrameStatus.response || {};
                response.url = response.url || mainFrameStatus.request.url;
                response.errorCode = mainFrameStatus.externalError.errorCode;
                response.errorString = mainFrameStatus.externalError.errorString;
                invokeListeners('onMainFrameError', response);
                return;
            }

            var eventCallbackList = callbackList[eventName];
            if (eventCallbackList) {
                for (var i = 0, _callback; _callback = eventCallbackList[i]; i++) 
                    if (_callback.apply(this, arguments) === false)
                        eventCallbackList.splice(i--, 1);

                if (eventCallbackList.length === 0)
                    page[eventName] = null;
            }

            if (eventName == 'onMainFrameError')
                mainFrameStatus.error = true;
        };
    };

    // callback added from this handler won't overwrite existing ones
    // return false to get itself removed from the event queue
    function addListener(eventName, callback, thirdarg){
        if (!callback)
            return;

        if (eventName == 'onSteady') {
            mainFrameNetwork.steadyMonitor(callback, thirdarg);
            return;
        }

        if (eventName.indexOf('on') !== 0)
            eventName = 'on' + eventName;
        callbackList[eventName] = callbackList[eventName] || [];
        callbackList[eventName].push(callback);

        // skip adding those events to page that phantomjs won't fire by itself
        if (!/^(?:onMainFrame|onSteady)/.test(eventName) && !page[eventName])
            page[eventName] = queuedEventCallbacks(eventName);
    }

    // keep track of the resource status
    // resourceDetails['req-N'] may have {req, actions, aborted, resp, err}
    addListener('ResourceRequested', function(arg0, arg1){
        var resId = 'res' + arg0.id;
        resourceDetails[resId] = {'req': arg0, 'actions': arg1};
    });
    addListener('ResourceReceived', function(arg0){
        var resId = 'res' + arg0.id, resObj = resourceDetails[resId];

        // ResourceError fires before ResourceReceived
        // make error code and string captured at ResourceError available to ResourceReceived 
        if (resObj.err) {
            arg0.errorCode = resObj.err.errorCode;
            arg0.errorString = resObj.err.errorString;
            resObj.aborted && (arg0.aborted = resObj.aborted);

            arg0.url = arg0.url || resObj.req.url; 
        }
        patchRedirectURL(arg0);
        resObj.resp = arg0;
    });
    // onResourceTimeout, onResourceError is also fired
    addListener('ResourceError', function(arg0){
        var resId = 'res' + arg0.id, resObj = resourceDetails[resId];
        // Upon abortion, url is stripped, resulting in protocol error (301)
        if (arg0.errorCode === 301 && arg0.url === '') 
            resObj.aborted = arg0.aborted = true;
        resObj.resp = resObj.err = arg0;
    });


    // onSteady Algorithm: 
    //  1) mainFrameNetwork.monitor(onSteady, timeout=4000ms) initiaites:
    //        a) minSteadyTimer (i.e., Min(300ms, timeout/10))
    //        b) maxSteadyTimer (i.e., maxSteadyTimeout = 4000ms)
    //      c) Steady-ready(resourceId) cancels Steady-wait(resourceId)
    //  2) If nothing fired during minSteadyTimer, 
    //       or in case 1(c) above ever happened, cancels minSteadyTimer
    //     finally, each Steady-ready() will see if for 75ms no more Steady-ready(), 
    //              and outStandingReqs.length == 0, fires onSteady()
    //  3) If take longer than maxSteadyTimeout, fires onSteady()
    mainFrameNetwork.steadyMonitor = function(onSteady, timeout){
        mainFrameNetwork.outstanding = {'minSteadyTimer':true};

        // install a one-time onSteady listener
        mainFrameNetwork.onSteady = onSteady || function(){};
        // 4000ms based on stats concerning max time users'd normally expect, as suggested by @albertyu
        timeout = parseInt(timeout || 4000);
        mainFrameNetwork.maxTimeout = timeout;
        
        mainFrameNetwork.minSteadyTimer = setTimeout(function(){
            invokeListeners('onSteady-ready', 'minSteadyTimer');
        }, Math.min(300, timeout/10));

        clearTimeout(mainFrameNetwork.maxSteadyTimer);
        // the max post onloaded time to tolerate: 4 secs as suggested by @albert
        mainFrameNetwork.maxSteadyTimer = setTimeout(function(){
            mainFrameNetwork.onSteady('maxSteadyTimer');
        }, timeout);

        // monitor outstanding requests
        if (!mainFrameStatus.steadyMonitor) {
            mainFrameStatus.steadyMonitor = true;
            addListener('ResourceRequested', function(arg0, arg1){
                invokeListeners('onSteady-wait', 'res' + arg0.id);
            });
            // onResourceTimeout, onResourceError will also be fired
            ['ResourceReceived','ResourceError'].forEach(function(eventName){
                addListener(eventName, function(arg0){
                    (!arg0.stage || arg0.stage == 'end') && invokeListeners('onSteady-ready', 'res' + arg0.id);
                });
            });
        }
    };
    addListener('Steady-wait', function(reason) {
        mainFrameNetwork.outstanding[reason] = true;
        clearTimeout(mainFrameNetwork.finalistTimer);

        // cancel the minSteadyTimer
        if (mainFrameNetwork.outstanding['minSteadyTimer']) {
            delete mainFrameNetwork.outstanding['minSteadyTimer'];
            clearTimeout(mainFrameNetwork.minSteadyTimer);
        }
    })
    addListener('Steady-ready', function(reason){
        delete mainFrameNetwork.outstanding[reason];

        // extend the finialist timer by discarding the previous one (non-atomic operations, but good enough)
        clearTimeout(mainFrameNetwork.finalistTimer);
        // wait for another 20ms to make sure the sea is completely silenced (i.e., no more new requests)
        mainFrameNetwork.finalistTimer = setTimeout(function(){
            if (Object.keys(mainFrameNetwork.outstanding).length === 0)
                mainFrameNetwork.onSteady('done');
        }, 75);
    })
    // introduce a reason to wait setTimeout/Interval for 'timeout' ms once
    addListener('Steady-waitTimer', function(timeout){
    	// directly ignore timeout longer than maxTimeout
    	function readyToWait() {
    		return mainFrameNetwork.maxTimeout && timeout < mainFrameNetwork.maxTimeout;
    	}

        var reason = ['timer', timerCounter++, timeout].join('-');
        if (readyToWait())
            invokeListeners('onSteady-wait', reason);
        else 
            addListener('MainFrameSteady', function(){
                readyToWait() && invokeListeners('onSteady-wait', reason);
                return false;
            });
        window.setTimeout(function(){
            readyToWait() && invokeListeners('onSteady-ready', reason);
        }, timeout || 1);
    })
    

    // LoadStarted fires only for mainFrame
    addListener('LoadStarted', function(){
        mainFrameStatus.loadStarted = true;
    });


    // expose the following customized events:
    //  - onNavigate:
    //  - onMainFrameNavigate: 
    //  - onChildFrameNavigate: 
    addListener('NavigationRequested', function(url, type, willNavigate, fromMainFrame) {
        if (!url || url === 'about:blank' || !willNavigate)
            return;

        addListener('ResourceRequested', function(requestData, networkRequest) {
            // traceback if such URL is recently recorded as the navigation
            if (decodeURI(url) === decodeURI(requestData.url) || url === requestData.url) {

                // let resourceDetails know whether a particular resource happens in frames
                var resObj = resourceDetails['res' + requestData.id];
                resObj.fromFrame = true;
                resObj.req.fromMainFrame = fromMainFrame;
                resObj.req.navigationType = type;

                // mark this as a navigational request
                navigationalRequests[requestData.id] = resObj;

                invokeListeners('onNavigate', requestData, networkRequest, fromMainFrame, type);
                invokeListeners((fromMainFrame ? 'onMainFrameNavigate' : 'onChildFrameNavigate'),
                                requestData, networkRequest, type);

                return false;
            }
        });
    });

    // expose the following customized events:
    //  - onSubResourceRequested: fired for subresource requests (i.e., not from frames/windows)
    addListener('NavigationRequested', function(url, type, willNavigate, fromMainFrame) {
        // the following is setup in NavigationRequested so as to run after the ResourceRequested setup above
        addListener('ResourceRequested', function(requestData, networkRequest) {
            if (!navigationalRequests[requestData.id])
                invokeListeners('onSubResourceRequested', requestData, networkRequest);
        });
        return false;
    });

    // expose the following customized events:
    //  - onMainFramePostRedirection:
    //  - onMainFramePreRedirection
    addListener('MainFrameNavigate', function(requestData, networkRequest, type) {
        if (requestData.id !== 1)
            invokeListeners('onMainFrameRedirection', requestData, networkRequest, type);

        if (mainFrameStatus.navigationsEnded)
            invokeListeners('onMainFramePostRedirection', requestData, networkRequest, type);
        else if (requestData.id !== 1)
            invokeListeners('onMainFramePreRedirection', requestData, networkRequest, type);

        if (mainFrameStatus.externalError)
            return;

        // backup the current mainFrameStatus, in case the new mainFrameStatus is detected being aborted
        var mainFrameStatusBackup = mainFrameStatus;
        // prepare a new mainFrameStatus
        mainFrameStatus = {'requested': true, 'request': requestData};
        if (mainFrameStatusBackup.requested)
        	mainFrameStatus.lastBackup = mainFrameStatusBackup;

        // expose the following customized events:
        //  - onMainFrameNavigationsEnded: fired once when the MainFrame has no more redirections
        addListener('ResourceReceived', function(response) {
            // ignore subresource's response 
            if (mainFrameStatus.request.id !== response.id)
                return;

            // restore the original mainFrameStatus if the current one is aborted
            if (response.aborted) {
                invokeListeners('onMainFrameResourceAborted', response);
                invokeListeners('onMainFrameResourceReceived', response);

                if (mainFrameStatus.lastBackup)
                	mainFrameStatus = mainFrameStatus.lastBackup;
                else
                	mainFrameStatus.response = response;

                if (!mainFrameStatus.navigationsEnded) {
                	mainFrameStatus.navigationsEnded = true;
                	invokeListeners('onMainFrameNavigationsEnded', mainFrameStatus.response);
                }
                return false;
            }

            mainFrameStatus.response = response;

            if (response.errorCode) {
                invokeListeners('onMainFrameResourceError', response);
                invokeListeners('onMainFrameResourceReceived', response);
                invokeListeners('onMainFrameError', response);
                return false;
            }
            
            invokeListeners('onMainFrameResourceReceived', response);

            // the mainFrame's response[stage=start] that has no further redirections 
            if (!mainFrameStatus.navigationsEnded 
                    && (response.status < 300 || !response.redirectURL)) {
                mainFrameStatus.navigationsEnded = true;
                invokeListeners('onMainFrameNavigationsEnded', response);

                mainFrameStatus.destResponse = response;

            // the corresponding mainFrame's response[stage=end]
            } else {
                delete mainFrameStatus.destResponse;
                // this is important to deactivate this listener once the main response is downloaded
                return false;
            }
        });
    });


    addListener('LoadFinished', function(status) {
        var response = mainFrameStatus.response || {'url': url};
        
        mainFrameStatus.loadFinished = true;
        if (status == 'success' 
                || (page.content && page.content !== '<html><head></head><body></body></html>')
                || (response.status && response.status >= 300 && response.status < 400)) {
            mainFrameStatus.loadSuccess = true;
            invokeListeners('onMainFrameLoadSuccess', response);
        } else {
            mainFrameStatus.loadFailed = true;
            response.errorCode = response.errorCode || 1002;
            response.errorString = response.errorString || 'Load Failed Error (from disallowed domains)';
            
            invokeListeners('onMainFrameLoadError', response);
            invokeListeners('onMainFrameError', response);
        }
        return false;
    });

    addListener('MainFrameLoadSuccess', function(response){
        addListener('onSteady', function(lastSignal){
            if (!mainFrameStatus.steady) {
                mainFrameStatus.steady = true;

                // note that page.content may not contain all dynamically-generated content
                // for content-type like xml will have no JS execution context, page.evaluate() returns null, so we resort to page.content
                var html = page.evaluate(function(){return document.documentElement ? document.documentElement.outerHTML : ''});
                response.body = html || page.content || response.body;

                invokeListeners('onMainFrameSteady', response, lastSignal);
            }
        });
    });

    return {
        addListener: addListener,
        invokeListeners: invokeListeners,
        notifyError: function(errorCode, errorString, url){
            mainFrameStatus.externalError = {'errorCode': errorCode, 'errorString': errorString};
            if (url) mainFrameStatus.externalError.url = url;

            // if not even requested, invoke MainFrameError immediately
            !mainFrameStatus.requested && invokeListeners('onMainFrameError', mainFrameStatus.externalError);
        },
        getMainFrameStatus: function(){
            return mainFrameStatus;
        },
        getResources: function() {
            return resourceDetails;
        }
    };
};