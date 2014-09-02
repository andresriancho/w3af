"""
stats.py

Copyright 2007 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
from __future__ import division

import gtk
import gobject
from collections import namedtuple

Frame = namedtuple('Frame', 'title items')
StatusItem = namedtuple('StatusItem', 'title default_value getter unit tooltip')


class StatsViewer(gtk.VBox):
    """
    This is the information I want to show in the stats viewer:
    
    Crawl queue stats:
        * Input speed: 30 URLs/min
        * Output speed: 40 URLs/min
        * Queue size: 300 URLs
        * Current URL: GET | http://host.tld/foo.bar
        * Estimated time until finish: 3min
    
    Audit queue stats:
        * Input speed: 30 URLs/min
        * Output speed: 40 URLs/min
        * Queue size: 300 URLs
        * Current URL: GET | http://host.tld/spam.eggs?id=1
        * Estimated time until finish: 3min

    HTTP speed: 150 req/min
    """
    VIEW_DATA = [Frame('Crawl status',
                       [StatusItem('Input speed', '0', 'crawl_input_speed', 'URLs/min', 'Queue input speed'),
                        StatusItem('Output speed', '0', 'crawl_output_speed', 'URLs/min', 'Queue output speed'),
                        StatusItem('Queue size', '0', 'crawl_qsize', 'URLs', 'Queue size'),
                        StatusItem('Current URL', 'n/a', 'crawl_current_fr', None, 'Current URL being processed'),
                        StatusItem('ETA', 'Unknown', 'crawl_eta', 'h:m', 'Time to finish processing this queue'),]
                       ),
                 Frame('Audit status',
                       [StatusItem('Input speed', '0', 'audit_input_speed', 'URLs/min', 'Queue input speed'),
                        StatusItem('Output speed', '0', 'audit_output_speed', 'URLs/min', 'Queue output speed'),
                        StatusItem('Queue size', '0', 'audit_qsize', 'URLs', 'Queue size'),
                        StatusItem('Current URL', 'n/a', 'audit_current_fr', None, 'Current URL being processed'),
                        StatusItem('ETA', 'Unknown', 'audit_eta', 'h:m', 'Time to finish processing this queue'),]
                       ),
                 Frame('Other',
                       [StatusItem('HTTP speed', '0', 'rpm', 'requests/min', 'HTTP client speed'),
                        ]
                       ),
                 
                 ]
    
    def __init__(self, w3af):
        super(StatsViewer, self).__init__()
        self.w3af = w3af
        
        self.build_default()
        
        # Refresh the content
        gobject.timeout_add(200, self.update().next)
        
        self.show()

    def build_default(self):
        for item in self.VIEW_DATA:
            
            if isinstance(item, StatusItem):
                self.add_status_item(item, self)
            
            if isinstance(item, Frame):
                frame = gtk.Frame(item.title)
                vbox = gtk.VBox()
                vbox.show()
                
                for status_item in item.items:
                    self.add_status_item(status_item, vbox)
                
                frame.add(vbox)
                frame.set_shadow_type(gtk.SHADOW_ETCHED_OUT)
                frame.show()
                self.pack_start(frame, False, False, 3)

    def update(self):
        while True:

            set_defaults = False
            
            if not self.w3af.status.is_running() or self.w3af.status.is_paused():
                set_defaults = True
           
            for frame in self.VIEW_DATA:
                for item in frame.items:
                    new_text = self.generate_text(item, set_defaults)
                    self.update_status_item(item.getter, new_text, self)
                    
                    yield True
    
    def generate_text(self, item, default=False):
        try:
            value = getattr(self.w3af.status, 'get_%s' % item.getter)()
        except RuntimeError:
            value = item.default_value
        else:
            value = item.default_value if value is None or default else value

        # https://github.com/andresriancho/w3af/issues/2679
        if isinstance(value, basestring):
            value = value.replace('\0', '')
            
        text = '%s: %s' % (item.title, value)
        
        if item.unit is not None:
            text += ' (%s)' % item.unit
            
        return text        
    
    def add_status_item(self, item, parent):
        align = gtk.Alignment()
        align.show()
        
        lab = gtk.Label(self.generate_text(item))
        lab.set_tooltip_text(item.tooltip)
        lab.show()
        lab.set_justify(gtk.JUSTIFY_FILL)
        
        # We use this for the update
        lab.identifier = item.getter
        
        align.add(lab)

        parent.pack_start(align)

    def update_status_item(self, identifier, new_text, parent):
        for child in parent.get_children():
            
            if hasattr(child, 'identifier'):
                if child.identifier == identifier:
                    child.set_text(new_text)
                    return
            
            if hasattr(child, 'get_children'):
                self.update_status_item(identifier, new_text, child)
