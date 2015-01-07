import errno
import sys

from multiprocessing.queues import JoinableQueue, _sentinel, debug, info


class SilentJoinableQueue(JoinableQueue):
    """
    A joinable queue which doesn't raise broken pipe errors, inspired in [0]

    [0] https://mail.python.org/pipermail//python-checkins/2011-July/106655.html
    """
    @staticmethod
    def _feed(buffer, notempty, send, writelock, close):
        debug('starting thread to feed data to pipe')
        from multiprocessing.util import is_exiting

        nacquire = notempty.acquire
        nrelease = notempty.release
        nwait = notempty.wait
        bpopleft = buffer.popleft
        sentinel = _sentinel
        if sys.platform != 'win32':
            wacquire = writelock.acquire
            wrelease = writelock.release
        else:
            wacquire = None

        try:
            while 1:
                nacquire()
                try:
                    if not buffer:
                        nwait()
                finally:
                    nrelease()
                try:
                    while 1:
                        obj = bpopleft()
                        if obj is sentinel:
                            debug('feeder thread got sentinel -- exiting')
                            close()
                            return

                        if wacquire is None:
                            send(obj)
                        else:
                            wacquire()
                            try:
                                send(obj)
                            finally:
                                wrelease()
                except IndexError:
                    pass
                except IOError:
                    # Should be catching the same as errno.EPIPE below
                    return
                except Exception as e:
                    if getattr(e, 'errno', 0) == errno.EPIPE:
                        return
        except Exception, e:
            # Since this runs in a daemon thread the resources it uses
            # may be become unusable while the process is cleaning up.
            # We ignore errors which happen after the process has
            # started to cleanup.
            try:
                if is_exiting():
                    info('error in queue thread: %s', e)
                else:
                    import traceback
                    traceback.print_exc()
            except Exception:
                pass

# monkey-patch
import multiprocessing.queues
multiprocessing.queues.JoinableQueue = SilentJoinableQueue