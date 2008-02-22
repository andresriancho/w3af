/*
*
*
*   Moth class definition
*
*
*/

function mothClass(){
    // Constructor Code
    this.initialized = true;
    this.oldLocation = "";
}

// Start running
mothClass.prototype.startMoth = function(){
        this.startSendingEvents();
        //window.open("chrome://helloworld/content/hello.xul", "", "chrome");
}


// Called after the page finished loading
// Sends the mouse events to every tag
mothClass.prototype.startSendingEvents = function(){
    var excp;
    this.oldLocation = window.content.document.location;
    
    try
    {
        var i;
        var elm;
        var elmlist;

        elmlist = this.getLeaves();
        for (i = 0; i < elmlist.length; i++)
        {
            elm = elmlist[i];
            this.SendMouseEvent('mouseover', elm);
            this.SendMouseEvent('mouseout', elm);
            this.SendMouseEvent('click', elm);

            // If the document.location changed, go back to the original URL
            // This wont work when I test the JS code outside the XPI!!
            if (this.oldLocation != window.content.document.location ){
                history.go(-1);
                alert("gone back");
            }
        }
    }
    catch(excp)
    {
        // TODO: Remove or change this.
        alert(excp);
    }
}

// Function that returns a list of all leaves of a node
mothClass.prototype.getLeaves = function(){
  return window.content.document.getElementsByTagName('*');
}

// Sends the mouse event of type eventtype to the element
mothClass.prototype.SendMouseEvent = function(eventtype, elm){
  var canBubble = true;
  var cancelable = true;
  var detail = 0;

  var clientPosition = this.getClientPosition(elm);

  var screenPosition = {
    x: clientPosition.x + window.screenX,
    y: clientPosition.y + window.screenY
  };

  try
  {
    var evtMouse = document.createEvent('MouseEvents');
    evtMouse.initMouseEvent(
                 eventtype,
                 canBubble, 
                 cancelable, 
                 window, 
                 detail,
                 screenPosition.x,
                 screenPosition.y,
                 clientPosition.x,
                 clientPosition.y,
                 false,
                 false,
                 false,
                 true,
                 0, 
                 elm.parentNode
                 );
     elm.dispatchEvent(evtMouse);
   }
   catch(e)
   {
     // this can happen in particular when calling dispatchEvent on an
     // applet. There appears to be no conversion from a DOM2 event
     // and an AWTEvent.
   }

},

// Get the position of an element
// Used to send a mouse event to a specific position
mothClass.prototype.getClientPosition = function(elm){
    var position = { x: elm.offsetLeft, y:  elm.offsetTop};

    while (elm.offsetParent)
    {
        elm = elm.offsetParent;
        position.x += elm.offsetLeft;
        position.y += elm.offsetTop;
    }

    return position;
}

/*
*
*
*   Main
*
*
*/
function startMoth(event){
    // Disable window alerts and prompts
    // TODO: This doesn't work!!!
    window.content.prompt = function() {};
    window.content.alert = function() {};


    m = new mothClass;
    m.startMoth();
}

