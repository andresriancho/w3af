#! /usr/bin/env python
"""Logging"""
import sys


class ILogger:
    '''Logger interface, by default this class
    will be used and logging calls are no-ops.
    '''
    level = 0
    def __init__(self, msg):
        return
    def warning(self, *args):
        return
    def debug(self, *args):
        return
    def error(self, *args):
        return
    def setLevel(cls, level):
        cls.level = level
    setLevel = classmethod(setLevel)
_LoggerClass = ILogger


class BasicLogger(ILogger):
    def __init__(self, msg, out=sys.stdout):
        self.msg, self.out = msg, out

    def warning(self, msg, *args):
        if self.level < 1: return
        print >>self, self.WARN, self.msg,
        print >>self, msg %args
    WARN = 'WARN'
    def debug(self, msg, *args):
        if self.level < 2: return
        print >>self, self.DEBUG, self.msg,
        print >>self, msg %args
    DEBUG = 'DEBUG'
    def error(self, msg, *args):
        print >>self, self.ERROR, self.msg,
        print >>self, msg %args
    ERROR = 'ERROR'

    def write(self, *args):
        '''Write convenience function; writes strings.
        '''
        for s in args: self.out.write(s)


def setBasicLogger():
    '''Use Basic Logger. 
    '''
    setLoggerClass(BasicLogger)
    BasicLogger.setLevel(0)

def setBasicLoggerWARN():
    '''Use Basic Logger.
    '''
    setLoggerClass(BasicLogger)
    BasicLogger.setLevel(1)

def setBasicLoggerDEBUG():
    '''Use Basic Logger.
    '''
    setLoggerClass(BasicLogger)
    BasicLogger.setLevel(2)

def setLoggerClass(loggingClass):
    '''Set Logging Class.
    '''
    assert issubclass(loggingClass, ILogger), 'loggingClass must subclass ILogger'
    global _LoggerClass
    _LoggerClass = loggingClass

def setLevel(level=0):
    '''Set Global Logging Level.
    '''
    ILogger.level = level

def getLogger(msg):
    '''Return instance of Logging class.
    '''
    return _LoggerClass(msg)


