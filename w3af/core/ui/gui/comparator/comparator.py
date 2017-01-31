import math
import os
import re
import difflib
import struct
import pango
import gobject
import gtk
import diffutil
import traceback

from w3af import ROOT_PATH


class FifoScheduler(object):
    """Base class with common functionality for schedulers.

    Derived classes should implement the 'get_current_task' method.
    """

    def __init__(self):
        """Create a scheduler with no current tasks.
        """
        self.tasks = []
        self.callbacks = []

    def __repr__(self):
        return "%s" % self.tasks

    def connect(self, signal, action):
        assert signal == "runnable"
        try:
            self.callbacks.index(action)
        except ValueError:
            self.callbacks.append(action)

    def add_task(self, task, atfront=0):
        """Add 'task' to the task list.

        'task' may be a function, generator or scheduler.
        The task is deemed to be finished when either it returns a
        false value or raises StopIteration.
        """
        try:
            self.tasks.remove(task)
        except ValueError:
            pass

        if atfront:
            self.tasks.insert(0, task)
        else:
            self.tasks.append(task)

        for callback in self.callbacks:
            callback(self)

    def get_current_task(self):
        try:
            return self.tasks[0]
        except IndexError:
            raise StopIteration

    def tasks_pending(self):
        return len(self.tasks) != 0

    def iteration(self):
        """Perform one iteration of the current task..

        Calls self.get_current_task() to find the current task.
        Remove task from self.tasks if it is complete.
        """
        try:
            task = self.get_current_task()
        except StopIteration:
            return 0
        try:
            ret = task()
        except StopIteration:
            pass
        except Exception:
            traceback.print_exc()
        else:
            if ret:
                return ret
        self.tasks.remove(task)
        return 0


def clamp(val, lower, upper):
    """Clamp 'val' to the inclusive range [lower,upper].
    """
    assert lower <= upper
    return min(max(val, lower), upper)


class ListItem(object):
    __slots__ = ("name", "active", "value")

    def __init__(self, s):
        a = s.split("\t")
        self.name = a.pop(0)
        self.active = int(a.pop(0))
        self.value = " ".join(a)

    def __str__(self):
        return "<%s %s %i %s>" % (self.__class__, self.name, self.active, self.value)

_pixmap_path = os.path.join(ROOT_PATH, "core/ui/gui/comparator/pixmaps")


def load_pixbuf(fname, size=0):
    """Load an image from a file as a pixbuf, with optional resizing.
    """
    image = gtk.Image()
    image.set_from_file(os.path.join(_pixmap_path, fname))
    image = image.get_pixbuf()
    if size:
        aspect = float(image.get_height()) / image.get_width()
        image = image.scale_simple(size, int(aspect * size), 2)
    return image


class Struct(object):
    """Similar to a dictionary except that members may be accessed as s.member.

    Usage:
    s = Struct(a=10, b=20, d={"cat":"dog"} )
    print s.a + s.b
    """
    def __init__(self, **args):
        self.__dict__.update(args)

    def __repr__(self):
        r = ["<"]
        for i in self.__dict__.keys():
            r.append("%s=%s" % (i, getattr(self, i)))
        r.append(">\n")
        return " ".join(r)

    def __cmp__(self, other):
        return cmp(self.__dict__, other.__dict__)


class Prefs(object):
    edit_wrap_lines = 0
    color_delete_bg = "DarkSeaGreen1"
    color_delete_fg = "Red"
    color_replace_bg = "#ddeeff"
    color_replace_fg = "Black"
    color_conflict_bg = "Pink"
    color_conflict_fg = "Black"
    color_inline_bg = "LightSteelBlue2"
    color_inline_fg = "Red"
    color_edited_bg = "gray90"
    color_edited_fg = "Black"
    regexes = [
        "CVS keywords\t0\t\$\\w+(:[^\\n$]+)?\$",
        "C++ comment\t0\t//.*",
        "C comment\t0\t/\*.*?\*/",
        "All whitespace\t0\t[ \\t\\r\\f\\v]*",
        "Leading whitespace\t0\t^[ \\t\\r\\f\\v]*",
        "Script comment\t0\t#.*",
    ]
    tab_size = 4
    supply_newline = 1
    save_encoding = 0
    ignore_blank_lines = 1
    draw_style = 2
    current_font = "Monospace 9"


MASK_SHIFT, MASK_CTRL, MASK_ALT = 1, 2, 3


class FileDiff(object):
    """Two or three way diff of text files."""

    keylookup = {gtk.keysyms.Shift_L: MASK_SHIFT,
                 gtk.keysyms.Control_L: MASK_CTRL,
                 gtk.keysyms.Alt_L: MASK_ALT,
                 gtk.keysyms.Shift_R: MASK_SHIFT,
                 gtk.keysyms.Control_R: MASK_CTRL,
                 gtk.keysyms.Alt_R: MASK_ALT}

    def _genLinkMap(self):
        da = gtk.DrawingArea()
        da.set_property("width_request", 50)
        da.set_property("visible", True)
        da.set_property("can_focus", True)
        da.set_property("has_focus", True)
        da.set_property("events", gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.KEY_PRESS_MASK | gtk.gdk.KEY_RELEASE_MASK)
        da.connect("expose-event", self.on_linkmap_expose_event)
        da.connect("scroll-event", self.on_linkmap_scroll_event)
        da.connect("button-press-event", self.on_linkmap_button_press_event)
        da.connect(
            "button-release-event", self.on_linkmap_button_release_event)
        da.connect("key-press-event", self.on_key_press_event)
        da.connect("key-release-event", self.on_key_release_event)
        return da

    def _genDiffMap(self):
        da = gtk.DrawingArea()
        da.set_property("width_request", 20)
        da.set_property("visible", True)
        da.set_property("events", gtk.gdk.BUTTON_PRESS_MASK)
        da.connect("expose-event", self.on_diffmap_expose_event)
        da.connect("button-press-event", self.on_diffmap_button_press_event)
        return da

    def _genTextView(self):
        sw = gtk.ScrolledWindow()
        sw.set_property("hscrollbar_policy", gtk.POLICY_AUTOMATIC)
        sw.set_property("vscrollbar_policy", gtk.POLICY_AUTOMATIC)
        sw.set_property("shadow_type", gtk.SHADOW_NONE)
        sw.set_property("window_placement", gtk.CORNER_TOP_LEFT)

        tv = gtk.TextView()
        tv.connect("key-press-event", self.on_key_press_event)
        tv.connect("key-release-event", self.on_key_release_event)
        tv.connect("focus-in-event", self.on_textview_focus_in_event)
        tv.connect("expose-event", self.on_textview_expose_event)
        tv.set_editable(False)

        buf = tv.get_buffer()
        buf.connect("delete-range", self.on_text_delete_range)
        buf.connect_after("insert-text", self.after_text_insert_text)
        buf.connect_after("delete-range", self.after_text_delete_range)
        buf.connect("mark-set", self.on_textbuffer_mark_set)

        sw.add(tv)
        return (sw, tv)

    def _genTodo(self):
        table = gtk.Table(3, 5)
        table.set_row_spacings(5)
        self.widget = table

        self.title0 = gtk.Label()
        table.attach(self.title0, 1, 2, 0, 1, yoptions=gtk.FILL)
        self.title1 = gtk.Label()
        table.attach(self.title1, 3, 4, 0, 1, yoptions=gtk.FILL)

        self.linkmap = self._genLinkMap()
        table.attach(
            self.linkmap, 2, 3, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)

        self.diffmap0 = self._genDiffMap()
        table.attach(
            self.diffmap0, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.diffmap1 = self._genDiffMap()
        table.attach(
            self.diffmap1, 4, 5, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
        self.diffmap = [self.diffmap0, self.diffmap1]

        (sw0, self.textview0) = self._genTextView()
        table.attach(sw0, 1, 2, 1, 2)
        (sw1, self.textview1) = self._genTextView()
        table.attach(sw1, 3, 4, 1, 2)
        self.scrolledwindow = [sw0, sw1]
        self.textview = [self.textview0, self.textview1]

        self.leftBaseBox = gtk.HBox()
        table.attach(self.leftBaseBox, 1, 2, 2, 3, yoptions=gtk.FILL)
        self.rightBaseBox = gtk.HBox()
        table.attach(self.rightBaseBox, 3, 4, 2, 3, yoptions=gtk.FILL)

        table.show_all()

    def on_idle(self):
        ret = self.scheduler.iteration()
        if self.scheduler.tasks_pending():
            return 1
        else:
            self.idle_hooked = 0
            return 0

    def on_scheduler_runnable(self, sched):
        if not self.idle_hooked:
            self.idle_hooked = 1
            gobject.idle_add(self.on_idle)

    def set_sensitive(self, how):
        self.widget.set_sensitive(how)

    def __init__(self):
        """Start up an filediff with num_panes empty contents."""
        self.idle_hooked = 0
        self.scheduler = FifoScheduler()
        self.scheduler.connect("runnable", self.on_scheduler_runnable)
        override = {}
        self._genTodo()

        self._update_regexes()
        self.keymask = 0
        self.load_font()
        self.deleted_lines_pending = -1
        self.textview_overwrite = 0
        self.textview_focussed = None
        self.textview_overwrite_handlers = [t.connect("toggle-overwrite", self.on_textview_toggle_overwrite) for t in self.textview]
        for i in range(2):
            w = self.scrolledwindow[i]
            w.get_vadjustment().connect("value-changed", self._sync_vscroll)
            w.get_hadjustment().connect("value-changed", self._sync_hscroll)
        self.linediffer = diffutil.Differ()

        # glade bug workaround
        self.linkmap.set_events(
            gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
        self.linkmap.set_double_buffered(0)  # we call paint_begin ourselves

        for text in self.textview:
            text.set_wrap_mode(Prefs.edit_wrap_lines)
            buf = text.get_buffer()

            def add_tag(name, props):
                tag = buf.create_tag(name)
                for p, v in props.items():
                    tag.set_property(p, v)
            add_tag("edited line", {"background": Prefs.color_edited_bg,
                                    "foreground": Prefs.color_edited_fg})
            add_tag("delete line", {"background": Prefs.color_delete_bg,
                                    "foreground": Prefs.color_delete_fg})
            add_tag("replace line", {"background": Prefs.color_replace_bg,
                                     "foreground": Prefs.color_replace_fg})
            add_tag("conflict line", {"background": Prefs.color_conflict_bg,
                                      "foreground": Prefs.color_conflict_fg})
            add_tag("inline line", {"background": Prefs.color_inline_bg,
                                    "foreground": Prefs.color_inline_fg})

        self.find_dialog = None
        self.last_search = None
        self.queue_draw()
        gobject.idle_add(
            lambda *args: self.load_font())  # hack around Bug 316730

    def set_left_pane(self, title, text):
        self.title0.set_markup("<b>%s</b>" % title)
        leftText = text
        buf = self.textview1.get_buffer()
        rightText = buf.get_text(*buf.get_bounds())
        self._set_internal((leftText, rightText))

    def set_right_pane(self, title, text):
        self.title1.set_markup("<b>%s</b>" % title)
        buf = self.textview0.get_buffer()
        leftText = buf.get_text(*buf.get_bounds())
        rightText = text
        self._set_internal((leftText, rightText))

    def _update_regexes(self):
        self.regexes = []
        for r in [ListItem(i) for i in Prefs.regexes]:
            if r.active:
                try:
                    self.regexes.append(
                        (re.compile(r.value + "(?m)"), r.value))
                except re.error:
                    pass

    def _update_cursor_status(self, buf):
        def update():
            it = buf.get_iter_at_mark(buf.get_insert())
            # Abbreviation for insert,overwrite so that it will fit in the status bar
            insert_overwrite = "INS,OVR".split(",")[self.textview_overwrite]
            # Abbreviation for line, column so that it will fit in the status bar
            line_column = "Ln %i, Col %i" % (
                it.get_line() + 1, it.get_line_offset() + 1)
            raise StopIteration
            yield 0
        self.scheduler.add_task(update().next)

    def on_textbuffer_mark_set(self, buffer, it, mark):
        if mark.get_name() == "insert":
            self._update_cursor_status(buffer)

    def on_textview_focus_in_event(self, view, event):
        self.textview_focussed = view
        self._update_cursor_status(view.get_buffer())

    def _after_text_modified(self, buffer, startline, sizechange):
        buffers = [t.get_buffer() for t in self.textview]
        pane = buffers.index(buffer)
        change_range = self.linediffer.change_sequence(
            pane, startline, sizechange, self._get_texts())
        for it in self._update_highlighting(change_range[0], change_range[1]):
            pass
        self.queue_draw()
        self._update_cursor_status(buffer)

    def _get_texts(self, raw=0):
        class FakeText(object):
            def __init__(self, buf, textfilter):
                self.buf, self.textfilter = buf, textfilter

            def __getslice__(self, lo, hi):
                b = self.buf
                txt = b.get_text(
                    b.get_iter_at_line(lo), b.get_iter_at_line(hi), 0)
                txt = self.textfilter(txt)
                return txt.split("\n")[:-1]

        class FakeTextArray(object):
            def __init__(self, bufs, textfilter):
                self.texts = [FakeText(b, textfilter) for b in bufs]

            def __getitem__(self, i):
                return self.texts[i]
        return FakeTextArray([t.get_buffer() for t in self.textview], [self._filter_text, lambda x:x][raw])

    def _filter_text(self, txt):
        def killit(m):
            assert m.group().count("\n") == 0
            if len(m.groups()):
                s = m.group()
                for g in m.groups():
                    if g:
                        s = s.replace(g, "")
                return s
            else:
                return ""
        try:
            for c, r in self.regexes:
                txt = c.sub(killit, txt)
        except AssertionError:
            print "Regular expression '%s' changed the number of lines in" \
                  "the file. Comparison will be incorrect. " % r
        return txt

    def after_text_insert_text(self, buffer, it, newtext, textlen):
        lines_added = newtext.count("\n")
        starting_at = it.get_line() - lines_added
        self._after_text_modified(buffer, starting_at, lines_added)

    def after_text_delete_range(self, buffer, it0, it1):
        starting_at = it0.get_line()
        assert self.deleted_lines_pending != -1
        self._after_text_modified(
            buffer, starting_at, -self.deleted_lines_pending)
        self.deleted_lines_pending = -1

    def load_font(self):
        fontdesc = pango.FontDescription(Prefs.current_font)
        context = self.textview0.get_pango_context()
        metrics = context.get_metrics(fontdesc, context.get_language())
        self.pixels_per_line = (
            metrics.get_ascent() + metrics.get_descent()) / 1024
        self.pango_char_width = metrics.get_approximate_char_width()
        tabs = pango.TabArray(10, 0)
        tab_size = Prefs.tab_size
        for i in range(10):
            tabs.set_tab(
                i, pango.TAB_LEFT, i * tab_size * self.pango_char_width)
        for i in range(2):
            self.textview[i].modify_font(fontdesc)
            self.textview[i].set_tabs(tabs)
        self.linkmap.queue_draw()
        self.pixbuf_apply0 = load_pixbuf(
            "button_apply0.xpm", self.pixels_per_line)
        self.pixbuf_apply1 = load_pixbuf(
            "button_apply1.xpm", self.pixels_per_line)
        self.pixbuf_delete = load_pixbuf(
            "button_delete.xpm", self.pixels_per_line)
        self.pixbuf_copy0 = load_pixbuf(
            "button_copy0.xpm", self.pixels_per_line)
        self.pixbuf_copy1 = load_pixbuf(
            "button_copy1.xpm", self.pixels_per_line)

    def on_key_press_event(self, obj, event):
        x = self.keylookup.get(event.keyval, 0)
        if self.keymask | x != self.keymask:
            self.keymask |= x
            a = self.linkmap.get_allocation()
            w = self.pixbuf_copy0.get_width()
            self.linkmap.queue_draw_area(0, 0, w, a[3])
            self.linkmap.queue_draw_area(a[2] - w, 0, w, a[3])

    def on_key_release_event(self, obj, event):
        x = self.keylookup.get(event.keyval, 0)
        if self.keymask & ~x != self.keymask:
            self.keymask &= ~x
            a = self.linkmap.get_allocation()
            w = self.pixbuf_copy0.get_width()
            self.linkmap.queue_draw_area(0, 0, w, a[3])
            self.linkmap.queue_draw_area(a[2] - w, 0, w, a[3])

    def on_text_delete_range(self, buffer, it0, it1):
        text = buffer.get_text(it0, it1, 0)
        self.deleted_lines_pending = text.count("\n")

    def on_textview_toggle_overwrite(self, view):
        self.textview_overwrite = not self.textview_overwrite
        for v, h in zip(self.textview, self.textview_overwrite_handlers):
            v.disconnect(h)
            if v != view:
                v.emit("toggle-overwrite")
        self.textview_overwrite_handlers = [t.connect("toggle-overwrite", self.on_textview_toggle_overwrite) for t in self.textview]
        self._update_cursor_status(view.get_buffer())

    def _set_internal(self, texts):
        self.linediffer.diffs = [[], []]
        self.queue_draw()
        buffers = [t.get_buffer() for t in self.textview]
        panetext = ["\n"] * 2
        for i, text in enumerate(texts):
            buffers[i].set_text(text)
            panetext[i] = text
        panetext = [self._filter_text(p) for p in panetext]
        lines = map(lambda x: x.split("\n"), panetext)
        self.linediffer.set_sequences_iter(*lines)
        self.queue_draw()
        lenseq = [len(d) for d in self.linediffer.diffs]
        self.scheduler.add_task(
            self._update_highlighting((0, lenseq[0]), (0, lenseq[1])).next)

    def _update_highlighting(self, range0, range1):
        buffers = [t.get_buffer() for t in self.textview]
        for b in buffers:
            taglist = ["delete line", "conflict line",
                       "replace line", "inline line"]
            table = b.get_tag_table()
            for tagname in taglist:
                tag = table.lookup(tagname)
                b.remove_tag(tag, b.get_start_iter(), b.get_end_iter())
        for chunk in self.linediffer.all_changes(self._get_texts()):
            for i, c in enumerate(chunk):
                if c and c[0] == "replace":
                    bufs = buffers[1], buffers[i * 2]
                    #tags = [b.get_tag_table().lookup("replace line") for b in bufs]
                    starts = [b.get_iter_at_line(
                        l) for b, l in zip(bufs, (c[1], c[3]))]
                    text1 = "\n".join(self._get_texts(
                        raw=1)[1][c[1]:c[2]]).encode("utf16")
                    text1 = struct.unpack("%iH" % (len(text1) / 2), text1)[1:]
                    textn = "\n".join(self._get_texts(
                        raw=1)[i * 2][c[3]:c[4]]).encode("utf16")
                    textn = struct.unpack("%iH" % (len(textn) / 2), textn)[1:]
                    matcher = difflib.SequenceMatcher(None, text1, textn)
                    #print "<<<\n%s\n---\n%s\n>>>" % (text1, textn)
                    tags = [b.get_tag_table().lookup(
                        "inline line") for b in bufs]
                    back = (0, 0)
                    for o in matcher.get_opcodes():
                        if o[0] == "equal":
                            if (o[2] - o[1] < 3) or (o[4] - o[3] < 3):
                                back = o[4] - o[3], o[2] - o[1]
                            continue
                        for i in range(2):
                            s, e = starts[i].copy(), starts[i].copy()
                            s.forward_chars(o[1 + 2 * i] - back[i])
                            e.forward_chars(o[2 + 2 * i])
                            bufs[i].apply_tag(tags[i], s, e)
                        back = (0, 0)
                    yield 1

    def on_textview_expose_event(self, textview, event):
        if event.window != textview.get_window(gtk.TEXT_WINDOW_TEXT) \
                and event.window != textview.get_window(gtk.TEXT_WINDOW_LEFT):
            return
        if not hasattr(textview, "meldgc"):
            self._setup_gcs(textview)
        visible = textview.get_visible_rect()
        pane = self.textview.index(textview)
        start_line = self._pixel_to_line(pane, visible.y)
        end_line = 1 + self._pixel_to_line(pane, visible.y + visible.height)
        gc = lambda x: getattr(textview.meldgc, "gc_" + x)
        gclight = textview.get_style().bg_gc[gtk.STATE_ACTIVE]

        def draw_change(change):  # draw background and thin lines
            ypos0 = self._line_to_pixel(pane, change[1]) - visible.y
            width = event.window.get_size()[0]
            #gcline = (gclight, gcdark)[change[1] <= curline and curline < change[2]]
            gcline = gclight
            event.window.draw_line(gcline, 0, ypos0 - 1, width, ypos0 - 1)
            if change[2] != change[1]:
                ypos1 = self._line_to_pixel(pane, change[2]) - visible.y
                event.window.draw_line(gcline, 0, ypos1, width, ypos1)
                event.window.draw_rectangle(
                    gc(change[0]), 1, 0, ypos0, width, ypos1 - ypos0)
        last_change = None
        for change in self.linediffer.single_changes(pane, self._get_texts()):
            if change[2] < start_line:
                continue
            if change[1] > end_line:
                break
            # pylint: disable=E1136
            if last_change and change[1] <= last_change[2]:
                last_change = ("conflict", last_change[1],
                               max(last_change[2], change[2]))
            else:
                if last_change:
                    draw_change(last_change)
                last_change = change
            # pylint: enable=E1136
        if last_change:
            draw_change(last_change)

    def queue_draw(self, junk=None):
        self.linkmap.queue_draw()
        self.diffmap0.queue_draw()
        self.diffmap1.queue_draw()

    #
    # scrollbars
    #
    def _sync_hscroll(self, adjustment):
        if not hasattr(self, "_sync_hscroll_lock"):
            self._sync_hscroll_lock = 0
        if not self._sync_hscroll_lock:
            self._sync_hscroll_lock = 1
            adjs = map(lambda x: x.get_hadjustment(), self.scrolledwindow)
            adjs.remove(adjustment)
            val = adjustment.get_value()
            for a in adjs:
                a.set_value(val)
            self._sync_hscroll_lock = 0

    def _sync_vscroll(self, adjustment):
        # only allow one scrollbar to be here at a time
        if not hasattr(self, "_sync_vscroll_lock"):
            self._sync_vscroll_lock = 0
        if (self.keymask & MASK_SHIFT) == 0 and not self._sync_vscroll_lock:
            self._sync_vscroll_lock = 1
            syncpoint = 0.5

            adjustments = map(
                lambda x: x.get_vadjustment(), self.scrolledwindow)
            adjustments = adjustments[:2]
            master = adjustments.index(adjustment)
            # scrollbar influence 0->1->2 or 0<-1<-2 or 0<-1->2
            others = zip(range(2), adjustments)
            del others[master]
            if master == 2:
                others.reverse()

            # the line to search for in the 'master' text
            master_y = adjustment.value + adjustment.page_size * syncpoint
            it = self.textview[master].get_line_at_y(int(master_y))[0]
            line_y, height = self.textview[master].get_line_yrange(it)
            line = it.get_line() + ((master_y - line_y) / height)

            for (i, adj) in others:
                mbegin, mend, obegin, oend = 0, self._get_line_count(
                    master), 0, self._get_line_count(i)
                # look for the chunk containing 'line'
                for c in self.linediffer.pair_changes(master, i, self._get_texts()):
                    c = c[1:]
                    if c[0] >= line:
                        mend = c[0]
                        oend = c[2]
                        break
                    elif c[1] >= line:
                        mbegin, mend = c[0], c[1]
                        obegin, oend = c[2], c[3]
                        break
                    else:
                        mbegin = c[1]
                        obegin = c[3]
                fraction = (line - mbegin) / ((mend - mbegin) or 1)
                other_line = (obegin + fraction * (oend - obegin))
                it = self.textview[i].get_buffer(
                ).get_iter_at_line(int(other_line))
                val, height = self.textview[i].get_line_yrange(it)
                val -= (adj.page_size) * syncpoint
                val += (other_line - int(other_line)) * height
                val = clamp(val, 0, adj.upper - adj.page_size)
                adj.set_value(val)

                # scrollbar influence 0->1->2 or 0<-1<-2 or 0<-1->2
                if master != 1:
                    line = other_line
                    master = 1
            self.on_linkmap_expose_event(self.linkmap, None)
            self._sync_vscroll_lock = 0

    #
    # diffmap drawing
    #
    def on_diffmap_expose_event(self, area, event):
        diffmapindex = self.diffmap.index(area)
        textindex = (0, 1)[diffmapindex]

        #TODO need height of arrow button on scrollbar - how do we get that?
        size_of_arrow = 14
        hperline = float(self.scrolledwindow[textindex].get_allocation(
        ).height - 4 * size_of_arrow) / self._get_line_count(textindex)
        if hperline > self.pixels_per_line:
            hperline = self.pixels_per_line

        scaleit = lambda x, s=hperline, o=size_of_arrow: x * s + o
        x0 = 4
        x1 = area.get_allocation().width - 2 * x0

        window = area.window
        window.clear()
        gctext = area.get_style().text_gc[0]
        if not hasattr(area, "meldgc"):
            self._setup_gcs(area)

        gc = area.meldgc.get_gc
        for c in self.linediffer.single_changes(textindex, self._get_texts()):
            assert c[0] != "equal"
            outline = True
            if Prefs.ignore_blank_lines:
                c1, c2 = self._consume_blank_lines(
                    self._get_texts()[textindex][c[1]:c[2]])
                if (c1 or c2) and (c[1] + c1 == c[2] - c2):
                    outline = False
            s, e = [int(x) for x in (math.floor(
                scaleit(c[1])), math.ceil(scaleit(c[2] + (c[1] == c[2]))))]
            window.draw_rectangle(gc(c[0]), 1, x0, s, x1, e - s)
            if outline:
                window.draw_rectangle(gctext, 0, x0, s, x1, e - s)

    def on_diffmap_button_press_event(self, area, event):
        #TODO need gutter of scrollbar - how do we get that?
        if event.button == 1:
            size_of_arrow = 14
            diffmapindex = self.diffmap.index(area)
            index = (0, 1)[diffmapindex]
            height = area.get_allocation().height
            fraction = (
                event.y - size_of_arrow) / (height - 3.75 * size_of_arrow)
            adj = self.scrolledwindow[index].get_vadjustment()
            val = fraction * adj.upper - adj.page_size / 2
            upper = adj.upper - adj.page_size
            adj.set_value(max(min(upper, val), 0))
            return 1
        return 0

    def _get_line_count(self, index):
        """Return the number of lines in the buffer of textview 'text'"""
        return self.textview[index].get_buffer().get_line_count()

    def _line_to_pixel(self, pane, line):
        it = self.textview[pane].get_buffer().get_iter_at_line(line)
        return self.textview[pane].get_iter_location(it).y

    def _pixel_to_line(self, pane, pixel):
        return self.textview[pane].get_line_at_y(pixel)[0].get_line()

    def next_diff(self, direction):
        adjs = map(lambda x: x.get_vadjustment(), self.scrolledwindow)
        curline = self._pixel_to_line(
            1, int(adjs[1].value + adjs[1].page_size / 2))
        c = None
        if direction == gtk.gdk.SCROLL_DOWN:
            for c in self.linediffer.single_changes(1, self._get_texts()):
                assert c[0] != "equal"
                c1, c2 = self._consume_blank_lines(
                    self._get_texts()[1][c[1]:c[2]])
                if c[1] + c1 == c[2] - c2:
                    continue
                if c[1] > curline + 1:
                    break
        else:  # direction == gtk.gdk.SCROLL_UP
            for chunk in self.linediffer.single_changes(1, self._get_texts()):
                c1, c2 = self._consume_blank_lines(
                    self._get_texts()[1][chunk[1]:chunk[2]])
                if chunk[1] + c1 == chunk[2] - c2:
                    continue
                if chunk[2] < curline:
                    c = chunk
                elif c:
                    break
        if c:
            if c[2] - c[1]:  # no range, use other side
                l0, l1 = c[1], c[2]
                aidx = 1
                a = adjs[aidx]
            else:
                l0, l1 = c[3], c[4]
                aidx = c[5]
                a = adjs[aidx]
            want = 0.5 * (self._line_to_pixel(
                aidx, l0) + self._line_to_pixel(aidx, l1) - a.page_size)
            want = clamp(want, 0, a.upper - a.page_size)
            a.set_value(want)

    def _setup_gcs(self, area):
        assert area.window
        gcd = area.window.new_gc()
        gcd.set_rgb_fg_color(gtk.gdk.color_parse(Prefs.color_delete_bg))
        gcc = area.window.new_gc()
        gcc.set_rgb_fg_color(gtk.gdk.color_parse(Prefs.color_replace_bg))
        gce = area.window.new_gc()
        gce.set_rgb_fg_color(gtk.gdk.color_parse(Prefs.color_edited_bg))
        gcx = area.window.new_gc()
        gcx.set_rgb_fg_color(gtk.gdk.color_parse(Prefs.color_conflict_bg))
        area.meldgc = Struct(
            gc_delete=gcd, gc_insert=gcd, gc_replace=gcc, gc_conflict=gcx)
        area.meldgc.get_gc = lambda p: getattr(area.meldgc, "gc_" + p)

    def _consume_blank_lines(self, txt):
        lo, hi = 0, 0
        for l in txt:
            if len(l) == 0:
                lo += 1
            else:
                break
        for l in txt[lo:]:
            if len(l) == 0:
                hi += 1
            else:
                break
        return lo, hi

    #
    # linkmap drawing
    #
    def on_linkmap_expose_event(self, area, event):
        window = area.window
        # not mapped?
        if not window:
            return
        if not hasattr(area, "meldgc"):
            self._setup_gcs(area)
        gctext = area.get_style().bg_gc[gtk.STATE_ACTIVE]

        alloc = area.get_allocation()
        (wtotal, htotal) = alloc.width, alloc.height
        window.begin_paint_rect((0, 0, wtotal, htotal))
        window.clear()

        # gain function for smoothing
        #TODO cache these values
        bias = lambda x, g: math.pow(x, math.log(g) / math.log(0.5))

        def gain(t, g):
            if t < 0.5:
                return bias(2 * t, 1 - g) / 2.0
            else:
                return (2 - bias(2 - 2 * t, 1 - g)) / 2.0
        f = lambda x: gain(x, 0.85)

        if self.keymask & MASK_SHIFT:
            pix0 = self.pixbuf_delete
            pix1 = self.pixbuf_delete
        elif self.keymask & MASK_CTRL:
            pix0 = self.pixbuf_copy0
            pix1 = self.pixbuf_copy1
        else:  # self.keymask == 0:
            pix0 = self.pixbuf_apply0
            pix1 = self.pixbuf_apply1
        draw_style = Prefs.draw_style
        gc = area.meldgc.get_gc

        pix_start = [None] * 2
        pix_start[0] = self.textview[0].get_visible_rect().y
        pix_start[1] = self.textview[1].get_visible_rect().y

        def bounds(idx):
            return [self._pixel_to_line(idx, pix_start[idx]), self._pixel_to_line(idx, pix_start[idx] + htotal)]
        visible = [None] + bounds(0) + bounds(1)

        for c in self.linediffer.pair_changes(0, 1, self._get_texts()):
            if Prefs.ignore_blank_lines:
                c1, c2 = self._consume_blank_lines(
                    self._get_texts()[0][c[1]:c[2]])
                c3, c4 = self._consume_blank_lines(
                    self._get_texts()[1][c[3]:c[4]])
                c = c[0], c[1] + c1, c[2] - c2, c[3] + c3, c[4] - c4
                if c[1] == c[2] and c[3] == c[4]:
                    continue

            assert c[0] != "equal"
            if c[2] < visible[1] and c[4] < visible[3]:  # find first visible chunk
                continue
            elif c[1] > visible[2] and c[3] > visible[4]:  # we've gone past last visible
                break

            f0, f1 = [self._line_to_pixel(0, l) - pix_start[0]
                      for l in c[1:3]]
            t0, t1 = [self._line_to_pixel(1, l) - pix_start[1]
                      for l in c[3:5]]

            if f0 == f1:
                f0 -= 2
                f1 += 2
            if t0 == t1:
                t0 -= 2
                t1 += 2
            if draw_style > 0:
                n = (1, 9)[draw_style - 1]
                points0 = []
                points1 = []
                for t in map(lambda x: float(x) / n, range(n + 1)):
                    points0.append(
                        (int(t * wtotal), int((1 - f(t)) * f0 + f(t) * t0)))
                    points1.append((int((
                        1 - t) * wtotal), int(f(t) * f1 + (1 - f(t)) * t1)))

                points = points0 + points1 + [points0[0]]

                window.draw_polygon(gc(c[0]), 1, points)
                window.draw_lines(gctext, points0)
                window.draw_lines(gctext, points1)
            else:
                w = wtotal
                p = self.pixbuf_apply0.get_width()
                window.draw_polygon(
                    gctext, 0, ((-1, f0), (p, f0), (p, f1), (-1, f1)))
                window.draw_polygon(gctext, 0, (
                    (w + 1, t0), (w - p, t0), (w - p, t1), (w + 1, t1)))
                points0 = (0, f0), (0, t0)
                window.draw_line(
                    gctext, p, (f0 + f1) / 2, w - p, (t0 + t1) / 2)

            x = wtotal - self.pixbuf_apply0.get_width()
            if c[0] == "insert":
                window.draw_pixbuf(
                    gctext, pix1, 0, 0, x, points0[-1][1], -1, -1, 0, 0, 0)
            elif c[0] == "delete":
                window.draw_pixbuf(
                    gctext, pix0, 0, 0, 0, points0[0][1], -1, -1, 0, 0, 0)
            else:  # replace
                window.draw_pixbuf(
                    gctext, pix0, 0, 0, 0, points0[0][1], -1, -1, 0, 0, 0)
                window.draw_pixbuf(
                    gctext, pix1, 0, 0, x, points0[-1][1], -1, -1, 0, 0, 0)

        # allow for scrollbar at end of textview
        mid = 0.5 * self.textview0.get_allocation().height
        window.draw_line(
            gctext, int(.25 * wtotal), int(mid), int(.75 * wtotal), int(mid))
        window.end_paint()

    def on_linkmap_scroll_event(self, area, event):
        self.next_diff(event.direction)

    def on_linkmap_button_press_event(self, area, event):
        if event.button == 1:
            self.focus_before_click = None
            for t in self.textview:
                if t.is_focus():
                    self.focus_before_click = t
                    break
            area.grab_focus()
            self.mouse_chunk = None
            alloc = area.get_allocation()
            (wtotal, htotal) = alloc.width, alloc.height
            pix_width = self.pixbuf_apply0.get_width()
            pix_height = self.pixbuf_apply0.get_height()
            if self.keymask == MASK_CTRL:  # hack
                pix_height *= 2

            # quick reject are we near the gutter?
            if event.x < pix_width:
                side = 0
                rect_x = 0
            elif event.x > wtotal - pix_width:
                side = 1
                rect_x = wtotal - pix_width
            else:
                return  1
            src = side
            dst = 1 - side
            adj = self.scrolledwindow[src].get_vadjustment()
            func = lambda c: self._line_to_pixel(src, c[1]) - adj.value

            for c in self.linediffer.pair_changes(src, dst, self._get_texts()):
                if Prefs.ignore_blank_lines:
                    c1, c2 = self._consume_blank_lines(
                        self._get_texts()[src][c[1]:c[2]])
                    c3, c4 = self._consume_blank_lines(
                        self._get_texts()[dst][c[3]:c[4]])
                    c = c[0], c[1] + c1, c[2] - c2, c[3] + c3, c[4] - c4
                    if c[1] == c[2] and c[3] == c[4]:
                        continue
                if c[0] == "insert":
                    continue
                h = func(c)
                if h < 0:  # find first visible chunk
                    continue
                elif h > htotal:  # we've gone past last visible
                    break
                elif h < event.y and event.y < h + pix_height:
                    self.mouse_chunk = (
                        (src, dst), (rect_x, h, pix_width, pix_height), c)
                    break
            #print self.mouse_chunk
            return 1
        elif event.button == 2:
            self.linkmap_drag_coord = event.x
        return 0

    def on_linkmap_button_release_event(self, area, event):
        if event.button == 1:
            if self.focus_before_click:
                self.focus_before_click.grab_focus()
                self.focus_before_click = None
            if self.mouse_chunk:
                (src, dst), rect, chunk = self.mouse_chunk
                # check we're still in button
                inrect = lambda p, r: ((r[0] < p.x) and (p.x < r[0] + r[2]) and (r[1] < p.y) and (p.y < r[1] + r[3]))
                if inrect(event, rect):
                    # gtk tries to jump back to where the cursor was unless we move the cursor
                    self.textview[src].place_cursor_onscreen()
                    self.textview[dst].place_cursor_onscreen()
                    chunk = chunk[1:]
                    self.mouse_chunk = None

                    if self.keymask & MASK_SHIFT:  # delete
                        b = self.textview[src].get_buffer()
                        b.delete(b.get_iter_at_line(
                            chunk[0]), b.get_iter_at_line(chunk[1]))
                    elif self.keymask & MASK_CTRL:  # copy up or down
                        b0 = self.textview[src].get_buffer()
                        t0 = b0.get_text(b0.get_iter_at_line(
                            chunk[0]), b0.get_iter_at_line(chunk[1]), 0)
                        b1 = self.textview[dst].get_buffer()
                        if event.y - rect[1] < 0.5 * rect[3]:  # copy up
                            b1.insert_with_tags_by_name(b1.get_iter_at_line(
                                chunk[2]), t0, "edited line")
                        else:  # copy down
                            b1.insert_with_tags_by_name(b1.get_iter_at_line(
                                chunk[3]), t0, "edited line")
                    else:  # replace
                        b0 = self.textview[src].get_buffer()
                        t0 = b0.get_text(b0.get_iter_at_line(
                            chunk[0]), b0.get_iter_at_line(chunk[1]), 0)
                        b1 = self.textview[dst].get_buffer()
                        b1.delete(b1.get_iter_at_line(
                            chunk[2]), b1.get_iter_at_line(chunk[3]))
                        b1.insert_with_tags_by_name(
                            b1.get_iter_at_line(chunk[2]), t0, "edited line")
            return 1
        return 0
