'''
profiles.py

Copyright 2007 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''

import pygtk
pygtk.require('2.0')
import gtk


class ProfileList(gtk.TreeView):
    '''A list showing all the profiles.

    @param w3af: The main core class.

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af):
        self.w3af = w3af

        # create the ListStore, with the plugin name
        self.liststore = gtk.ListStore(str, str, str)

        # we will keep the profile instances here
        self.profile_instances = {None:None}

        # build the list with the profiles name, description, and id
        self.liststore.append(["Empty profile", "Clean profile with nothing configured", None])
        for profile in sorted(w3af.getProfileList()):
            nom = profile.getName()
            desc = profile.getDesc()
            prfid = str(id(profile))
            self.profile_instances[prfid] = profile
            self.liststore.append([nom, desc, prfid])

        # create the TreeView using liststore
        super(ProfileList,self).__init__(self.liststore)
        
        # callbacks for right button and select
        self.connect('button-release-event', self._popupMenu)
        self.connect('cursor-changed', self._useProfile)
        
        # create a TreeViewColumn for the text
        tvcolumn = gtk.TreeViewColumn('Profiles')
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'text', 0)
        self.append_column(tvcolumn)

        # put the tooltips
        self.set_tooltip_column(1)

        # FIXME: que los botones se apaguen y prendan si hay algo para 
        #    grabar (en funcion de que este modificado o no)
        #    save as  (estando seleccionado
        #    revert (idem grabar)
        #    delete  (idem save as)
        # FIXME: Que el primero, el default arranque "seleccionado"
        self.show()
        
    def _popupMenu( self, tv, event ):
        '''Shows a menu when you right click on a plugin.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button != 3:
            return

        # FIXME: que estos esten prendidos o apagados como correspondan
        print "FIXME: this should present a menu with the following options:"
        print "  Save this configuration"
        print "  Revert to saved profile state"
        print "  Save this profile to a new one"
        print "  Delete this profile"

#        (path, column) = tv.get_cursor()
#        # Is it over a plugin name ?
#        if path != None and len(path) == 1:
#            # Get the information about the click
#            plugin = self.getPluginInstance(path)
#            pname = self.liststore[path][0]
#            
#            # Ok, now I show the popup menu !
#            # Create the popup menu
#            gm = gtk.Menu()
#            
#            # And the items
#            e = gtk.MenuItem("Edit plugin...")
#            e.connect('activate', editPlugin, pname, 'attack' )
#            gm.append( e )
#            e = gtk.MenuItem("Configure plugin...")
#            e.connect('activate', self._configureExploit, plugin, pname)
#            gm.append( e )
#            gm.show_all()
#            
#            gm.popup( None, None, None, event.button, event.time)

    def _getProfileName(self):
        '''Gets the actual profile instance.

        @return: The profile instance for the actual cursor position.
        '''
        (path, focus) = self.get_cursor()
        prfid = self.liststore[path][2]
        profile = self.profile_instances[prfid]
        if profile is None:
            return None
        return profile.getName()

    def _useProfile(self, widget):
        '''Uses the selected profile.'''
        profile = self._getProfileName()
        self.w3af.useProfile(profile)
        self.w3af.mainwin.pcbody.reload()

        print "FIXME: use profile", profile

    def saveProfile(self):
        '''Saves the selected profile.'''
        profile = self._getProfileName()
        print "FIXME: save profile", profile

    def saveAsProfile(self):
        '''Copies the selected profile.'''
        profile = self._getProfileName()
        print "FIXME: save as profile", profile

    def revertProfile(self):
        '''Reverts the selected profile to its saved state.'''
        profile = self._getProfileName()
        print "FIXME: revert profile", profile

    def deleteProfile(self):
        '''Deletes the selected profile.'''
        profile = self._getProfileName()
        print "FIXME: delete profile", profile
