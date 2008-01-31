// CREDITS: // Automatic Page Refresher by 
Peter Gehrig and Urs Dudli www.24fun.com // Permission given to use the script 
provided that this notice remains as is. // Additional scripts can be found at 
http://www.hypergurl.com // Configure refresh interval (in seconds) var refreshinterval=5 
// Shall the coundown be displayed inside your status bar? Say "yes" 
or "no" below: var displaycountdown="yes" // Do not edit the 
code below var starttime var nowtime var reloadseconds=0 var secondssinceloaded=0 
function starttime() { starttime=new Date() starttime=starttime.getTime() countdown() 
} function countdown() { nowtime= new Date() nowtime=nowtime.getTime() secondssinceloaded=(nowtime-starttime)/1000 
reloadseconds=Math.round(refreshinterval-secondssinceloaded) if (refreshinterval>=secondssinceloaded) 
{ var timer=setTimeout("countdown()",1000) if (displaycountdown=="yes") 
{ window.status="Page refreshing in "+reloadseconds+ " seconds" 
} } else { clearTimeout(timer) window.location.reload(true) } } window.onload=starttime 

