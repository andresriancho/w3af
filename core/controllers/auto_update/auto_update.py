'''
auto_update.py

Copyright 2011 Andres Riancho

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

from __future__ import with_statement
from datetime import datetime, date, timedelta
import os
import re
import time
import ConfigParser
import threading


class SVNError(Exception):
    pass


class SVNUpdateError(SVNError):
    pass


class SVNCommitError():
    pass


class SVNClient(object):
    '''
    Typically an abstract class. Intended to define behaviour. Not to be
    instantiated.
    SVN implementations should extend from this class.
    Implemented methods in child classes should potentially raise SVNError
    exception (or descendant) when a condition error is found.
    '''

    def __init__(self, localpath):
        self._localpath = localpath
        self._repourl = self._get_repourl()
        # Action Locker! 
        self._actionlock = threading.RLock()

    def _get_repourl(self):
        '''
        Get repo's URL. To be implemented by subclasses.
        '''
        raise NotImplementedError

    def update(self, rev=None):
        '''
        Update local repo to last revision if `rev` is None; otherwise update
        to revision `rev`.
        
        @param revision: Revision to update to. If None assume HEAD.
        '''
        raise NotImplementedError

    def commit(self):
        '''
        Commit to remote repo changes in local repo.
        '''
        raise NotImplementedError

    def status(self, path=None):
        '''
        Return a SVNFilesList object.
        
        @param localpath: Path to get the status from. If None use project's
            root.
        '''
        raise NotImplementedError

    def list(self, path_or_url=None):
        '''
        Return a SVNFilesList. Elements are tuples containing the path and
        the status for all files in `path_or_url` at the provided revision.
        '''
        raise NotImplementedError

    def diff(self, localpath, rev=None):
        '''
        Return string with the differences between `rev` and HEAD revision for
        `localpath`
        '''
        raise NotImplementedError


import pysvn

# Actions on files
FILE_UPD = 'UPD' # Updated
FILE_NEW = 'NEW' # New
FILE_DEL = 'DEL' # Removed

wcna = pysvn.wc_notify_action
pysvn_action_translator = {
    wcna.update_add: FILE_NEW,
    wcna.update_delete: FILE_DEL,
    wcna.update_update: FILE_UPD
}

# Files statuses
ST_CONFLICT = 'C'
ST_NORMAL = 'N'
ST_UNVERSIONED = 'U'
ST_MODIFIED = 'M'
ST_UNKNOWN = '?'

wcsk = pysvn.wc_status_kind
pysvn_status_translator = {
    wcsk.conflicted: ST_CONFLICT,
    wcsk.normal: ST_NORMAL,
    wcsk.unversioned: ST_UNVERSIONED,
    wcsk.modified: ST_MODIFIED
}


class w3afSVNClient(SVNClient):
    '''
    Our wrapper for pysvn.Client class.
    '''

    UPD_ACTIONS = (wcna.update_add, wcna.update_delete, wcna.update_update)

    def __init__(self, localpath):
        self._svnclient = pysvn.Client()
        # Call parent's __init__
        super(w3afSVNClient, self).__init__(localpath)
        # Set callbacks
        self._svnclient.callback_notify = self._register
        # Callback to be called when there's an error in the certificate 
        # validation and svn doesn't know what to do.
        self._svnclient.callback_ssl_server_trust_prompt = \
            lambda trustdata: (True, trustdata['failures'], True)
        # Events occurred in current action
        self._events = []
    
    def __getattribute__(self, name):
        '''
        Wrap all methods on order to be able to respond to Ctrl+C signals.
        This implementation was added due to limitations in pysvn.
        '''
        def new_meth(*args, **kwargs):
            def wrapped_meth(*args, **kwargs):
                try:
                    self._result = meth(*args, **kwargs)
                    self._exc = None
                except Exception, exc:
                    if isinstance(exc, pysvn.ClientError):
                        exc = SVNError(*exc.args)
                    self._exc = exc
            # Run wrapped_meth in new thread.
            th = threading.Thread(target=wrapped_meth, args=args,
                                  kwargs=kwargs)
            th.setDaemon(True)
            try:
                th.start()
                while th.isAlive():
                    time.sleep(0.2)
                try:
                    if self._exc:
                        raise self._exc
                    return self._result
                finally:
                    self._exc = self._result = None
            except KeyboardInterrupt:
                raise
        
        attr = SVNClient.__getattribute__(self, name)
        if callable(attr):
            meth = attr
            return new_meth
        return attr

    @property
    def URL(self):
        return self._repourl

    def update(self, rev=None):
        with self._actionlock:
            kind = pysvn.opt_revision_kind
            if rev is None:
                rev = pysvn.Revision(kind.head)
            elif type(rev) is int:
                rev = pysvn.Revision(kind.number, rev)
            else:
                rev = pysvn.Revision(kind.number, rev.number)

            self._events = []
            try:
                pysvn_rev = \
                    self._svnclient.update(self._localpath, revision=rev)[0]
            except pysvn.ClientError, ce:
                raise SVNUpdateError(*ce.args)
            
            updfiles = self._filter_files(self.UPD_ACTIONS)
            updfiles.rev = Revision(pysvn_rev.number, pysvn_rev.date)
            return updfiles

    def status(self, localpath=None):
        with self._actionlock:
            path = localpath or self._localpath
            entries = self._svnclient.status(path, recurse=False)            
            res = [(ent.path, pysvn_status_translator.get(ent.text_status,
                                          ST_UNKNOWN)) for ent in entries]
            return SVNFilesList(res)

    def list(self, path_or_url=None):
        with self._actionlock:
            if not path_or_url:
                path_or_url = self._localpath
            entries = self._svnclient.list(path_or_url, recurse=False)
            res = [(ent.path, None) for ent, _ in entries]
            return SVNFilesList(res)

    def diff(self, localpath, rev=None):
        with self._actionlock:
            path = os.path.join(self._localpath, localpath)
            # If no rev is passed then compare to HEAD
            if rev is None:
                rev = pysvn.Revision(pysvn.opt_revision_kind.head)
            tempfile = os.tempnam()
            diff_str = self._svnclient.diff(tempfile, path, revision1=rev)
            return diff_str

    def log(self, start_rev, end_rev):
        '''
        Return SVNLogList of log messages between `start_rev`  and `end_rev`
        revisions.
        
        @param start_rev: Revision object
        @param end_rev: Revision object
        '''
        with self._actionlock:
            # Expected by pysvn.Client.log method
            _startrev = pysvn.Revision(pysvn.opt_revision_kind.number, 
                               start_rev.number)
            _endrev = pysvn.Revision(pysvn.opt_revision_kind.number,
                                         end_rev.number)
            logs = (l.message for l in self._svnclient.log(self._localpath, 
                              revision_start=_startrev, revision_end=_endrev))
            rev = end_rev if (end_rev.number > start_rev.number) else start_rev
            return SVNLogList(logs, rev)

    def _get_repourl(self):
        '''
        Get repo's URL.
        '''
        svninfo = self._get_svn_info(self._localpath)
        return svninfo.URL

    def _get_svn_info(self, path_or_url):
        try:
            return self._svnclient.info2(path_or_url, recurse=False)[0][1]
        except pysvn.ClientError, ce:
            raise SVNUpdateError(*ce.args)

    def get_revision(self, local=True):
        '''
        Return Revision object.
        
        @param local: If true return local's revision data; otherwise use
        repo's.
        '''
        path_or_url = self._localpath if local else self._repourl
        _rev = self._get_svn_info(path_or_url).rev
        return Revision(_rev.number, _rev.date)

    def _filter_files(self, filterbyactions=()):
        '''
        Filter... Return files-actions
        
        @param filterby: 
        '''
        files = SVNFilesList()
        for ev in self._events:
            action = ev['action']
            if action in filterbyactions:
                path = ev['path']
                # We're not interested on reporting directories unless a 
                # 'delete' has been performed on them
                if not os.path.isdir(path) or action == wcna.update_delete:
                    files.append(path, pysvn_action_translator[action])
        return files

    def _register(self, event):
        '''
        Callback method. Registers all events taking place during this action.
        '''
        self._events.append(event)


class Revision(object):
    '''
    Our own class for revisions.
    '''

    def __init__(self, number, date):
        self._number = number
        self._date = date

    def __eq__(self, rev):
        return self._number == rev.number and \
                self._date == rev.date
    
    def __ne__(self, rev):
        return not self.__eq__(rev)

    def __lt__(self, rev):
        return self._number < rev.number

    @property
    def date(self):
        return self._date

    @property
    def number(self):
        return self._number


# Limit of lines to SVNList types. To be used in __str__ method re-definition.
PRINT_LINES = 20

class SVNList(list):
    '''
    Wrapper for python list type. It may contain the number of the current
    revision and do a custom list print. Child classes are encouraged to 
    redefine the __str__ method.
    '''

    def __init__(self, seq=(), rev=None):
        '''
        @param rev: Revision object
        '''
        list.__init__(self, seq)
        self._rev = rev
        self._sorted = True

    def _getrev(self):
        return self._rev

    def _setrev(self, rev):
        self._rev = rev

    # TODO: Cannot use *full* decorators as we're still on py2.5
    rev = property(_getrev, _setrev)

    def __eq__(self, olist):
        return list.__eq__(self, olist) and self._rev == olist.rev


class SVNFilesList(SVNList):
    '''
    Custom SVN files list holder.
    '''

    def __init__(self, seq=(), rev=None):
        SVNList.__init__(self, seq, rev)
        self._sorted = True

    def append(self, path, status):
        list.append(self, (path, status))
        self._sorted = False

    def __str__(self):
        # First sort by status
        sortfunc = lambda x, y: cmp(x[1], y[1])
        self.sort(cmp=sortfunc)
        lines, rest = self[:PRINT_LINES], max(len(self) - PRINT_LINES, 0)
        print_list = ['%s %s' % (f, s) for s, f in lines]
        if rest:
            print_list.append('and %d files more.' % rest)
        if self._rev:
            print_list.append('At revision %s.' % self._rev.number)
        return os.linesep.join(print_list)


class SVNLogList(SVNList):
    '''
    Provides a custom way to print a SVN logs list.
    '''
    def __str__(self):
        print_list = []
        if self._rev:
            print_list.append('Revision %s:' % self._rev.number)
        lines, rest = self[:PRINT_LINES], max(len(self) - PRINT_LINES, 0)
        print_list += ['%3d. %s' % (n + 1, ln) for n, ln in enumerate(lines)]
        if rest:
            print_list.append('and %d commit logs more.' % rest)
        return os.linesep.join(print_list)


# Use this class to perform svn actions on code
SVNClientClass = w3afSVNClient

# Get w3af install dir
w3afLocalPath = os.sep.join(__file__.split(os.sep)[:-4])

# Facade class. Intended to be used to interact with the module
class VersionMgr(object): #TODO: Make it singleton?
    '''
    Perform SVN w3af code update and commit. When an instance is created loads
    data from a .conf file that will be used when actions are executed.
    Also provides some callbacks as well as events to register to.
    
    Callbacks on:
        UPDATE:
            * callback_onupdate_confirm(msg)
                Return True/False
                
            * callback_onupdate_show_log(msg, log_func)
                Displays 'msg' to the user and depending on user's answer
                call 'log_func()' which returns a string with the summary of
                the commit logs from the from local revision to repo's.
            
            * callback_onupdate_error
                If an SVNError occurs this callback is called in order to the
                client class handles the error. Probably notify the user.
        COMMIT:
            {implementation pending}
    Events:
        ON_UPDATE
        ON_UPDATE_ADDED_DEP
        ON_UPDATE_CHECK
        ON_ACTION_ERROR
    '''

    # Events constants
    ON_UPDATE = 1
    ON_UPDATE_ADDED_DEP = 2
    ON_UPDATE_CHECK = 3
    ON_ACTION_ERROR = 4
    ON_COMMIT = 6
    
    # Callbacks
    callback_onupdate_confirm = None
    callback_onupdate_show_log = None
    callback_onupdate_error = None
    
    # Revision constants
    HEAD = 0
    PREVIOUS = -1
    
    def __init__(self, localpath=w3afLocalPath, log=None):
        '''
        w3af version manager class. Handles the logic concerning the 
        automatic update/commit process of the code.
        
        @param localpath: Working directory
        @param log: Default output function
        '''
        self._localpath = localpath
        
        if not log:
            import core.controllers.outputManager as om
            log = om.out.console
        self._log = log
        self._client = SVNClientClass(localpath)
        # Registered functions
        self._reg_funcs = {}
        # Startup configuration
        self._start_cfg = StartUpConfig()
        # Default events registration
        msg = 'Checking if a new version is available in our SVN repository.' \
        ' Please wait...'
        self.register(VersionMgr.ON_UPDATE_CHECK, log, msg)
        msg = 'w3af is updating from the official SVN server...'
        self.register(VersionMgr.ON_UPDATE, log, msg)
        msg = 'At least one new dependency was included in w3af. Please ' \
        'update manually.'
        self.register(VersionMgr.ON_UPDATE_ADDED_DEP, log, msg)
    
    def __getattribute__(self, name):
        def new_meth(*args, **kwargs):
            try:
                return attr(*args, **kwargs)
            except SVNError, err:
                msg = 'An error occured while updating:\n%s' % err.args
                self._notify(VersionMgr.ON_ACTION_ERROR, msg)
        attr = object.__getattribute__(self, name)            
        if callable(attr):
            return new_meth                
        return attr

    def update(self, force=False, rev=HEAD, print_result=False):
        '''
        Perform code update if necessary. Return three elems tuple with the
        SVNFilesList of the changed files, the local and the repo's revision.
        
        @param force: Force update ignoring the startup config.
        @param rev: Revision number. If != HEAD then update will be forced.
            Also, if rev equals PREVIOUS (-1) assume revision number is the
            last that worked.        
        @param print_result: If True print the result files using instance's
            log function.
        '''
        client = self._client
        rev = int(rev)
        localrev = client.get_revision(local=True)
        files = SVNFilesList(rev=localrev)        
        # If revision is not HEAD then force = True
        if rev != VersionMgr.HEAD:
            if rev == -1: # Use previous working revision
                rev = self._start_cfg.last_rev
            remrev = rev
        else:
            remrev = None

        if force or self._has_to_update():
            self._notify(VersionMgr.ON_UPDATE_CHECK)
            remrev = remrev and Revision(remrev, None) or \
                                            client.get_revision(local=False)
            # If local and repo's rev are the same => Nothing to do.
            if localrev != remrev:
                proceed_upd = True
                callback = self.callback_onupdate_confirm
                # Call callback function
                if callback:
                    proceed_upd = callback(\
                        'Your current w3af installation is r%s. Do you want ' \
                        'to update to r%s?' % (localrev.number, remrev.number))
    
                if proceed_upd:
                    self._notify(VersionMgr.ON_UPDATE)
                    # Find new deps.
                    newdeps = self._added_new_dependencies()
                    if newdeps:
                        self._notify(VersionMgr.ON_UPDATE_ADDED_DEP)
                    else:
                        # Finally do the update!
                        files = client.update(rev=remrev)
                        # Update last-rev.
                        self._start_cfg.last_rev = min(localrev, remrev)

            # Save today as last-update date and persist it.
            self._start_cfg.last_upd = date.today()
            self._start_cfg.save()

            # Before returning perform some interaction with the user if
            # requested.
            if print_result:
                self._log(str(files))

            callback = self.callback_onupdate_show_log
            # Skip downgrades
            if remrev > localrev and callback:
                log = lambda: str(self.show_summary(localrev, remrev))
                callback('Do you want to see a summary of the new code ' \
                         'commits log messages?', log)
        return (files, localrev, remrev)
    
    def show_summary(self, start_rev, end_rev):
        '''
        Return SVNLogList of log messages between `start_rev`  and `end_rev`
        revisions.
        
        @param start_rev: Start Revision object
        @param end_rev: End Revision object
        '''
        return self._client.log(start_rev, end_rev)

    def status(self, path=None):
        return self._client.status(path)

    def register(self, event, func, msg):
        '''
        Register the caller to `event` so when it takes place call its `func`
        with `msg` as param.
        '''
        self._reg_funcs[event] = (func, msg)

    def _notify(self, event, msg=''):
        '''
        Call registered function for event. If `msg` is not empty use it.
        '''
        f, _msg = self._reg_funcs.get(event)
        f(msg or _msg)

    def _added_new_dependencies(self):
        '''
        Return tuple with the dependencies added to extlib/ in the repo if
        any. Basically it compares local dirs under extlib/ to those in the
        repo as well as checks if at least a new sentence containing the 
        import keyword was added to the dependencyCheck.py file.
        '''
        #
        # Check if a new directory was added to repo's extlib
        #
        client = self._client
        ospath = os.path
        join = ospath.join
        # Find dirs in repo
        repourl = self._client.URL + '/' + 'extlib'
        # In repo we distinguish dirs from files by the dot (.) presence
        repodirs = (ospath.basename(d) for d, _ in client.list(repourl)[1:] \
                                        if ospath.basename(d).find('.') == -1)
        # Get local dirs
        extliblocaldir = join(self._localpath, 'extlib')
        extlibcontent = (join(extliblocaldir, f) for f in \
                                                os.listdir(extliblocaldir))
        localdirs = (ospath.basename(d) for d in \
                                            extlibcontent if ospath.isdir(d))
        # New dependencies
        deps = tuple(set(repodirs).difference(localdirs))

        #
        # Additional constraint: We should verify that at least an import
        # sentence was added inside a try-except block to the 
        # dependencyCheck.py files
        #
        if deps:
            depfiles = ('core/controllers/misc/dependencyCheck.py',
                        'core/ui/gtkUi/dependencyCheck.py')
            for depfile in depfiles:
                diff_str = client.diff(depfile)
                nlines = (nl[1:].strip() for nl in \
                                    diff_str.split('\n') if nl.startswith('-'))
                try_counter = 0
                for nl in nlines:
                    if nl == 'try:':
                        try_counter += 1
                    elif re.match('except.*?:', nl):
                        try_counter -= 1
                    elif nl.find('import') != -1 and try_counter:
                        return deps
        return ()
    
    def _has_to_update(self):
        '''
        Helper method that figures out if an update should be performed
        according to the startup cfg file.
        Some rules:
            1) IF auto_upd is False THEN return False
            2) IF last_upd == 'yesterday' and freq == 'D' THEN return True
            3) IF last_upd == 'two_days_ago' and freq == 'W' THEN return False.

        @return: Boolean value.
        '''
        startcfg = self._start_cfg
        # That's it!
        if not startcfg.auto_upd:
            return False
        else:        
            freq = startcfg.freq
            diff_days = max((date.today()-startcfg.last_upd).days, 0)
            
            if (freq == StartUpConfig.FREQ_DAILY and diff_days > 0) or \
                (freq == StartUpConfig.FREQ_WEEKLY and diff_days > 6) or \
                (freq == StartUpConfig.FREQ_MONTHLY and diff_days > 29):
                return True
            return False


from core.controllers.misc.homeDir import get_home_dir

class StartUpConfig(object):
    '''
    Wrapper class for ConfigParser.ConfigParser.
    Holds the configuration for the VersionMgr update/commit process
    '''

    ISO_DATE_FMT = '%Y-%m-%d'
    # Frequency constants
    FREQ_DAILY = 'D' # [D]aily
    FREQ_WEEKLY = 'W' # [W]eekly
    FREQ_MONTHLY = 'M' # [M]onthly
    # DEFAULT VALUES
    DEFAULTS = {'auto-update': 'true', 'frequency': 'D',
                'last-update': 'None', 'last-rev': 0}

    def __init__(self):
        
        self._start_cfg_file = os.path.join(get_home_dir(), 'startup.conf')
        self._start_section = 'STARTUP_CONFIG'
        self._config = ConfigParser.ConfigParser()
        configs = self._load_cfg()
        self._autoupd, self._freq, self._lastupd, self._lastrev = configs

    ### PROPERTIES #

    def _get_last_upd(self):
        '''
        Getter method.
        '''
        return self._lastupd

    def _set_last_upd(self, datevalue):
        '''
        @param datevalue: datetime.date value
        '''
        self._lastupd = datevalue
        self._config.set(self._start_section, 'last-update',
                         datevalue.isoformat())
    # Read/Write property
    # @property - Cannot use *full* decorators as we're still on py2.5
    last_upd = property(_get_last_upd, _set_last_upd)
    
    def _get_last_rev(self):
        return self._lastrev
    
    def _set_last_rev(self, rev):
        self._lastrev = rev.number
        self._config.set(self._start_section, 'last-rev', self._lastrev)
    # Read/Write property
    # @property
    last_rev = property(_get_last_rev, _set_last_rev)

    @property
    def freq(self):
        return self._freq

    @property
    def auto_upd(self):
        return self._autoupd

    ### METHODS #

    def _load_cfg(self):
        '''
        Loads configuration from config file.
        '''
        config = self._config
        startsection = self._start_section
        if not config.has_section(startsection):
            config.add_section(startsection)
            defaults = StartUpConfig.DEFAULTS
            config.set(startsection, 'auto-update', defaults['auto-update'])
            config.set(startsection, 'frequency', defaults['frequency'])
            config.set(startsection, 'last-update', defaults['last-update'])
            config.set(startsection, 'last-rev', defaults['last-rev'])

        # Read from file
        config.read(self._start_cfg_file)

        auto_upd = config.get(startsection, 'auto-update', raw=True)
        boolvals = {'false': 0, 'off': 0, 'no': 0,
                    'true': 1, 'on': 1, 'yes': 1}
        auto_upd = bool(boolvals.get(auto_upd.lower(), False))

        freq = config.get(startsection, 'frequency', raw=True).upper()
        if freq not in (StartUpConfig.FREQ_DAILY, StartUpConfig.FREQ_WEEKLY,
                        StartUpConfig.FREQ_MONTHLY):
            freq = StartUpConfig.FREQ_DAILY

        lastupdstr = config.get(startsection, 'last-update', raw=True).upper()
        # Try to parse it
        try:
            lastupd = datetime.strptime(lastupdstr, self.ISO_DATE_FMT).date()
        except:
            # Provide default value that enforces the update to happen
            lastupd = date.today() - timedelta(days=31)
        try:
            lastrev = config.getint(startsection, 'last-rev')
        except TypeError:
            lastrev = 0
        return (auto_upd, freq, lastupd, lastrev)

    def save(self):
        '''
        Saves current values to cfg file
        '''
        with open(self._start_cfg_file, 'wb') as configfile:
            self._config.write(configfile)
