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

import core.controllers.outputManager as om

# Before doing anything, check if I have all needed dependencies
from core.controllers.misc.dependencyCheck import dependencyCheck
dependencyCheck()

# Called here to init some variables in the config ( cf.cf.save() )
import core.controllers.miscSettings as miscSettings

import os,sys
from core.controllers.misc.factory import factory
from core.controllers.misc.parseOptions import parseOptions
from core.data.url.xUrllib import xUrllib
import core.data.parsers.urlParser as urlParser
from core.controllers.w3afException import *
from core.controllers.targetSettings import targetSettings as targetSettings

import traceback
import copy
import Queue
import time

import core.data.kb.knowledgeBase as kb
import core.data.kb.config as cf
from core.data.request.frFactory import createFuzzableRequests
from core.controllers.threads.threadManager import threadManagerObj as tm

# Provide a progress bar for all plugins.
from core.controllers.coreHelpers.progressBar import progressBar
from core.controllers.coreHelpers.fingerprint404Page import fingerprint404Page

# Profile objects
from core.data.profile.profile import profile as profile

class w3afCore:
    '''
    This is the core of the framework, it calls all plugins, handles exceptions,
    coordinates all the work, creates threads, etc.
     
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''

    def __init__(self ):
        self._initializeInternalVariables()
        self.uriOpener = xUrllib()

        # Create .w3af inside home directory
        if 'HOME' not in os.environ:
            # This should never happen
            import tempfile
            self._homeLocation = tempfile.mkdtemp()
        else:
            self._homeLocation = os.environ["HOME"] + os.path.sep + '.w3af'
            if not os.path.exists(self._homeLocation):
                os.makedirs(self._homeLocation)
    
    def getHomePath( self ):
        '''
        @return: The location of the w3af directory inside the home directory of the current user.
        '''
        return self._homeLocation
        
    def _initializeInternalVariables(self):
        '''
        Init some internal variables
        '''
        # A dict with plugin types as keys and a list of plugin names as values
        self._strPlugins = {'audit':[],'grep':[],'bruteforce':[],'discovery':[],\
        'evasion':[], 'mangle':[], 'output':['console']}
        
        # A dict with plugin types as keys and a list of plugin instances as values
        self._plugins = {'audit':[],'grep':[],'bruteforce':[],'discovery':[],\
        'evasion':[], 'mangle':[], 'output':[]}

        self._pluginsOptions = {'audit':{},'grep':{},'bruteforce':{},'discovery':{},\
        'evasion':{}, 'mangle':{}, 'output':{}, 'attack':{}}
        
        self._fuzzableRequestList  = []
        
        self._initialized = False
        self.target = targetSettings()
        
        # Init some values
        kb.kb.save( 'urls', 'urlQueue' ,  Queue.Queue() )
        self._isRunning = False
        self._paused = False
        self._mustStop = False
    
    def _rPlugFactory( self, strReqPlugins, PluginType ):
        '''
        This method creates the requested modules list.
        
        @parameter strReqPlugins: A string list with the requested plugins to be executed.
        @parameter PluginType: [audit|discovery|grep]
        @return: A list with plugins to be executed, this list is ordered using the exec priority.
        '''     
        requestedPluginsList = []
        
        if 'all' in strReqPlugins:
            fileList = [ f for f in os.listdir('plugins' + os.path.sep+ PluginType + os.path.sep ) ]    
            allPlugins = [ os.path.splitext(f)[0] for f in fileList if os.path.splitext(f)[1] == '.py' ]
            allPlugins.remove ( '__init__' )
            
            if len ( strReqPlugins ) != 1:
                # [ 'all', '!sqli' ]
                # I want to run all plugins except sqli
                unwantedPlugins = [ x[1:] for x in strReqPlugins if x[0] =='!' ]
                strReqPlugins = list( set(allPlugins) - set(unwantedPlugins) ) #bleh! v2
            else:
                strReqPlugins = allPlugins
            
            # Update the plugin list
            # This update is usefull for cases where the user selected "all" plugins,
            # the self._strPlugins[PluginType] is useless if it says 'all'.
            self._strPlugins[PluginType] = strReqPlugins
                
        for pluginName in strReqPlugins:
            plugin = factory( 'plugins.' + PluginType + '.' + pluginName )

            # Now we are going to check if the plugin dependencies are met
            for dep in plugin.getPluginDeps():
                try:
                    depType, depPlugin = dep.split('.')
                except:
                    raise w3afException('Plugin dependencies must be indicated using pluginType.pluginName notation.\
                    This is an error in ' + pluginName +'.getPluginDeps() .')
                if depType == PluginType:
                    if depPlugin not in strReqPlugins:
                        if cf.cf.getData('autoDependencies'):
                            strReqPlugins.append( depPlugin )
                            om.out.information('Auto-enabling plugin: ' + PluginType + '.' + depPlugin)
                            # nice recursive call, this solves the "dependency of dependency" problem =)
                            return self._rPlugFactory( strReqPlugins, depType )
                        else:
                            raise w3afException('Plugin '+ pluginName +' depends on plugin ' + dep + ' and ' + dep + ' is not enabled. ')
                else:
                    if depPlugin not in self._strPlugins[depType]:
                        if cf.cf.getData('autoDependencies'):
                            dependObj = factory( 'plugins.' + depType + '.' + depPlugin )
                            dependObj.setUrlOpener( self.uriOpener )
                            if dependObj not in self._plugins[depType]:
                                self._plugins[depType].insert( 0, dependObj )
                                self._strPlugins[depType].append( depPlugin )
                            om.out.information('Auto-enabling plugin: ' + depType + '.' + depPlugin)
                        else:
                            raise w3afException('Plugin '+ pluginName +' depends on plugin ' + dep + ' and ' + dep + ' is not enabled. ')
                    else:
                        # if someone in another planet depends on me... run first
                        self._strPlugins[depType].remove( depPlugin )
                        self._strPlugins[depType].insert( 0, depPlugin )
            
            # Now we set the plugin options
            if pluginName in self._pluginsOptions[ PluginType ].keys():
                plugin.setOptions( self._pluginsOptions[ PluginType ][pluginName] )
                
            # This sets the url opener for each module that is called inside the for loop
            plugin.setUrlOpener( self.uriOpener )
            # Append the plugin to the list
            requestedPluginsList.append ( plugin )

        # The plugins are all on the requestedPluginsList, now I need to order them
        # based on the module dependencies. For example, if A depends on B , then
        # B must be runned first.
        
        orderedPluginList = []
        for plugin in requestedPluginsList:
            deps = plugin.getPluginDeps()
            if len( deps ) != 0:
                # This plugin has dependencies, I should add the plugins in order
                for plugin2 in requestedPluginsList:
                    if PluginType+'.'+plugin2.getName() in deps and plugin2 not in orderedPluginList:
                        orderedPluginList.insert( 1, plugin2)

            # Check if I was added because of a dep, if I wasnt, add me.
            if plugin not in orderedPluginList:
                orderedPluginList.insert( 100, plugin )
        
        # This should never happend.
        if len(orderedPluginList) != len(requestedPluginsList):
            om.out.error('There is an error in the way w3afCore orders plugins. The ordered plugin list length is not equal to the requested plugin list. ', newLine=False)
            om.out.error('The error was found sorting plugins of type: '+ PluginType +'.')
            om.out.error('Please report this bug to the developers including a complete list of commands that you run to get to this error.')

            om.out.error('Ordered plugins:')
            for plugin in orderedPluginList:
                om.out.error('- ' + plugin.getName() )

            om.out.error('\nRequested plugins:')
            for plugin in requestedPluginsList:
                om.out.error('- ' + plugin.getName() )

            sys.exit(-1)

        return orderedPluginList
    
    def initPlugins( self ):
        '''
        The user interfaces should run this method *before* calling start(). If they don't do it, an exception is
        raised.
        '''
        self._initialized = True
        
        # This is inited before all, to have a full logging facility.
        om.out.setOutputPlugins( self._strPlugins['output'] )
        
        # First, create an instance of each requested plugin and add it to the plugin list
        # Plugins are added taking care of plugin dependencies
        self._plugins['audit'] = self._rPlugFactory( self._strPlugins['audit'] , 'audit')
        
        self._plugins['bruteforce'] = self._rPlugFactory( self._strPlugins['bruteforce'] , 'bruteforce')        
        
        # First, create an instance of each requested module and add it to the module list
        self._plugins['discovery'] = self._rPlugFactory( self._strPlugins['discovery'] , 'discovery')
        
        self._plugins['grep'] = self._rPlugFactory( self._strPlugins['grep'] , 'grep')
        self.uriOpener.setGrepPlugins( self._plugins['grep'] )
        
        self._plugins['mangle'] = self._rPlugFactory( self._strPlugins['mangle'] , 'mangle')
        self.uriOpener.settings.setManglePlugins( self._plugins['mangle'] )
        
        # Only by creating this object I'm adding 404 detection to all plugins
        fingerprint404Page( self.uriOpener )

    def _updateURLsInKb( self, fuzzableRequestList ):
        '''
        Creates an URL list in the kb
        '''
        # Create the queue that will be used in gtkUi
        oldList = kb.kb.getData( 'urls', 'urlList')
        newList = [ fr.getURL() for fr in fuzzableRequestList if fr.getURL() not in oldList ]
        
        # Update the Queue
        urlQueue = kb.kb.getData( 'urls', 'urlQueue' )
        for u in newList:
            urlQueue.put( u )
            
        # Update the list of URLs that is used world wide
        oldList = kb.kb.getData( 'urls', 'urlList')
        newList.extend( oldList )
        kb.kb.save( 'urls', 'urlList' ,  newList )

        # Update the list of URIs that is used world wide
        uriList = kb.kb.getData( 'urls', 'uriList')
        uriList.extend( [ fr.getURI() for fr in fuzzableRequestList] )
        uriList = list( set( uriList ) )
        kb.kb.save( 'urls', 'uriList' ,  uriList )
    
    def _discoverAndBF( self ):
        '''
        Discovery and bruteforce phases are related, so I have joined them
        here in this method.
        '''
        go = True
        tmpList = copy.deepcopy( self._fuzzableRequestList )
        res = []
        discoveredFrList = []
        
        # this is an identifier to know what call number of _discoverWorker we are working on
        self._count = 0
        
        while go:
            discoveredFrList = self._discover( tmpList )
            successfullyBruteforced = self._bruteforce( discoveredFrList )
            if not successfullyBruteforced:
                # Haven't found new credentials
                go = False
                for fr in discoveredFrList:
                    if fr not in res:
                        res.append( fr )
            else:
                tmp = []
                tmp.extend( discoveredFrList )
                tmp.extend( successfullyBruteforced )
                for fr in tmp:
                    if fr not in res:
                        res.append( fr )
                
                # So in the next "while go:" loop I can do a discovery
                # using the new credentials I found
                tmpList = successfullyBruteforced
                
                # Now I reconfigure the urllib to use the newly found credentials
                self._reconfigureUrllib()
        
        self._updateURLsInKb( res )
        
        return res
    
    def _reconfigureUrllib( self ):
        '''
        Configure the main urllib with the newly found credentials.
        '''
        for v in kb.kb.getData( 'basicAuthBrute' , 'auth' ):
            self.uriOpener.settings.setBasicAuth( v.getURL(), v['user'], v['pass'] )
        
        # I don't need this, the urllib2 cookie handler does this for me
        #for v in kb.kb.getData( 'formAuthBrute' , 'auth' ):
        #   self.uriOpener.settings.setHeadersList( v['additionalHeaders'] )
    
    def pause(self, pauseYesNo):
        '''
        Pauses/Un-Pauses scan.
        @parameter trueFalse: True if the UI wants to pause the scan.
        '''
        self._paused = pauseYesNo
        self._isRunning = not pauseYesNo
        om.out.debug('Paused scan.')
        
    def _sleepIfPausedDieIfStopped( self ):
        '''
        This method sleeps until self._paused is False.
        '''
        while self._paused:
            time.sleep(0.5)
            
            # The user can pause and then STOP
            if self._mustStop:
                # hack!
                raise KeyboardInterrupt
        
        # The user can simply STOP the scan
        if self._mustStop:
            raise KeyboardInterrupt
            
    def start(self):
        '''
        Starts the work.
        User interface coders: Please remember that you have to call initPlugins() method before calling start.
        
        @return: No value is returned.
        ''' 
        om.out.debug('Called w3afCore.start()')
        try:
            # Just in case the gtkUi / consoleUi / WebUi forgot to do this...
            self.verifyEnvironment()
        except Exception,e:
            om.out.error('verifyEnvironment() raised an exception: "' + str(e) + '". This should never happend, are *you* user interface coder sure that you called verifyEnvironment() *before* start() ?')
            raise e
        else:
            self._isRunning = True
            try:
                ###### This is the main section ######
                # Create the first fuzzableRequestList
                for url in cf.cf.getData('targets'):
                    try:
                        response = self.uriOpener.GET( url )
                        self._fuzzableRequestList.extend( createFuzzableRequests( response ) )
                    except KeyboardInterrupt:
                        self._end()
                        raise
                    except w3afException, w3:
                        om.out.information( 'The target URL: ' + url + ' is unreachable.' )
                        om.out.information( 'Error description: ' + str(w3) )
                    except Exception, e:
                        om.out.information( 'The target URL: ' + url + ' is unreachable because of an unhandled exception.' )
                        om.out.information( 'Error description: "' + str(e) + '". See debug output for more information.')
                        om.out.debug( 'Traceback for this error: ' + str( traceback.format_exc() ) )
                
                self._fuzzableRequestList = self._discoverAndBF()
                    
                if len( self._fuzzableRequestList ) == 0:
                    om.out.information('No URLs found by discovery.')
                else:
                    
                    # Filter out the fuzzable requests that aren't important (and will be ignored by audit plugins anyway...)
                    #self._fuzzableRequestList = [ fr for fr in self._fuzzableRequestList if len(fr.getDc()) > 0 or cf.cf.getData('fuzzFileName') or (cf.cf.getData('fuzzableCookie') and fr.getCookie() ) ]
                    msg = 'Found ' + str(len( kb.kb.getData( 'urls', 'urlList') )) + ' URLs and ' + str(len( self._fuzzableRequestList)) + ' different points of injection.'
                    om.out.information( msg )
                    
                    om.out.information('The list of URLs is:')
                    for u in kb.kb.getData( 'urls', 'urlList'):
                        om.out.information( '- ' + u )
                        
                    om.out.information('The list of fuzzable requests is:')
                    for fuzzRequest in self._fuzzableRequestList:
                        om.out.information( '- ' + str( fuzzRequest) )
                
                    self._audit()
                    
                self._end()
                ###########################
            
            except w3afFileException, e:
                self._end( e )
                om.out.setOutputPlugins( ['console'] )
            except w3afException, e:
                self._end( e )
                raise e
            except KeyboardInterrupt, e:
                self._end()
                # I wont handle this. 
                # The user interface must know what to do with it
                raise e
    
    def cleanup( self ):
        '''
        The GTK user interface calls this when a scan has been stopped (or ended successfully) and the user wants
        to start a new scan. All data from the kb is deleted.
        @return: None
        '''
        # Clean all data that is stored in the kb
        reload(kb)
        
        # Not cleaning the config is a FEATURE, because the user is most likely going to start a new
        # scan to the same target, and he wants the proxy, timeout and other configs to remain configured
        # as he did it the first time.
        '''
        reload(cf)
        
        # Set some defaults for the core
        #import core.controllers.miscSettings as miscSettings
        #miscSettings.miscSettings()
        '''
        
        # Zero internal variables from the core
        self._initializeInternalVariables()
        
    def stop( self ):
        '''
        This method is called by the user interface layer, when the user "clicks" on the stop button.
        @return: None. The stop method can take some seconds to return.
        '''
        self._mustStop = True
    
    def _end( self, exceptionInstance=None ):
        '''
        This method is called when the process ends normally or by an error.
        '''
        if exceptionInstance:
            om.out.error( str(exceptionInstance) )

        tm.join( joinAll=True )
        tm.stopAllDaemons()
        
        for plugin in self._plugins['grep']:
            plugin.end()
        
        om.out.endOutputPlugins()
        cf.cf.save('targets', [] )
        # Now I'm definitly not running:
        self._isRunning = False
        
        # End the xUrllib
        self.uriOpener.end()
        self.uriOpener = xUrllib()
    
    def isRunning( self ):
        '''
        @return: If the user has called start, and then wants to know if the core is still working, it should call
        isRunning to know that.
        '''
        return self._isRunning
    
    def _discover( self, toWalk ):
        # Init some internal variables
        self._alreadyWalked = toWalk
        self._urls = []
        self._firstDiscovery = True
        
        for fr in toWalk:
            fr.iterationNumber = 0
        
        result = []
        try:
            result = self._discoverWorker( toWalk )
        except KeyboardInterrupt, e:
            om.out.information('The user interrupted the discovery phase, continuing with audit.')
            result = self._alreadyWalked
        
        # Let the plugins know that they won't be used anymore
        self._endDiscovery()
        
        return result
    
    def _endDiscovery( self ):
        '''
        Let the discovery plugins know that they won't be used anymore.
        '''
        for p in self._plugins['discovery']:
            try:
                p.end()
            except Exception, e:
                om.out.error('The plugin "'+ p.getName() + '" raised an exception in the end() method: ' + str(e) )
    
    def _discoverWorker(self, toWalk ):
        om.out.debug('Called _discoverWorker()' )
        
        while len( toWalk ) and self._count < cf.cf.getData('maxDiscoveryLoops'):
        
            # This variable is for LOOP evasion
            self._count += 1
            
            pluginsToRemoveList = []
            fuzzableRequestList = []
            
            for plugin in self._plugins['discovery']:
                for fr in toWalk:
                
                    if fr.iterationNumber > cf.cf.getData('maxDepth'):
                        om.out.debug('Avoiding discovery loop in fuzzableRequest: ' + str(fr) )
                    else:
                        om.out.debug('Running plugin: ' + plugin.getName() )
                        try:
                            # This is for the pause and stop feature
                            self._sleepIfPausedDieIfStopped()
                        
                            pluginResult = plugin.discover( fr )
                        except w3afException,e:
                            om.out.error( str(e) )
                            tm.join( plugin )
                        except w3afRunOnce, rO:
                            # Some plugins are ment to be run only once
                            # that is implemented by raising a w3afRunOnce exception
                            pluginsToRemoveList.append( plugin )
                            tm.join( plugin )
                        else:
                            tm.join( plugin )
                            for i in pluginResult:
                                fuzzableRequestList.append( (i, plugin.getName()) )
                        om.out.debug('Ending plugin: ' + plugin.getName() )
                    #end-if fr.iterationNumber > cf.cf.getData('maxDepth'):
                #end-for
            #end-for
            
            ##
            ##  The search has finished, now i'll some mangling with the requests
            ##
            newFR = []
            for iFr, pluginWhoFoundIt in fuzzableRequestList:
                # I dont care about fragments ( http://a.com/foo.php#frag ) and I dont really trust plugins
                # so i'll remove fragments here
                iFr.setURL( urlParser.removeFragment( iFr.getURL() ) )
                
                # Increment the iterationNumber !
                iFr.iterationNumber = fr.iterationNumber + 1
                
                if iFr not in self._alreadyWalked and urlParser.baseUrl( iFr.getURL() ) in cf.cf.getData('baseURLs'):
                    # Found a new fuzzable request
                    newFR.append( iFr )
                    self._alreadyWalked.append( iFr )
                    if iFr.getURL() not in self._urls:
                        om.out.information('New URL found by ' + pluginWhoFoundIt +' plugin: ' +  iFr.getURL() )
                        self._urls.append( iFr.getURL() )
            
            # Update the list / queue that lives in the KB
            self._updateURLsInKb( newFR )

            
            ##
            ##  Cleanup!
            ##
            
            # This wont be used anymore, here i'm duplicating objects that are already saved
            # in the self._alreadyWalked list.
            del fuzzableRequestList
            try: del iFr
            except: pass
            
            # Get ready for next while loop
            toWalk = newFR
            
            # Remove plugins that don't want to be runned anymore
            for pluginToRemove in pluginsToRemoveList:
                if pluginToRemove in self._plugins['discovery']:
                    self._plugins['discovery'].remove( pluginToRemove )
                    om.out.debug('The discovery plugin: ' + pluginToRemove.getName() + ' wont be runned anymore.')      
                    try:
                        pluginToRemove.end()
                    except Exception, e:
                        om.out.error('The plugin "'+ pluginToRemove.getName() + '" raised an exception in the end() method: ' + str(e) )
                
        return self._alreadyWalked
    
    def _audit(self):
        om.out.debug('Called _audit()' )
        
        # This two for loops do all the audit magic [KISS]
        for plugin in self._plugins['audit']:
            om.out.information('Starting ' + plugin.getName() + ' plugin execution.')
            
            pbar = progressBar( maxValue=len(self._fuzzableRequestList) )
            
            for fr in self._fuzzableRequestList:
                # Sends each fuzzable request to the plugin
                try:
                    # This is for the pause and stop feature
                    self._sleepIfPausedDieIfStopped()
                
                    plugin.audit( fr )
                except w3afException, e:
                    om.out.error( str(e) )
                    tm.join( plugin )
                else:
                    tm.join( plugin )
                    # Update the progress bar
                    pbar.inc()
                    
            # Let the plugin know that we are not going to use it anymore
            try:
                plugin.end()
            except w3afException, e:
                om.out.error( str(e) )
                
    def _bruteforce(self, fuzzableRequestList):
        '''
        @parameter fuzzableRequestList: A list of fr's to be analyzed by the bruteforce plugins
        @return: A list of the URL's that have been successfully bruteforced
        '''
        res = []
        
        om.out.debug('Called _bruteforce()' )
        
        for plugin in self._plugins['bruteforce']:
            om.out.information('Starting ' + plugin.getName() + ' plugin execution.')
            for fr in fuzzableRequestList:
                
                # Sends each url to the plugin
                try:
                    # This is for the pause and stop feature
                    self._sleepIfPausedDieIfStopped()
                    
                    frList = plugin.bruteforce( fr )
                    tm.join( plugin )
                except w3afException, e:
                    tm.join( plugin )
                    om.out.error( str(e) )
                    
                try:
                    plugin.end()
                except w3afException, e:
                    om.out.error( str(e) )
                    
                res.extend( frList )
                
        return res

    def setPluginOptions(self, pluginName, pluginType, PluginsOptions ):
        '''
        @parameter PluginsOptions: A dict with the options for a plugin. For example:\
        {'LICENSE_KEY':'AAAA'}
            
        @return: No value is returned.
        '''
        pluginName, PluginsOptions = parseOptions( pluginName, PluginsOptions )         
        self._pluginsOptions[ pluginType ][ pluginName ] = PluginsOptions
    
    def getPlugins( self, pluginType ):
        return self._strPlugins[ pluginType ]
    
    def setPlugins( self, pluginNames, pluginType ):
        '''
        This method sets the plugins that w3afCore is going to use. Before this plugin
        existed w3afCore used setDiscoveryPlugins() / setAuditPlugins() / etc , this wasnt
        really extensible and was replaced with a combination of setPlugins and getPluginTypes.
        This way the user interface isnt bound to changes in the plugin types that are added or
        removed.
        
        @parameter pluginNames: A list with the names of the Plugins that will be runned.
        @parameter pluginType: The type of the plugin.
        @return: None
        '''
        # Validate the input...
        pluginNames = list( set( pluginNames ) )    # bleh !
        pList = self.getPluginList(  pluginType  )
        for p in pluginNames:
            if p not in pList \
                and p.replace('!','') not in pList\
                and p != 'all':
                    raise w3afException('Unknown plugin selected ("'+ p +'")')
        
        setMap = {'discovery':self._setDiscoveryPlugins, 'audit':self._setAuditPlugins,\
        'grep':self._setGrepPlugins, 'evasion':self._setEvasionPlugins, 'output':self._setOutputPlugins\
        , 'mangle': self._setManglePlugins, 'bruteforce': self._setBruteforcePlugins}
        
        func = setMap[ pluginType ]
        func( pluginNames )
        
    def getPluginTypesDesc( self, type ):
        '''
        @parameter type: The type of plugin for which we want a description.
        @return: A description of the plugin type passed as parameter
        '''
        try:
            p = __import__('plugins.' + type )
            aModule = sys.modules['plugins.' + type ]
        except Exception, e:
            print e
            raise w3afException('Unknown plugin type: "'+ type + '".')
        else:
            return aModule.getLongDescription()
        
    def getPluginTypes( self ):
        '''
        @return: A list with all plugin types.
        '''
        pluginTypes = [ f for f in os.listdir('plugins' + os.path.sep) if f.count('.py') == 0 ]
        pluginTypes.remove( 'attack' )
        if '.svn' in pluginTypes:
            pluginTypes.remove('.svn')
        return pluginTypes
    
    def _setBruteforcePlugins( self, bruteforcePlugins ):
        '''
        @parameter manglePlugins: A list with the names of output Plugins that will be runned.
        @return: No value is returned.
        '''
        self._strPlugins['bruteforce'] = bruteforcePlugins
    
    def _setManglePlugins( self, manglePlugins ):
        '''
        @parameter manglePlugins: A list with the names of output Plugins that will be runned.
        @return: No value is returned.
        '''
        self._strPlugins['mangle'] = manglePlugins
    
    def _setOutputPlugins( self, outputPlugins ):
        '''
        @parameter outputPlugins: A list with the names of output Plugins that will be runned.
        @return: No value is returned.
        '''
        self._strPlugins['output'] = outputPlugins
        
    def _setDiscoveryPlugins( self, discoveryPlugins ):
        '''
        @parameter discoveryPlugins: A list with the names of Discovery Plugins that will be runned.
        @return: No value is returned.
        '''         
        self._strPlugins['discovery'] = discoveryPlugins
    
    def _setAuditPlugins( self, AuditPlugins ):
        '''
        @parameter AuditPlugins: A list with the names of Audit Plugins that will be runned.
        @return: No value is returned.
        '''         
        self._strPlugins['audit'] = AuditPlugins
        
    def _setGrepPlugins( self, GrepPlugins):
        '''
        @parameter GrepPlugins: A list with the names of Grep Plugins that will be used.
        @return: No value is returned.
        '''     
        self._strPlugins['grep'] = GrepPlugins
        
    def _setEvasionPlugins( self, EvasionPlugins ):
        '''
        @parameter EvasionPlugins: A list with the names of Evasion Plugins that will be used.
        @return: No value is returned.
        '''     
        self._plugins['evasion'] = self._rPlugFactory( EvasionPlugins , 'evasion')
        self.uriOpener.setEvasionPlugins( self._plugins['evasion'] )

    def verifyEnvironment(self):
        '''
        Checks if all parameters where configured correctly by the above layer (w3af.py)
        '''
        # Init ALL plugins
        if not self._initialized:
            raise w3afException('You must call the initPlugins method before calling start()')
        
        try:
            assert cf.cf.getData('targets')  != [], 'No target URI configured.'
        except AssertionError, ae:
            raise w3afException( str(ae) )
            
        try:
            cry = True
            if len(self._strPlugins['audit']) == 0 and len(self._strPlugins['discovery']) == 0 \
            and len(self._strPlugins['grep']) == 0:
                cry = False
            assert cry , 'No audit, grep or discovery plugins configured to run.'
        except AssertionError, ae:
            raise w3afException( str(ae) )
    
    def getPluginList( self, PluginType ):
        '''
        @return: A string list of the names of all available plugins by type.
        '''
        strPluginList = self._getListOfFiles( 'plugins' + os.path.sep + PluginType + os.path.sep )
        return strPluginList
        
    def getProfileList( self ):
        '''
        @return: A string list of the names of all available profiles.
        '''
        strProfileList = self._getListOfFiles( 'profiles' + os.path.sep, extension='.ini' )
        instanceList = [ profile('profiles' + os.path.sep + p + '.ini' ) for p in strProfileList ]
        return instanceList
        
    def _getListOfFiles( self, directory, extension='.py' ):
        '''
        @return: A string list of the names of all available plugins by type.
        '''
        fileList = [ f for f in os.listdir( directory ) ]
        strFileList = [ os.path.splitext(f)[0] for f in fileList if os.path.splitext(f)[1] == extension ]
        if '__init__' in strFileList:
            strFileList.remove ( '__init__' )
        strFileList.sort()
        return strFileList
        
    def getPluginInstance( self, pluginName, pluginType ):
        '''
        @return: An instance of a plugin.
        '''
        fileList = [ f for f in os.listdir('plugins' + os.path.sep + pluginType  + os.path.sep) ]    
        fileList = [ os.path.splitext(f)[0] for f in fileList if os.path.splitext(f)[1] == '.py' ]
        fileList.remove ( '__init__' )
        if pluginName in fileList:
            ModuleName = 'plugins.'+pluginType+ '.'+ pluginName
            __import__(ModuleName)
            aModule = sys.modules[ModuleName]
            className = ModuleName.split('.')[len(ModuleName.split('.'))-1]
            aClass = getattr( aModule , className )
            plugin = apply(aClass, ())
            # This sets the url opener for each module that is called inside the for loop
            plugin.setUrlOpener( self.uriOpener )
            if pluginName in self._pluginsOptions[ pluginType ].keys():
                plugin.setOptions( self._pluginsOptions[ pluginType ][pluginName] )
                
            # This will init some plugins like mangle and output
            if pluginType == 'attack' and not self._initialized:
                self.initPlugins()
            return plugin
                
        raise w3afException('Plugin not found')
    
    def useProfile( self, profileName ):
        '''
        Gets all the information from the profile, and runs it.
        '''
        if not profileName.endswith('.ini'):
            profileName += '.ini'
        if not profileName.startswith('profiles' + os.path.sep):
            profileName = 'profiles' + os.path.sep + profileName
            
        profileInstance = profile( profileName ) 
        for pluginType in self._plugins.keys():
            pluginNames = profileInstance.getEnabledPlugins( pluginType )
            self.setPlugins( pluginNames, pluginType )
            '''
            def setPluginOptions(self, pluginName, pluginType, PluginsOptions ):
                @parameter PluginsOptions: A dict with the options for a plugin. For example:\
                { 'LICENSE_KEY':'AAAA' }
            '''
            for pluginName in profileInstance.getEnabledPlugins( pluginType ):
                pluginOptions = profileInstance.getPluginOptions( pluginName, pluginType )
                self.setPluginOptions( pluginName, pluginType, pluginOptions )
    
    def getVersion( self ):
        # Let's check if the user is using a version from SVN
        import re
        revision = '0'
        try:
            for line in file('.svn' + os.path.sep +'entries'):
                line = line.strip()
                if re.match('^\d+$', line ):
                    if int(line) > int(revision):
                        revision = int(line)
        except:
            pass
    
        res = 'w3af - Web Application Attack and Audit Framework'
        res += '\nVersion: beta6'
        res += '\nRevision: ' + str(revision)
        res += '\nAuthor: Andres Riancho'
        return res
    
# """"Singleton""""
wCore = w3afCore()

