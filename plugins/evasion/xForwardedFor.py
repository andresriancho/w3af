from random import randint
from core.controllers.basePlugin.baseEvasionPlugin import baseEvasionPlugin

# options
from core.data.options.optionList import optionList


class xForwardedFor(baseEvasionPlugin):
    '''
    This Plugin adds a X-Forwarded-For header field to every request (except it already has one).
    It generates a new random IP for every request.
    The Plugin can be handy if the target has some kind of "one request per host"-feature

    Example:
    if(isset($_SERVER['HTTP_X_FORWARDED_FOR'])){
           $ip = explore(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0];
    } else {
           $ip = $_SERVER['REMOTE_ADDR'];
    }


    @author: m3tamantra (m3tamantra@gmail.com )
    '''

    def __init__(self):
        baseEvasionPlugin.__init__(self)
        
    def modifyRequest(self, request):
        '''
            Add X-Forwarded-For header if the request doesn't have one
        '''
        if(not request.has_header('X-Forwarded-For')):
            request.add_header('X-Forwarded-For', self.getRandomIP())
        return request
    
    def getRandomIP(self):
        ret_ip = ''
        for _ in range(4):
            ret_ip += '%d.'%(randint(1, 254))
        return ret_ip[:-1]
    
    def getOptions(self):
        return optionList()
    
    def setOptions(self, optionsMap): 
        pass
           
    def getPluginDeps(self):
        return []
    
    def getPriority(self):
        return 86
    
    def getLongDesc(self):
        return '''
        This evasion plugin adds an X-Forwarded-For header field
        with random IP to every request.
        
        Example:
            Input:
                GET / HTTP/1.1
                ...
            Output:
                GET / HTTP/1.1
                ...
                X-Forwarded-For: 34.21.66.39
        '''
    
