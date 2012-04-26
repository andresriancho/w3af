'''
w3afCore.py

Copyright 2006 Andres Riancho

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

import os
import sys
import time
import traceback


from core.controllers.coreHelpers.progress import progress
from core.controllers.coreHelpers.status import w3af_core_status
from core.controllers.coreHelpers.profiles import w3af_core_profiles
from core.controllers.coreHelpers.plugins import w3af_core_plugins
from core.controllers.coreHelpers.target import w3af_core_target
from core.controllers.coreHelpers.strategy import w3af_core_strategy
from core.controllers.coreHelpers.fingerprint_404 import fingerprint_404_singleton
from core.controllers.threads.threadManager import threadManagerObj as tm

from core.controllers.misc.epoch_to_string import epoch_to_string
from core.controllers.misc.homeDir import (create_home_dir,
    verify_dir_has_perm, HOME_DIR)
from core.controllers.misc.number_generator import consecutive_number_generator
from core.controllers.misc.temp_dir import (create_temp_dir, remove_temp_dir,
    TEMP_DIR)
from core.controllers.w3afException import (w3afException, w3afMustStopException,
                                            w3afMustStopByUnknownReasonExc)
import core.controllers.outputManager as om
import core.data.kb.config as cf
import core.data.kb.knowledgeBase as kb
from core.data.url.xUrllib import xUrllib


class w3afCore(object):
    '''
    This is the core of the framework, it calls all plugins, handles exceptions,
    coordinates all the work, creates threads, etc.
     
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self ):
        '''
        Init some variables and files.
        Create the URI opener.
        '''
        # Create some directories
        self._home_directory()
        self._tmp_directory()
        
        # These are some of the most important moving parts in the w3afCore
        # they basically handle every aspect of the w3af framework:
        self.strategy = w3af_core_strategy( self )
        self.profiles = w3af_core_profiles( self )
        self.plugins = w3af_core_plugins( self )
        self.status = w3af_core_status()
        self.target = w3af_core_target()
        self.progress = progress()
        
        # Init some internal variables
        self._initializeInternalVariables()
        self.plugins.zero_enabled_plugins()
        
        # I init the 404 detection for the whole framework
        self.uriOpener = xUrllib()
        fp_404_db = fingerprint_404_singleton()
        fp_404_db.set_urlopener( self.uriOpener )
        
    def start(self):
        '''
        The user interfaces call this method to start the whole scanning
        process.
        This method raises almost every possible exception, so please do your
        error handling!
        '''
        om.out.debug('Called w3afCore.start()')
        
        # This will help identify the total scan time
        self._start_time_epoch = time.time()
        
        try:
            # Just in case the gtkUi / consoleUi forgot to do this...
            self.verifyEnvironment()
        except Exception, e:
            error = ('verifyEnvironment() raised an exception: "%s". This'
                ' should never happen. Are *you* user interface coder sure'
                ' that you called verifyEnvironment() *before* start() ?' % e)
            om.out.error(error)
            raise

        # Let the output plugins know what kind of plugins we're
        # using during the scan
        om.out.logEnabledPlugins(self.plugins.getAllEnabledPlugins(), 
                                 self.plugins.getAllPluginOptions())

        self.status.start()
        
        try:
            self.strategy.start()
        except MemoryError:
            msg = 'Python threw a MemoryError, this means that your'
            msg += ' OS is running very low in memory. w3af is going'
            msg += ' to stop.'
            om.out.error( msg )
            raise
        except w3afMustStopByUnknownReasonExc:
            #
            # TODO: Jan 31, 2011. Temporary workaround. Make w3af crash on
            # purpose so we can find out the *really* unknown error
            # conditions.
            #
            raise
        except w3afMustStopException, wmse:
            self._end(wmse, ignore_err=True)
            om.out.error('\n**IMPORTANT** The following error was '
             'detected by w3af and couldn\'t be resolved:\n %s\n' % wmse)
        except Exception:
            om.out.error('\nUnhandled error, traceback: %s\n' %
                         traceback.format_exc()) 
            raise
        finally:
            
            try:
                msg = 'Scan finished in %s' % epoch_to_string(self._start_time_epoch)
                om.out.information( msg )
            except:
                # In some cases we get here after a disk full exception
                # where the output manager can't even writea log message
                # to disk and/or the console. Seen this happen many times
                # in LiveCDs like Backtrack that don't have "real disk space"  
                pass
            
            self.progress.stop()
    
    def cleanup( self ):
        '''
        The GTK user interface calls this when a scan has been stopped 
        (or ended successfully) and the user wants to start a new scan.
        All data from the kb is deleted.
        
        @return: None
        '''
        # Clean all data that is stored in the kb
        kb.kb.cleanup()

        # Zero internal variables from the core
        self._initializeInternalVariables()
        
        # Not cleaning the config is a FEATURE, because the user is most likely going to start a new
        # scan to the same target, and he wants the proxy, timeout and other configs to remain configured
        # as he did it the first time.
        # reload(cf)
        
        # It is also a feature to keep the mist settings from the last run.
        # Set some defaults for the core
        #import core.controllers.miscSettings as miscSettings
        #miscSettings.miscSettings()
        
        # Not calling:
        # self.plugins.zero_enabled_plugins()
        # because I wan't to keep the selected plugins and configurations
        
    def stop( self ):
        '''
        This method is called by the user interface layer, when the user "clicks" on the stop button.
        @return: None. The stop method can take some seconds to return.
        '''
        om.out.debug('The user stopped the core.')
        self.strategy.stop()
        self.uriOpener.stop()
    
    def pause(self, pause_yes_no):
        '''
        Pauses/Un-Pauses scan.
        @parameter trueFalse: True if the UI wants to pause the scan.
        '''
        self.status.pause( pause_yes_no )
        self.strategy.pause( pause_yes_no )
        self.uriOpener.pause( pause_yes_no )

    def quit( self ):
        '''
        The user is in a hurry, he wants to exit w3af ASAP.
        '''
        self.strategy.quit()
        self.uriOpener.stop()
        
        # Now it's safe to remove the temp_dir
        remove_temp_dir()
    
    def verifyEnvironment(self):
        '''
        Checks if all parameters where configured correctly by the user,
        which in this case is a mix of w3af_console, w3af_gui and the real
        (human) user.
        '''
        if not self.plugins.initialized:
            msg = 'You must call the plugins.init_plugins() method before calling start()'
            raise w3afException( msg )
        
        if not cf.cf.getData('targets'):
            raise w3afException( 'No target URI configured.' )
            
        if not len( self.plugins.getEnabledPlugins('audit') )\
        and not len( self.plugins.getEnabledPlugins('discovery') )\
        and not len( self.plugins.getEnabledPlugins('grep') ):
            raise w3afException( 'No audit, grep or discovery plugins configured to run.' )            
    
    def _end(self, exc_inst=None, ignore_err=False):
        '''
        This method is called when the process ends normally or by an error.
        '''
        try:
            # End the xUrllib (clear the cache) and create a new one, so it can
            # be used by exploit plugins. 
            self.uriOpener.end()
            self.uriOpener = xUrllib()
            
            if exc_inst:
                om.out.debug(str(exc_inst))
            
            tm.join(joinAll=True)
            tm.stopAllDaemons()
            
            for plugin in self.plugins.plugins['grep']:
                plugin.end()
            
            # Also, close the output manager.
            om.out.endOutputPlugins()

        except Exception:
            if not ignore_err:
                raise
        
        finally:
            self.status.stop()
            self.progress.stop()
            
            # Remove all references to plugins from memory
            self.plugins.zero_enabled_plugins()            
            
            # No targets to be scanned.
            cf.cf.save('targets', [])
            
    def _home_directory(self):
        '''
        Handle all the work related to creating/managing the home directory.
        @return: None
        '''
        # Start by trying to create the home directory (linux: /home/user/.w3af/)
        create_home_dir()

        # If this fails, maybe it is because the home directory doesn't exist
        # or simply because it ain't writable|readable by this user
        if not verify_dir_has_perm(HOME_DIR, perm=os.W_OK|os.R_OK, levels=1):
            print('Either the w3af home directory "%s" or its contents are not'
                  ' writable or readable. Please set the correct permissions '
                  'and ownership.' % HOME_DIR)
            sys.exit(-3)
            
    def _tmp_directory(self):
        '''
        Handle the creation of the tmp directory, where a lot of stuff is stored.
        Usually it's something like /tmp/w3af/<pid>/
        '''
        try:
            create_temp_dir()
        except:
            msg = ('The w3af tmp directory "%s" is not writable. Please set '
            'the correct permissions and ownership.' % TEMP_DIR)
            print msg
            sys.exit(-3)            
            
    def _initializeInternalVariables(self):
        '''
        Init some internal variables; this method is called when the whole process starts, and when the user
        performs a clear() in the gtk user interface.
        '''        
        self.plugins.initialized = False
        self.target.clear()
        
        # Reset global sequence number generator
        consecutive_number_generator.reset()
        
# Singleton
wCore = w3afCore()