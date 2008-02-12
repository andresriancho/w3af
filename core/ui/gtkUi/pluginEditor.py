#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# This script shows the use of pygtksourceview module, the python wrapper
# of gtksourceview C library.
# It has been directly translated from test-widget.c
#
# Copyright (C) 2004 - Iñigo Serna <inigoserna@telefonica.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


import os, os.path
import sys
import pygtk
pygtk.require ('2.0')

import gtk
if gtk.pygtk_version < (2,3,93):
    print "PyGtk 2.3.93 or later required for this example"
    raise SystemExit

import gtksourceview
import gnomevfs
import pango
import gnomeprint.ui

import subprocess

import time

######################################################################
##### global vars
windows = []    # this list contains all view windows
MARKER_TYPE_1 = 'one'
MARKER_TYPE_2 = 'two'
DATADIR = '/usr/share'

######################################################################
##### Plugin editor starter function
def editPlugin( widget, pluginName, pluginType ):
    '''
    I get here when the user right clicks on a plugin name, then he clicks on "Edit..."
    This method calls the plugin editor as a separate process and exists.
    '''
    program = 'python'
    fName = 'plugins/' + pluginType + '/' + pluginName + '.py'
    try:
        subprocess.Popen(['python', 'core/ui/gtkUi/pluginEditor.py', fName])
    except Exception, e:
        msg = 'Error while starting the w3af plugin editor.'
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, msg)
        dlg.set_title('Error')
        dlg.run()
        dlg.destroy()
        
######################################################################
##### error dialog
def error_dialog(parent, msg):
    dialog = gtk.MessageDialog(parent,
                               gtk.DIALOG_DESTROY_WITH_PARENT,
                               gtk.MESSAGE_ERROR,
                               gtk.BUTTONS_OK,
                                msg)
    dialog.run()
    dialog.destroy()
    

######################################################################
##### remove all markers
def remove_all_markers(buffer):
    begin, end = buffer.get_bounds()
    markers = buffer.get_markers_in_region(begin, end)
    map(buffer.delete_marker, markers)


######################################################################
##### load file
def load_file(buffer, uri):
    buffer.begin_not_undoable_action()
    # TODO: use g_io_channel when pygtk supports it
    try:
        txt = open(uri.path).read()
    except:
        return False
    buffer.set_text(txt)
    buffer.set_data('filename', uri.path)
    buffer.end_not_undoable_action()

    buffer.set_modified(False)
    buffer.place_cursor(buffer.get_start_iter())
    return True


######################################################################
##### buffer creation
def open_file(buffer, filename):
    # get the new language for the file mimetype
    manager = buffer.get_data('languages-manager')

    if os.path.isabs(filename):
        path = filename
    else:
        path = os.path.abspath(filename)
    uri = gnomevfs.URI(path)

    mime_type = gnomevfs.get_mime_type(path) # needs ASCII filename, not URI
    if mime_type:
        language = manager.get_language_from_mime_type(mime_type)
        if language:
            buffer.set_highlight(True)
            buffer.set_language(language)
        else:
            print 'No language found for mime type "%s"' % mime_type
            buffer.set_highlight(False)
    else:
        print 'Couldn\'t get mime type for file "%s"' % filename
        buffer.set_highlight(False)

    remove_all_markers(buffer)
    load_file(buffer, uri) # TODO: check return
    return True


######################################################################
##### Printing callbacks
def page_cb(job, *args):
    percent = 100 * job.get_page() / job.get_page_count()
    print 'Printing %.2f%%    \r' % percent,


def finished_cb(job, *args):
    print
    gjob = job.get_print_job()
    preview = gnomeprint.ui.JobPreview(gjob, 'w3af - Plugin editor')
    preview.show()


######################################################################
##### Action callbacks
def numbers_toggled_cb(action, sourceview):
    sourceview.set_show_line_numbers(action.get_active())
    

def markers_toggled_cb(action, sourceview):
    sourceview.set_show_line_markers(action.get_active())
    

def margin_toggled_cb(action, sourceview):
    sourceview.set_show_margin(action.get_active())
    

def auto_indent_toggled_cb(action, sourceview):
    sourceview.set_auto_indent(action.get_active())
    

def insert_spaces_toggled_cb(action, sourceview):
    sourceview.set_insert_spaces_instead_of_tabs(action.get_active())
    

def tabs_toggled_cb(action, action2, sourceview):
    sourceview.set_tabs_width(action.get_current_value())
    

def new_view_cb(action, sourceview):
    window = create_view_window(sourceview.get_buffer(), sourceview)
    window.set_default_size(400, 400)
    window.show()
    

def print_preview_cb(action, sourceview):
    buffer = sourceview.get_buffer()
    job = gtksourceview.SourcePrintJob()
    job.setup_from_view(sourceview)
    job.set_wrap_mode(gtk.WRAP_CHAR)
    job.set_highlight(True)
    job.set_print_numbers(5)
    job.set_header_format('Printed on %A', None, '%F', False)
    filename = buffer.get_data('filename')
    job.set_footer_format('%T', filename, 'Page %N/%Q', True)
    job.set_print_header(True)
    job.set_print_footer(True)
    start, end = buffer.get_bounds()
    if job.print_range_async(start, end):
        job.connect('begin_page', page_cb)
        job.connect('finished', finished_cb)
    else:
        print 'Async print failed'


######################################################################
##### Buffer action callbacks
def open_file_cb(action, buffer):
    chooser = gtk.FileChooserDialog('Open file...', None,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                    gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    response = chooser.run()
    if response == gtk.RESPONSE_OK:
        filename = chooser.get_filename()
        if filename:
            open_file(buffer, filename)
    chooser.destroy()

def save_file_cb(action, buffer):
    txt = buffer.get_text(buffer.get_start_iter(),buffer.get_end_iter(), include_hidden_chars=True)
    openedFile = buffer.get_data('filename')
    try:
        f = open( openedFile, 'w' )
        f.write( txt )
        f.close()
    except Exception, e:
        msg = 'An error ocurred when trying to save the file. Exception details: ' + str(e)
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
        dlg.set_title('Error saving file')
        dlg.run()
        dlg.destroy()

def update_cursor_position(buffer, view):
    # This line fixes an error when using threads...
    time.sleep(0.01)
    
    tabwidth = view.get_tabs_width()
    pos_label = view.get_data('pos_label')
    iter = buffer.get_iter_at_mark(buffer.get_insert())
    nchars = iter.get_offset()
    row = iter.get_line() + 1
    start = iter
    start.set_line_offset(0)
    col = 0
    while not start.equal(iter):
        if start.get_char == '\t':
            col += (tabwidth - (col % tabwidth))
        else:
            col += 1
            start = start.forward_char()
    pos_label.set_text('char: %d, line: %d, column: %d' % (nchars, row, col))
    

def move_cursor_cb (buffer, cursoriter, mark, view):
    update_cursor_position(buffer, view)


def window_deleted_cb(widget, ev, view):
    if windows[0] == widget:
        gtk.main_quit()
    else:
        # remove window from list
        windows.remove(widget)
        # we return False since we want the window destroyed
        return False
    return True


def button_press_cb(view, ev):
    buffer = view.get_buffer()
    if not view.get_show_line_markers():
        return False
    # check that the click was on the left gutter
    if ev.window == view.get_window(gtk.TEXT_WINDOW_LEFT):
        if ev.button == 1:
            marker_type = MARKER_TYPE_1
        else:
            marker_type = MARKER_TYPE_2
        x_buf, y_buf = view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT,
                                                    int(ev.x), int(ev.y))
        # get line bounds
        line_start = view.get_line_at_y(y_buf)[0]
        line_end = line_start.copy()
        line_end.forward_to_line_end()

        # get the markers already in the line
        marker_list = buffer.get_markers_in_region(line_start, line_end)
        # search for the marker corresponding to the button pressed
        for m in marker_list:
            if m.get_marker_type() == marker_type:
                marker = m
                break
        else:
            marker = None

        if marker:
            # a marker was found, so delete it
            buffer.delete_marker(marker)
        else:
            # no marker found, create one
            marker = buffer.create_marker(None, marker_type, line_start)
    return False
        

######################################################################
##### Actions & UI definition
buffer_actions = [
    ('Open', gtk.STOCK_OPEN, '_Open', '<control>O', 'Open a file', open_file_cb),
    ('Save', gtk.STOCK_SAVE, '_Save', '<control>S', 'Save a file', save_file_cb),    
    ('Quit', gtk.STOCK_QUIT, '_Quit', '<control>Q', 'Exit the application', gtk.main_quit)
]

view_actions = [
    ('FileMenu', None, '_File'),
    ('ViewMenu', None, '_View'),
    ('PrintPreview', gtk.STOCK_PRINT, '_Print Preview', '<control>P', 'Preview printing of the file', print_preview_cb),
    ('NewView', gtk.STOCK_NEW, '_New View', None, 'Create a new view of the file', new_view_cb),
    ('TabsWidth', None, '_Tabs Width')
]

toggle_actions = [
    ('ShowNumbers', None, 'Show _Line Numbers', None, 'Toggle visibility of line numbers in the left margin', numbers_toggled_cb, False),
    ('ShowMarkers', None, 'Show _Markers', None, 'Toggle visibility of markers in the left margin', markers_toggled_cb, False),
    ('ShowMargin', None, 'Show M_argin', None, 'Toggle visibility of right margin indicator', margin_toggled_cb, False),
    ('AutoIndent', None, 'Enable _Auto Indent', None, 'Toggle automatic auto indentation of text', auto_indent_toggled_cb, False),
    ('InsertSpaces', None, 'Insert _Spaces Instead of Tabs', None, 'Whether to insert space characters when inserting tabulations', insert_spaces_toggled_cb, False)
]

radio_actions = [
    ('TabsWidth4', None, '4', None, 'Set tabulation width to 4 spaces', 4),
    ('TabsWidth6', None, '6', None, 'Set tabulation width to 6 spaces', 6),
    ('TabsWidth8', None, '8', None, 'Set tabulation width to 8 spaces', 8),
    ('TabsWidth10', None, '10', None, 'Set tabulation width to 10 spaces', 10),
    ('TabsWidth12', None, '12', None, 'Set tabulation width to 12 spaces', 12)
]

view_ui_description = """
<ui>
  <menubar name='MainMenu'>
    <menu action='FileMenu'>
      <menuitem action='PrintPreview'/>
    </menu>
    <menu action='ViewMenu'>
      <menuitem action='NewView'/>
      <separator/>
      <menuitem action='ShowNumbers'/>
      <menuitem action='ShowMarkers'/>
      <menuitem action='ShowMargin'/>
      <separator/>
      <menuitem action='AutoIndent'/>
      <menuitem action='InsertSpaces'/>
      <separator/>
      <menu action='TabsWidth'>
        <menuitem action='TabsWidth4'/>
        <menuitem action='TabsWidth6'/>
        <menuitem action='TabsWidth8'/>
        <menuitem action='TabsWidth10'/>
        <menuitem action='TabsWidth12'/>
      </menu>
    </menu>
  </menubar>
</ui>
"""

buffer_ui_description = """
<ui>
  <menubar name='MainMenu'>
    <menu action='FileMenu'>
      <menuitem action='Open'/>
      <menuitem action='Save'/>
      <separator/>
      <menuitem action='Quit'/>
    </menu>
    <menu action='ViewMenu'>
    </menu>
  </menubar>
</ui>
"""

    
######################################################################
##### create view window
def create_view_window(buffer, sourceview = None):
    # window
    window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    window.set_border_width(0)
    window.set_title('w3af - Plugin editor')
    windows.append(window) # this list contains all view windows

    # view
    view = gtksourceview.SourceView(buffer)
    buffer.connect('mark_set', move_cursor_cb, view)
    buffer.connect('changed', update_cursor_position, view)
    view.connect('button-press-event', button_press_cb)
    window.connect('delete-event', window_deleted_cb, view)

    # action group and UI manager
    action_group = gtk.ActionGroup('ViewActions')
    action_group.add_actions(view_actions, view)
    action_group.add_toggle_actions(toggle_actions, view)
    action_group.add_radio_actions(radio_actions, -1, tabs_toggled_cb, view)

    ui_manager = gtk.UIManager()
    ui_manager.insert_action_group(action_group, 0)
    # save a reference to the ui manager in the window for later use
    window.set_data('ui_manager', ui_manager)
    accel_group = ui_manager.get_accel_group()
    window.add_accel_group(accel_group)
    ui_manager.add_ui_from_string(view_ui_description)

    # misc widgets
    vbox = gtk.VBox(0, False)
    sw = gtk.ScrolledWindow()
    sw.set_shadow_type(gtk.SHADOW_IN)
    pos_label = gtk.Label('Position')
    view.set_data('pos_label', pos_label)
    menu = ui_manager.get_widget('/MainMenu')

    # layout widgets
    window.add(vbox)
    vbox.pack_start(menu, False, False, 0)
    vbox.pack_start(sw, True, True, 0)
    sw.add(view)
    vbox.pack_start(pos_label, False, False, 0)

    # setup view
    font_desc = pango.FontDescription('monospace 10')
    if font_desc:
        view.modify_font(font_desc)

    # change view attributes to match those of sourceview
    if sourceview:
        action = action_group.get_action('ShowNumbers')
        action.set_active(sourceview.get_show_line_numbers())
        action = action_group.get_action('ShowMarkers')
        action.set_active(sourceview.get_show_line_markers())
        action = action_group.get_action('ShowMargin')
        action.set_active(sourceview.get_margin())
        action = action_group.get_action('AutoIndent')
        action.set_active(sourceview.get_auto_indent())
        action = action_group.get_action('InsertSpaces')
        action.set_active(sourceview.get_insert_spaces_instead_of_tabs())
        action = action_group.get_action('TabsWidth%d' % sourceview.get_tabs_width())
        if action:
            action.set_active(True)

    # add marker pixbufs
    pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(DATADIR,
                                                       'pixmaps/apple-green.png'))
    if pixbuf:
        view.set_marker_pixbuf(MARKER_TYPE_1, pixbuf)
    else:
        print 'could not load marker 1 image.  Spurious messages might get triggered'
    pixbuf = gtk.gdk.pixbuf_new_from_file(os.path.join(DATADIR,
                                                       'pixmaps/apple-red.png'))
    if pixbuf:
        view.set_marker_pixbuf(MARKER_TYPE_2, pixbuf)
    else:
        print 'could not load marker 2 image.  Spurious messages might get triggered'

    vbox.show_all()

    return window
    
    
######################################################################
##### create main window
def create_main_window(buffer):
    window = create_view_window(buffer)
    ui_manager = window.get_data('ui_manager')
    
    # buffer action group
    action_group = gtk.ActionGroup('BufferActions')
    action_group.add_actions(buffer_actions, buffer)
    ui_manager.insert_action_group(action_group, 1)
    # merge buffer ui
    ui_manager.add_ui_from_string(buffer_ui_description)

    # preselect menu checkitems
    groups = ui_manager.get_action_groups()
    # retrieve the view action group at position 0 in the list
    action_group = groups[0]
    action = action_group.get_action('ShowNumbers')
    action.set_active(True)
    action = action_group.get_action('ShowMarkers')
    action.set_active(True)
    action = action_group.get_action('ShowMargin')
    action.set_active(True)
    action = action_group.get_action('AutoIndent')
    action.set_active(True)
    action = action_group.get_action('InsertSpaces')
    action.set_active(True)
    action = action_group.get_action('TabsWidth4')
    action.set_active(True)

    return window


######################################################################
##### main
def main(args):
    # create buffer
    lm = gtksourceview.SourceLanguagesManager()
    buffer = gtksourceview.SourceBuffer()
    buffer.set_data('languages-manager', lm)

    # parse arguments
    open_file(buffer, args[1])
        
    # create first window
    window = create_main_window(buffer)
    window.set_default_size(800, 600)
    try:
        window.set_icon_from_file('core/ui/gtkUi/data/w3af_icon.jpeg')
    except:
        try:
            window.set_icon_from_file('data/w3af_icon.jpeg')
        except:
            pass
    window.show()

    # main loop
    gtk.main()
    

if __name__ == '__main__':
    if '--debug' in sys.argv:
        import pdb
        pdb.run('main(sys.argv)')
    else:
        main(sys.argv)
