/*
 * Global variables
 */

var web_windows_theme = "metasploit";

/*
 * Window Management code and Dialogs
 */

var winIndex = 0;

/* Returns a unique Window identifier */
function obtainWindowId() {
	return (winIndex++);
}

function openStartWindow() {
    openKbWindow();
    var win = create_window_ajax("/start.win", "start", "w3af Log Console", 760, 300);
    win.setDestroyOnClose();
    win.showCenter();
}

function openKbWindow() {
    var win = create_window_ajax("/kbExplorer.win", "kbexplorer", "KnowledgeBase Explorer", 250, 400);
    win.setDestroyOnClose();
    win.show();
}

/*
 * Create and AJAX based window from extenal content
 */
function create_window_ajax(target_url, wid, wtitle, wwidth, wheight) {
	var uid = obtainWindowId();
	var new_mwindow = new Window(wid+'-'+uid,
	{ 
		className: web_windows_theme,
		title: wtitle + ' (' + uid+')',
		top:70,
		left:100,
		width:wwidth,
		height:wheight,
		resizable: true,
		draggable: true,
		url: target_url,
		showEffect: Element.show,
		hideEffect: Element.hide
	});
    return new_mwindow;
}
