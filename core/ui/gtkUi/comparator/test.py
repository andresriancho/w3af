import sys
import pygtk, gtk

import comparator

class Test(object):

    def __init__(self, cont1, cont2):
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect("destroy", gtk.main_quit)
        self.window.resize(800,400)

        doc = comparator.FileDiff(cont1, cont2)

        self.window.add(doc.widget)
        self.window.show()
        gtk.main()

cont1 = open("example1.txt").read()
cont2 = open("example2.txt").read()
Test(cont1, cont2)
