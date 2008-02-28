'''
consoleUi.py

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

import sys
try:
    # Some traditional imports
    from random import randint
    import time
    
    # Import all other menu's
    import core.ui.consoleUi.url as url
    import core.ui.consoleUi.tools as tools
    import core.ui.consoleUi.profiles as profiles
    import core.ui.consoleUi.plugins as plugins
    import core.ui.consoleUi.exploit as exploit
    
    # Import w3af
    import core.controllers.w3afCore
    import core.controllers.outputManager as om
    from core.controllers.w3afException import w3afException
    from core.ui.consoleUi.consoleMenu import consoleMenu
    from core.controllers.threads.threadManager import threadManager as tm
    import core.controllers.miscSettings as miscSettings
    from core.ui.consoleUi.pluginConfig import pluginConfig
    import core.data.kb.knowledgeBase as kb
except KeyboardInterrupt:
    print 'Exiting before importing modules.'
    sys.exit(0)
    
class consoleUi(consoleMenu):
    '''
    A console user interface.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )    
    '''
    def __init__( self, scriptFile=None , commands=[] ):
        self._scriptFileName = scriptFile
        
        consoleMenu.__init__(self)
        self._menu = {'help':self._rootHelp, 'url-settings':self._url, 'misc-settings':self._misc,\
        'plugins':self._plugins,'start':self.start, 'assert': self._assert, \
        'profiles':self._profile,'exploit':self._exploit,'exit':self._exit,'target':self._target,'tools':self._tools, 'version': self._version}
        self._w3af = core.controllers.w3afCore.w3afCore()
        self._commands = commands
        # I will use pop(), so I need a reversed list.
        self._commands.reverse()
        self._targetURLs = []
        
        self._tm = tm()
    
    def sh( self ):
        '''
        Starts the shell's main loop.
        
        @parameter commands: A list of commands to run.
        @return: The prompt
        '''
        prompt = 'w3af>>> '
        self._mainloop( prompt )
        
    def _exec( self, command ):
        '''
        Executes a user input.
        '''
        command, parameters = self._parse( command )

        if command in self._menu.keys():
            func = self._menu[command]
            return func(parameters)
        else:
            om.out.console( 'command not found' )
        
    def _rootHelp( self, parameters ):
        '''
        Prints a help message to the user.
        '''
        if len(parameters) == 0 :
            self.mprint('The following commands are available:','')
            self.mprint('help','You are here. help [command] prints more specific help.')
            self.mprint('url-settings','Configure the URL opener.')
            self.mprint('misc-settings','Configure w3af misc settings.')
            self.mprint('plugins','Enable, disable and configure plugins.')
            self.mprint('profiles','List and start scan profiles.')
            self.mprint('start','Start site analysis.')
            self.mprint('exploit','Exploit a vulnerability.')
            self.mprint('tools','Enter the tools section.')
            self.mprint('target','Set the target URL.')
            self.mprint('exit','Exit w3af.')
        elif parameters[0] == 'target':
            self.mprint('Enter the target configuration. Here you will configure the target URL.','')
        elif parameters[0] == 'exploit':
            self.mprint('Enter the exploit configuration.','')
        elif parameters[0] == 'plugins':
            self.mprint('Enter the plugin configuration.','')
        elif parameters[0] == 'url-settings':
            self.mprint('Enter the url configuration.','')
        elif parameters[0] == 'profiles':
            self.mprint('Enter the profiles configuration. Here you will be able to run predefined scans.','')
        elif parameters[0] == 'misc-settings':
            self.mprint('Enter the w3af misc configuration.','')
    
    def _tools( self, parameters ):
        '''
        Opens a tools menu
        '''
        toolsObj = tools.tools( self._commands )
        try:
            toolsObj.sh()
        except KeyboardInterrupt,k:
            om.out.console('')
    
    def _url( self, parameters  ):
        '''
        Opens a URL config menu
        '''
        _url = url.url( self._w3af, self._commands )
        try:
            _url.sh()
        except KeyboardInterrupt,k:
            om.out.console('')
        
    def _profile( self, parameters  ):
        '''
        Opens a profile config menu
        '''
        s = profiles.profiles( self._w3af, self._commands )
        try:
            s.sh()
        except KeyboardInterrupt,k:
            om.out.console('')
        
    def _plugins( self, parameters ):
        '''
        Opens a plugins config menu
        '''
        p = plugins.plugins( self._w3af, self._commands  )
        try:
            p.sh()
        except KeyboardInterrupt,k:
            om.out.console('')
        
    def _exploit( self, parameters  ):
        '''
        Opens a exploit config menu
        '''
        e = exploit.exploit( self._w3af, self._commands )
        try:
            e.sh()
        except KeyboardInterrupt,k:
            om.out.console('')
    
    def _version( self, parameters ):
        '''
        Prints the w3af version.
        '''
        om.out.information(self._w3af.getVersion())
        return True
        
    def _misc( self, parameters ):
        '''
        Opens a misc config menu
        '''
        mS = miscSettings.miscSettings()
        pConf = pluginConfig( self._w3af, self._commands )
        prompt = 'w3af/misc-settings>>> '
        pConf.sh( prompt, mS )
        return True
    
    def _target( self, parameters ):
        '''
        Sets the target URL
        '''
        tar = self._w3af.target
        pConf = pluginConfig( self._w3af, self._commands )
        prompt = 'w3af/target>>> '
        pConf.sh( prompt, tar )
        return True
        
    def start( self, parameters  ):
        '''
        Starts the discovery and audit work.
        '''
        try:
            self._w3af.initPlugins()
            self._w3af.verifyEnvironment()
            self._w3af.start()
        except w3afException, e:
            om.out.console( str(e) )
        except AssertionError, ae:
            om.out.error( str(ae) )
        except KeyboardInterrupt, e:
            self._exit()
        
        return True
        
    def _getRndExitMsg( self ):
        '''
        @return: A random exit msg.
        '''
        res = []
        res.append('bye.')
        res.append('Be a good boy and contribute with some lines of code.')
        res.append('Be a good boy and contribute with some money :)')
        res.append('w3af, better than the regular script kiddie.')
        res.append('GPL v2 inside.')
        res.append('got shell?')
        res.append('spawned a remote shell today?')
        
        res = res[ randint( 0, len(res) -1 ) ]
        
        return res
    
    def _assert( self, parameters ):
        '''
        This command is used to replace unit-tests.
        '''
        assertCommand = 'assert '
        assertCommand += ' '.join( parameters )
        try:
            exec( assertCommand )
        except AssertionError, ae:
            if self._scriptFileName:
                msg = 'Assert **FAILED** in w3af script "'+ self._scriptFileName +'"'
            else:
                msg = 'Assert **FAILED**'

            try:
                # Get the value of the first argument
                a = parameters[0]
                exec( 'aRes = ' + a )
            except:
                pass
            else:
                msg += ' : ' + a + ' == ' + str(aRes)
            raise w3afException( msg )
        except Exception, e:
            om.out.error('An unexpected exception was raised during assertion: ' + str(e) )
            om.out.error('The executed command was: ' + assertCommand )
        else:
            om.out.console('Assert succeded.')
        
    def _exit( self, parameters = [] ):
        om.out.console( '' )
        om.out.console( self._getRndExitMsg() )
        try:
            self._tm.stopAllDaemons()
            self._tm.join( joinAll=True )
            # Let them die ...
            try:
                time.sleep(0.5)
            except:
                pass
        except w3afException, w3:
            om.out.error( 'Found exception while joining threads: '+str(w3) )
        except Exception, e:
            om.out.debug( 'Found unhandled exception while joining threads: '+str(e) )

        return False
    
    _back = _exit
