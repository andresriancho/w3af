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

import gtk
from . import helpers, entries
from core.controllers.w3afException import w3afException

# Profile objects
from core.data.profile.profile import profile as profile

import cgi


class ProfileList(gtk.TreeView):
    '''A list showing all the profiles.

    @param w3af: The main core class.
    @param initial: The profile to start

    @author: Facundo Batista <facundobatista =at= taniquetil.com.ar>
    '''
    def __init__(self, w3af, initial=None):
        self.w3af = w3af

        super(ProfileList,self).__init__()
        
        # A list to store the several "initial" profiles
        self._parameter_profile = initial
        
        self.loadProfiles(selected=initial)

        # callbacks for right button and select
        self.connect('button-press-event', self._changeAtempt)
        self.connect('button-release-event', self._popupMenu)
        self.connect('cursor-changed', self._useProfile)
        self._rightButtonMenu = None
        
        # create a TreeViewColumn for the text
        tvcolumn = gtk.TreeViewColumn(_('Profiles'))
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.add_attribute(cell, 'markup', 0)
        self.append_column(tvcolumn)

        # put the tooltips if supported
        if hasattr(self, "set_tooltip_column"):
            self.set_tooltip_column(1)

        # here we keep the info exactly like the core, to change it
        # easily to it
        self.pluginsConfigs = {None:{}}
        self.origActPlugins = sorted(self.w3af.mainwin.pcbody.getActivatedPlugins())

        self.show()

    def loadProfiles(self, selected=None):
        '''Load the profiles.

        @param selected: which profile is already selected.
        '''
        # create the ListStore, with the info listed below
        liststore = gtk.ListStore(str, str, str, int, str)

        # we will keep the profile instances here
        self.profile_instances = {None:None}

        # build the list with the profiles name, description, profile_instance
        instance_list, invalid_profiles = self.w3af.getProfileList()
        tmpprofiles = []
        for profile_obj in instance_list:
            nom = profile_obj.getName()
            desc = profile_obj.getDesc()
            tmpprofiles.append((nom, desc, profile_obj))
        
        # Also add to that list the "selected" profile, that was specified by the user with the
        # "-p" parameter when executing w3af
        if self._parameter_profile:
            try:
                profile_obj = profile(self._parameter_profile)
            except w3afException:
                raise ValueError(_("The profile %r does not exists!") % self._parameter_profile)
            else:
                nom = profile_obj.getName()
                desc = profile_obj.getDesc()
                
                # I don't want to add duplicates, so I perform this test:
                add_to_list = True
                for nom_tmp, desc_tmp, profile_tmp in tmpprofiles:
                    if nom_tmp == nom and desc_tmp == desc:
                        add_to_list = False
                        break
                
                if add_to_list:
                    tmpprofiles.append((nom, desc, profile_obj))
        
        # Create the liststore using a specially sorted list, what I basically want is the
        # empty profile at the beginning of the list, and the rest sorted in alpha order
        tmpprofiles = sorted(tmpprofiles)
        tmpprofiles_special_order = []
        for nom, desc, profile_obj in tmpprofiles:
            if nom == 'empty_profile':
                tmpprofiles_special_order.insert( 0 , (nom, desc, profile_obj))
            else:
                tmpprofiles_special_order.append( (nom, desc, profile_obj))
        
        # And now create the liststore and the internal dict
        for nom, desc, profile_obj in tmpprofiles_special_order:
            prfid = str(id(profile_obj))
            self.profile_instances[prfid] = profile_obj
            liststore.append([nom, desc, prfid, 0, nom])
        
        # set this liststore
        self.liststore = liststore
        self.set_model(liststore)

        # select the indicated one
        self.selectedProfile = None
        if selected is None:
            self.set_cursor(0)
            self._useProfile()
        else:
            for i, (nom, desc, prfid, changed, perm) in enumerate(liststore):
                if selected == self.profile_instances[ prfid ].get_profile_file() or\
                selected == self.profile_instances[ prfid ].getName():
                    self.set_cursor(i)
                    self._useProfile()
                    break
            else:
                raise ValueError(_("Unexpected problem while loading profile %r (duplicated profile name?).") % selected)
                
        # Now that we've finished loading everything, show the invalid profiles in a nice pop-up window
        if invalid_profiles:
            message = 'The following profiles are invalid and failed to load:\n'
            for i in invalid_profiles:
                message += '\n\t- ' + i
            message += '\n\nPlease click OK to continue without these profiles.'
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, message)
            dlg.run()
            dlg.destroy()
        
    def _controlDifferences(self):
        '''Returns if something is different against initial state.'''
        # Always check activation status
        nowActive = sorted(self.w3af.mainwin.pcbody.getActivatedPlugins())
        if nowActive != self.origActPlugins:
            return True

        # Check plugins config
        for ptype in self.w3af.getPluginTypes():
            for pname in self.w3af.getPluginList(ptype):
                opts = self.w3af.getPluginOptions(ptype, pname)
                if not opts:
                    continue

                # let's see if we have it (if we don't, it means
                # we never got into that plugin, therefore it's ok
                if (ptype,pname) not in self.pluginsConfigs:
                    continue

                # compare it
                savedconfig = self.pluginsConfigs[(ptype,pname)]
                for (k, origv) in savedconfig.items():
                    newv = str(opts[k])
                    if newv != origv:
                        return True

        return False

    def profileChanged(self, plugin=None, changed=None):
        '''Get executed when a plugin is changed.

        @param plugin: The plugin which changed.
        @parameter changed: Force a change.

        When executed, this check if the saved config is equal or not to the 
        original one, and enables color and buttons.
        '''
        if changed is None:
            changed = self._controlDifferences()
        
        # update boldness and info
        path = self.get_cursor()[0]
        if not path:
            return
        row = self.liststore[path]
        row[3] = changed
        if changed:
            row[0] = "<b>%s</b>" % row[4]
        else:
            row[0] = row[4]

        # update the mainwin buttons
        newstatus = self._getActionsSensitivity(path)
        self.w3af.mainwin.activateProfileActions([True]+newstatus)

    def pluginConfig(self, plugin):
        '''Gets executed when a plugin config panel is created.

        @param plugin: The plugin which will be configured.

        When executed, takes a snapshot of the original plugin configuration.
        '''
        # only stores the original one
        if (plugin.ptype,plugin.pname) in self.pluginsConfigs:
            return

        # we adapt this information to a only-options dict, as that's
        # the information that we can get later from the core
        opts = plugin.getOptions()
        realopts = {}
        for opt in opts:
            realopts[opt.getName()] = opt.getDefaultValueStr()
        self.pluginsConfigs[(plugin.ptype,plugin.pname)] = realopts

    def _changeAtempt(self, widget, event):
        '''Let the user change profile if the actual is saved.'''
        path = self.get_cursor()[0]
        if not path:
            return
        row = self.liststore[path]
        if row[3]:
            # The profile is changed
            if event.button != 1:
                return True

            # Clicked with left button
            msg = _("Do you want to discard the changes in the Profile?")
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
            stayhere = dlg.run() != gtk.RESPONSE_YES
            dlg.destroy()
            if not stayhere:
                # even if it's modified, we're leaving it: when we come back, the previous
                # configuration will be loaded... so here we just unbold it and set it as 
                # not modified 
                row[0] = row[4]
                row[3] = False
                self.w3af.mainwin.sb(_("The previous profile configuration was discarded"))
            return stayhere
        return False

    def _popupMenu( self, tv, event ):
        '''Shows a menu when you right click on a plugin.
        
        @param tv: the treeview.
        @parameter event: The GTK event 
        '''
        if event.button != 3:
            return

        # don't allow right button in other widget if actual is not saved
        path = self.get_cursor()[0]
        if not path:
            return
        row = self.liststore[path]
        posic = self.get_path_at_pos(int(event.x), int(event.y))
        if posic is None:
            return
        clickpath = posic[0]
        if row[3] and clickpath != path:
            return True

        # creates the whole menu only once
        if self._rightButtonMenu is None:
            gm = gtk.Menu()
            self._rightButtonMenu = gm
        
            # the items
            e = gtk.MenuItem(_("Save configuration to profile"))
            e.connect('activate', self.saveProfile)
            gm.append(e)
            e = gtk.MenuItem(_("Save configuration to a new profile"))
            e.connect('activate', self.saveAsProfile)
            gm.append(e)
            e = gtk.MenuItem(_("Revert to saved profile state"))
            e.connect('activate', self.revertProfile)
            gm.append(e)
            e = gtk.MenuItem(_("Delete this profile"))
            e.connect('activate', self.deleteProfile)
            gm.append(e)
            gm.show_all()
        else:
            gm = self._rightButtonMenu
        
        (path, column) = tv.get_cursor()
        # Is it over a plugin name ?
        if path is not None and len(path) == 1:
            # Enable/disable the options in function of state
            newstatus = self._getActionsSensitivity(path)
            children = gm.get_children()
            for child,stt in zip(children, newstatus):
                child.set_sensitive(stt)
                
            gm.popup( None, None, None, event.button, event.time)

    def _getActionsSensitivity(self, path):
        '''Returns which actions must be activated or not

        @param path: where the cursor is located
        @return: four booleans indicating the state for each option
        '''
        vals = []
        row = self.liststore[path]

        # save: enabled if it's modified
        vals.append(row[3])
        # save as: always enabled
        vals.append(True)
        # revert: enabled if it's modified
        vals.append(row[3])
        # delete: enabled
        vals.append(True)

        return vals

    def _getProfile(self):
        '''Gets the actual profile instance.

        @return: The profile instance for the actual cursor position.
        '''
        (path, focus) = self.get_cursor()
        if path is None:
            return None
        prfid = self.liststore[path][2]
        profile_obj = self.profile_instances[prfid]
        return profile_obj

    def _getProfileName(self):
        '''Gets the actual profile name.

        @return: The profile name for the actual cursor position.
        '''
        profile_obj = self._getProfile()
        if profile_obj is None:
            return None
        return profile_obj.getName()

    def _useProfile(self, widget=None):
        '''Uses the selected profile.'''
        profile_obj = self._getProfile()
        profileName = self._getProfileName()
        if profileName == self.selectedProfile:
            return
        self.selectedProfile = profileName

        try:
            self.w3af.useProfile(profile_obj.get_profile_file())
        except w3afException, w3:
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, str(w3) )
            dlg.run()
            dlg.destroy()
            return

        if profile_obj is not None:
            profdesc = profile_obj.getDesc()
        else:
            profdesc = None
        self.w3af.mainwin.pcbody.reload(profdesc)

        # get the activated plugins
        self.origActPlugins = self.w3af.mainwin.pcbody.getActivatedPlugins()

        # update the mainwin buttons
        path = self.get_cursor()[0]
        newstatus = self._getActionsSensitivity(path)
        self.w3af.mainwin.activateProfileActions(newstatus)

    def newProfile(self, widget=None):
        '''Creates a new profile.'''
        # ask for new profile info
        dlg = entries.EntryDialog(_("New profile"), gtk.STOCK_NEW, [_("Name:"), _("Description:")])
        dlg.run()
        dlgResponse = dlg.inputtexts
        dlg.destroy()
        if dlgResponse is None:
            return

        # use the empty profile
        try:
            self.w3af.useProfile(None)
        except w3afException, w3:
            dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_OK, str(w3) )
            dlg.run()
            dlg.destroy()
            return
        self.w3af.mainwin.pcbody.reload(None)

        # save it
        filename, description = dlgResponse
        filename = cgi.escape(filename)
        try:
            profile_obj = helpers.coreWrap(self.w3af.saveCurrentToNewProfile, filename , description)
        except w3afException:
            #FIXME: This message should be more descriptive
            self.w3af.mainwin.sb(_("Problem hit!"))
            return
        self.w3af.mainwin.sb(_("New profile created"))
        self.loadProfiles(selected=profile_obj.get_profile_file())

        # get the activated plugins
        self.origActPlugins = self.w3af.mainwin.pcbody.getActivatedPlugins()

        # update the mainwin buttons
        path = self.get_cursor()[0]
        newstatus = self._getActionsSensitivity(path)
        self.w3af.mainwin.activateProfileActions(newstatus)

    def saveProfile(self, widget=None):
        '''Saves the selected profile.'''
        profile_obj = self._getProfile()
        if not self.w3af.mainwin.saveStateToCore(relaxedTarget=True):
            return
        self.w3af.saveCurrentToProfile( profile_obj.getName(), profileDesc=profile_obj.getDesc() )
        self.w3af.mainwin.sb(_("Profile saved"))
        path = self.get_cursor()[0]
        row = self.liststore[path]
        row[0] = row[4]
        row[3] = False

    def saveAsProfile(self, widget=None):
        '''Copies the selected profile.'''
        if not self.w3af.mainwin.saveStateToCore(relaxedTarget=True):
            return

        dlg = entries.EntryDialog(_("Save as..."), gtk.STOCK_SAVE_AS, [_("Name:"), _("Description:")])
        dlg.run()
        dlgResponse = dlg.inputtexts
        dlg.destroy()
        if dlgResponse is not None:
            filename,description = dlgResponse
            filename = cgi.escape(filename)
            try:
                profile_obj = helpers.coreWrap(self.w3af.saveCurrentToNewProfile, filename , description)
            except w3afException:
                self.w3af.mainwin.sb(_("There was a problem saving the profile!"))
                return
            self.w3af.mainwin.sb(_("New profile created"))
            self.loadProfiles(selected=profile_obj.get_profile_file())

    def revertProfile(self, widget=None):
        '''Reverts the selected profile to its saved state.'''
        msg = _("Do you really want to discard the changes in the the profile and load the previous saved configuration?")
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()

        if opt == gtk.RESPONSE_YES:
            self.selectedProfile = -1
            path = self.get_cursor()[0]
            row = self.liststore[path]
            row[0] = row[4]
            row[3] = False
            self._useProfile()
            self.w3af.mainwin.sb(_("The profile configuration was reverted to its last saved state"))

    def deleteProfile(self, widget=None):
        '''Deletes the selected profile.'''
        profile_obj = self._getProfile()

        msg = _("Do you really want to DELETE the profile '%s'?") % profile_obj.getName()
        dlg = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO, msg)
        opt = dlg.run()
        dlg.destroy()

        if opt == gtk.RESPONSE_YES:
            # Special case to handle the parameter profile
            if profile_obj.get_profile_file() == self._parameter_profile:
                self._parameter_profile = None

            self.w3af.removeProfile( profile_obj.get_profile_file() )
            self.w3af.mainwin.sb(_("The profile was deleted"))
            self.loadProfiles()
