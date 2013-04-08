import random

from core.controllers.plugins.evasion_plugin import EvasionPlugin
from core.data.options.option_list import OptionList


class x_forwarded_for(EvasionPlugin):
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
        EvasionPlugin.__init__(self)
        '''
        random.seed(..) is used to generate the same IP addresses in every scan
        otherwise the plugin could generate false negatives
        (scan #1 finds bug because of some specific IP it's sent in the header; 
        and then scan #2 doesn't send the same IP and the bug is not found).
        
        TODO: I think this is still not working right.
              http://pastebin.com/rfXktADV  => scan 1
              http://pastebin.com/dVK17yEt  => scan 2
              Maybe I shoulden't use random at all and just to it with a counter variable?
        '''
        random.seed(666)
        
    def modify_request(self, request):
        '''
            Add X-Forwarded-For header if the request doesn't have one
        '''
        if(not request.has_header('X-Forwarded-For')):
            request.add_header('X-Forwarded-For', self.get_random_ip())
        return request
    
    def get_random_ip(self):
        ret_ip = ''
        for _ in range(4):
            ret_ip += '%d.'%(random.randint(1, 254))
        return ret_ip[:-1]
    
    def get_options(self):
        return OptionList()
    
    def set_options(self, optionsMap): 
        pass
           
    def get_plugin_deps(self):
        return []
    
    def get_priority(self):
        return 86
    
    def get_long_desc(self):
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

