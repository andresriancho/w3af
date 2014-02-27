"""
speedometer.py

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
import gtk
import gobject
import cairo
import pango
import random


MIN_SPEED = 0
MAX_SPEED = 400


class Speedometer(gtk.DrawingArea):
    
    # pylint: disable-msg=E1101
    
    def __init__(self):
        super(Speedometer, self).__init__()
        self.connect("expose_event", self.do_expose_event)

        # x,y is where I'm at
        self.x, self.y = -13, -9
        # rx,ry is point of rotation
        self.rx, self.ry = 28, 17
        # Is the current angle of the arrow
        self.rot = -3.64
        # sx,sy is to mess with scale
        self.sx, self.sy = 1, 1

        # Set the current speed to zero
        self._current_speed = self._old_speed = 0

        # This is what gives the animation life!
        gobject.timeout_add(2000, self.tick)

    def tick(self):
        # First I get a new speed from the "core"
        self._old_speed = self._current_speed

        self._current_speed = random.randint(MIN_SPEED, MAX_SPEED)

        # This invalidates the screen, causing the expose event to fire.
        self.alloc = self.get_allocation()
        rect = gtk.gdk.Rectangle(
            self.alloc.x, self.alloc.y, self.alloc.width, self.alloc.height)
        self.window.invalidate_rect(rect, True)

        return True  # Causes timeout to tick again.

    # When expose event fires, this is run
    def do_expose_event(self, widget, event):

        # Create a context for the arrow
        self.arrow_ctx = self.window.cairo_create()

        # Create a context for the background
        self.background_ctx = self.window.cairo_create()

        # Create a context for the text
        self.text_ctx = self.window.cairo_create()

        # Call our draw function to do stuff.
        self.draw(*self.window.get_size())

    def draw(self, width, height):
        # First we draw the background
        matrix = cairo.Matrix(1, 0, 0, 1, width / 2 - 126,
                              height / 2 - 126)  # 126 is image width/2
        self.background_ctx.transform(matrix)  # Make it so...
        self.draw_image(self.background_ctx, 0, 0, 'speedometer.png')

        # Now we draw the requests per second
        self.draw_text()

        # A shortcut
        cr = self.arrow_ctx

        # First, let's shift 0,0 to be in the center of page
        # This means:
        #  -y | -y
        #  -x | +x
        # ----0------
        #  -x | +x
        #  +y | +y

        matrix = cairo.Matrix(1, 0, 0, 1, width / 2, height / 2)
        cr.transform(matrix)  # Make it so...

        # Now save that situation so that we can mess with it.
        # This preserves the last context ( the one at 0,0)
        # and let's us do new stuff.
        cr.save()

        # Now attempt to rotate something around a point
        # Use a matrix to change the shape's position and rotation.

        # First, make a matrix. Don't look at me, I only use this stuff :)
        ThingMatrix = cairo.Matrix(1, 0, 0, 1, 0, 0)

        # Next, move the drawing to it's x,y
        cairo.Matrix.translate(ThingMatrix, self.x, self.y)
        cr.transform(ThingMatrix)  # Changes the context to reflect that

        # Now, change the matrix again to:
        cairo.Matrix.translate(
            ThingMatrix, self.rx, self.ry)  # move it all to point of rotation
        cairo.Matrix.rotate(ThingMatrix, self.rot)  # Do the rotation
        cairo.Matrix.translate(
            ThingMatrix, -self.rx, -self.ry)  # move it back again
        cairo.Matrix.scale(ThingMatrix, self.sx, self.sy)  # Now scale it all
        cr.transform(ThingMatrix)  # and commit it to the context

        # Now, whatever is draw is "under the influence" of the
        # context and all that matrix magix we just did.
        self.draw_image(cr, 0, 0, 'arrow.png')

        # Based on the current speed, and the current angle of the arrow I have to calculate
        # the angle to rotate (positive or negative).

        # I know that from min to max, we have 4.2.
        # I know that
        step = 4.2 / MAX_SPEED
        if self._current_speed >= self._old_speed:
            # I have to rotate right (+)
            self.rot += (self._current_speed - self._old_speed) * step
        else:
            # I have to rotate left (-)
            self.rot -= (self._old_speed - self._current_speed) * step

        print self.rot

        # Now mess with scale too
        self.sx += 0  # Change to 0 to see if rotation is working...
        if self.sx > 4:
            self.sx = 0.5
        self.sy = self.sx

        # We restore to a clean context, to undo all that hocus-pocus
        cr.restore()

    def draw_text(self):
        self._layout = self.create_pango_layout(
            str(self._current_speed) + ' req/second')
        self._layout.set_font_description(pango.FontDescription("Arial 13"))
        fontw, fonth = self._layout.get_pixel_size()
        self.text_ctx.move_to(150, 243)
        self.text_ctx.set_source_color(gtk.gdk.Color(255, 255, 255))
        self.text_ctx.update_layout(self._layout)
        self.text_ctx.show_layout(self._layout)

    def draw_image(self, ctx, x, y, image_file):
        ctx.save()
        ctx.translate(x, y)
        pixbuf = gtk.gdk.pixbuf_new_from_file(image_file)
        format = cairo.FORMAT_RGB24
        if pixbuf.get_has_alpha():
            format = cairo.FORMAT_ARGB32

        iw = pixbuf.get_width()
        ih = pixbuf.get_height()
        image = cairo.ImageSurface(format, iw, ih)
        image = ctx.set_source_pixbuf(pixbuf, 0, 0)

        ctx.paint()
        puxbuf = None
        image = None
        ctx.restore()
        ctx.clip()


def run(Widget):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    window.set_size_request(400, 400)
    widget = Widget()
    widget.show()
    window.add(widget)
    window.present()
    gtk.main()

if __name__ == '__main__':
    run(Speedometer)
    
