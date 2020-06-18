"""
poll.py

Copyright 2019 Andres Riancho

This file is part of w3af, http://w3af.org/ .

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

"""
import sys
import time
import errno
import select
import itertools

READ = select.POLLIN | select.POLLPRI | select.POLLERR | select.POLLHUP
READ_WRITE = READ | select.POLLOUT
ERROR = select.POLLERR


def poll(rlist, wlist, xlist, timeout=None):
    """
    This is a drop-in replacement of select.select() which uses select.poll()
    to avoid the limitations on select.select()

    :param rlist: List of sockets to read from
    :param wlist: List of sockets to write from
    :param xlist: List of sockets to wait for exceptional conditions
    :param timeout: The seconds to wait for new poll() events
    :return: The return value is a triple of lists of objects that are ready
    """
    timeout = timeout * 1000.0
    end_time = 0

    if timeout is not None:
        end_time = time.time() + timeout

    #
    # Create the poll object and register the fds
    #
    poll_obj = select.poll()

    for fd in rlist:
        poll_obj.register(fd, READ)

    for fd in wlist:
        poll_obj.register(fd, READ_WRITE)

    for fd in xlist:
        poll_obj.register(fd, ERROR)

    #
    # Map file descriptors to socket objects
    #
    # Since poll() returns a list of tuples containing the file descriptor
    # for the socket and the event flag, a mapping from file descriptor numbers
    # to objects is needed to retrieve the socket to read or write from it.
    #
    # https://pymotw.com/2/select/
    #
    fd_to_fd = dict()

    for fd in itertools.chain(rlist, wlist, xlist):
        #
        # select.select() supports receiving objects (files, sockets, etc.) or
        # the file descriptor as int. Need to support both here:
        #
        if hasattr(fd, 'fileno'):
            fd_to_fd[fd.fileno()] = fd
        else:
            fd_to_fd[fd] = fd

    #
    # Actually poll() for changes
    #
    while True:
        poll_obj.poll(timeout)

        try:
            poll_fds = poll_obj.poll(timeout)
        except select.error:
            err = sys.exc_info()[1]

            if err.args[0] == errno.EINTR:
                # If we loop back we have to subtract the amount of time
                # we already waited
                if timeout is not None:
                    timeout = end_time - time.time()
                    if timeout < 0:
                        return [], [], []
            else:
                # Something else caused the select.error, so
                # this actually is an exception.
                raise
        else:
            #
            # poll() returns the result in its own format, which I need to
            # unwrap in order to follow the select.select() interface
            #
            rlist, wlist, xlist = [], [], []

            for fd, flags in poll_fds:
                if flags & select.POLLIN:
                    rlist.append(fd_to_fd[fd])

                if flags & select.POLLOUT:
                    wlist.append(fd_to_fd[fd])

                if flags & select.POLLERR:
                    xlist.append(fd_to_fd[fd])

            return rlist, wlist, xlist
