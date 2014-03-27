"""
rendering.py

Copyright 2010 Andres Riancho

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

RENDERING_ENGINES = {'webkit': False, 'gtkhtml2': False, 'moz': False}

try:
    import webkit
    RENDERING_ENGINES['webkit'] = True
except Exception, e:
    pass

try:
    import gtkmozembed
    RENDERING_ENGINES['moz'] = True
except Exception, e:
    pass

try:
    import gtkhtml2
    #   This brings crashes like:
    #       HtmlView-ERROR **: file htmlview.c: line 1906 (html_view_insert_node): assertion
    #       failed: (node->style != NULL)
    #   TODO: Change this to True when gtkhtml2 is fixed
    RENDERING_ENGINES['gtkhtml2'] = False
except Exception, e:
    pass

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af.core.data.constants.encodings import UTF8


def getRenderingView(w3af, parentView):
    """Return RenderingView with best web engine or raise exception."""
    if RENDERING_ENGINES['webkit']:
        return WebKitRenderingView(w3af, parentView)
    if RENDERING_ENGINES['moz']:
        return MozRenderingView(w3af, parentView)
    if RENDERING_ENGINES['gtkhtml2']:
        return GtkHtmlRenderingView(w3af, parentView)
    raise BaseFrameworkException('If you want to render HTML responses, you need to install at least one of rendering engines: \
                python-webkit, python-gtkmozembed, python-gtkhtml2')


class RenderingView(gtk.VBox):
    """Rendering view."""
    def __init__(self, w3af, parentView):
        """Make object."""
        gtk.VBox.__init__(self)
        self.id = 'RenderingView'
        self.label = 'Rendered'
        self.parentView = parentView

    def show_object(self, obj):
        """Show object in view."""
        raise BaseFrameworkException('Child MUST implment a clear() method.')

    def clear(self):
        raise BaseFrameworkException('Child MUST implment a clear() method.')

    def get_object(self):
        """Return object (request or resoponse)."""
        pass

    def highlight(self, text, tag):
        """Highlight word in the text."""
        pass


class GtkHtmlRenderingView(RenderingView):
    """GtkHTML2 web engine view."""
    def __init__(self, w3af, parentView):
        """Make GtkHtmlRenderingView object."""
        super(GtkHtmlRenderingView, self).__init__(w3af, parentView)
        self._renderingWidget = gtkhtml2.View()
        swRenderedHTML = gtk.ScrolledWindow()
        swRenderedHTML.add(self._renderingWidget)
        swRenderedHTML.show_all()
        self.pack_start(swRenderedHTML)

    def show_object(self, obj):
        """Show object in view."""
        # It doesn't make sense to render something empty
        if not obj.is_text_or_html():
            return
        if not len(obj.get_body()):
            return
        mimeType = 'text/html'
        try:
            document = gtkhtml2.Document()
            document.clear()
            document.open_stream(mimeType)
            document.write_stream(obj.get_body())
            document.close_stream()
            self._renderingWidget.set_document(document)
        except ValueError, ve:
            # I get here when the mime type is an image or something that I can't display
            pass
        except Exception, e:
            print _('This is a catched exception!')
            print _('Exception:'), type(e), str(e)
            print _('I think you hitted bug #1933524 , this is mainly a gtkhtml2 problem. Please report this error here:')
            print 'https://sourceforge.net/apps/trac/w3af/newticket'

    def clear(self):
        """Clear view."""
        pass


class MozRenderingView(RenderingView):
    """Gecko web engine view."""
    def __init__(self, w3af, parentView):
        """Make MozRenderingView object."""
        super(MozRenderingView, self).__init__(w3af, parentView)
        self._renderingWidget = gtkmozembed.MozEmbed()
        print self._renderingWidget
        swRenderedHTML = gtk.ScrolledWindow()
        swRenderedHTML.add(self._renderingWidget)
        swRenderedHTML.show_all()
        self.pack_start(swRenderedHTML)

    def show_object(self, obj):
        """Show object in view."""
        mimeType = 'text/html'
        # mimeType = obj.content_type
        if obj.is_text_or_html():
            self._renderingWidget.render_data(obj.get_body(
            ), long(len(obj.get_body())), str(obj.get_uri()), mimeType)

    def clear(self):
        """Clear view."""
        pass


class WebKitRenderingView(RenderingView):
    """WebKit web engine view."""
    def __init__(self, w3af, parentView):
        """Make WebKitRenderingView object."""
        super(WebKitRenderingView, self).__init__(w3af, parentView)
        self._renderingWidget = webkit.WebView()
        # Settings
        settings = self._renderingWidget.get_settings()
        settings.set_property('auto-load-images', True)
        settings.set_property('enable-scripts', False)
        swRenderedHTML = gtk.ScrolledWindow()
        swRenderedHTML.add(self._renderingWidget)
        swRenderedHTML.show_all()
        self.pack_start(swRenderedHTML)

    def show_object(self, obj):
        """Show object in view."""
        mimeType = 'text/html'
        load_string = self._renderingWidget.load_string

        try:
            if obj.is_text_or_html():

                body = obj.get_body()
                uri = obj.get_uri().url_string
                try:
                    load_string(body, mimeType, UTF8, uri)
                except Exception:
                    load_string(repr(body), mimeType, UTF8, uri)

            else:
                raise Exception
        except Exception:
            load_string(_("Can't render response"), mimeType, 'UTF-8', 'error')

    def clear(self):
        """Clear view."""
        pass
