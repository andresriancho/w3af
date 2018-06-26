import time
import OpenSSL

import w3af.core.controllers.output_manager as om

from w3af.core.data.url.handlers.keepalive.utils import debug
from w3af.core.controllers.exceptions import ConnectionPoolException


class ConnectionManager(object):
    """
    The connection manager must be able to:
        * Keep track of all existing HTTPConnections
        * Kill the connections that we're not going to use anymore
        * Create/reuse connections when needed.
        * Control the size of the pool.
    """
    # Max connections allowed per host
    MAX_CONNECTIONS = 50

    # Used in get_available_connection
    GET_AVAILABLE_CONNECTION_RETRY_SECS = 0.05
    GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME = 60.00

    # Used to cleanup the connection pool
    FORCEFULLY_CLOSE_CONN_TIME = GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME * 2

    # Log stats once every N requests
    LOG_STATS_EVERY = 25

    UNKNOWN = 'unknown'

    def __init__(self):
        # Used and free connections
        self._used_conns = set()
        self._free_conns = set()

        # Stats
        self.request_counter = 0

    def remove_connection(self, conn, host=None, reason=UNKNOWN):
        """
        Remove a connection, it was closed by the server.

        :param conn: Connection to remove
        :param host: The host for to the connection. If passed, the connection
                     will be removed faster.
        :param reason: Why this connection is removed
        """
        # Just make sure we don't leak open connections
        try:
            conn.close()
        except OpenSSL.SSL.SysCallError:
            # This exception is raised when the remote end closes the connection
            # before we do. We continue as if nothing happen, because our goal
            # is to have a closed connection, and we already got that.
            pass

        # Remove it from out internal DB
        for conns in (self._free_conns, self._used_conns):
            conns.discard(conn)

        args = (conn, reason)
        msg = 'Removed %s from pool. Reason "%s"'
        debug(msg % args)

    def free_connection(self, conn):
        """
        Mark connection as available for being reused
        """
        if conn in self._used_conns.copy():
            self._used_conns.discard(conn)
            self._free_conns.add(conn)
            conn.current_request_start = None

    def replace_connection(self, bad_conn, req, conn_factory):
        """
        Replace a broken connection.

        :param bad_conn: The bad connection
        :param req: The request we want to send using the new connection
        :param conn_factory: The factory function for new connection creation.
        """
        # Remove
        self.remove_connection(bad_conn,
                               host=req.get_host(),
                               reason='replace connection')

        # Create the new one
        new_conn = conn_factory(req)
        new_conn.current_request_start = time.time()
        self._used_conns.add(new_conn)

        # Log
        args = (bad_conn, new_conn)
        debug('Replaced broken %s with the new %s' % args)

        return new_conn

    def log_stats(self, host):
        """
        Log stats every N requests for a connection (which in most cases translate
        1:1 to HTTP requests).

        :return: None, write output to log file.
        """
        # Log this information only once every N requests
        self.request_counter += 1
        if self.request_counter % self.LOG_STATS_EVERY != 0:
            return

        # General stats
        free = len(self.get_all_free_for_host(host))
        in_use = list(self.get_all_used_for_host(host))
        args = (host, free, len(in_use), self.MAX_CONNECTIONS)

        msg = '%s connection pool stats (free:%s / in_use:%s / max:%s)'
        om.out.debug(msg % args)

        # Connection in use time stats
        def sort_by_time(c1, c2):
            return cmp(c1.current_request_start, c2.current_request_start)

        in_use.sort(sort_by_time)
        top_offenders = in_use[:5]

        connection_info = []

        for conn in top_offenders:
            if conn.current_request_start is None:
                continue

            args = (conn.id, time.time() - conn.current_request_start)
            connection_info.append('(%s, %.2f sec)' % args)

        connection_info = ' '.join(connection_info)
        om.out.debug('Connections with more in use time: %s' % connection_info)

    def get_available_connection(self, req, conn_factory):
        """
        Return an available connection ready to be reused

        :param req: Request we want to send using the connection.
        :param conn_factory: Factory function for connection creation. Receives
                             req as parameter.
        """
        waited_time_for_conn = 0.0
        host = req.get_host()

        self.log_stats(host)

        while waited_time_for_conn < self.GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME:
            if not req.new_connection:
                # If the user is not specifying that he needs a new HTTP
                # connection for this request then check if we can reuse an
                # existing free connection from the connection pool
                #
                # By default req.new_connection is False, meaning that we'll
                # most likely re-use the connections
                #
                # A user sets req.new_connection to True when he wants to
                # do something special with the connection (such as setting
                # a specific timeout)
                for conn in self.get_all_free_for_host(host):
                    try:
                        self._free_conns.remove(conn)
                    except KeyError:
                        # The connection was removed from the set by another thread
                        continue
                    else:
                        self._used_conns.add(conn)
                        conn.current_request_start = time.time()

                        msg = 'Reusing free %s to use in %s'
                        args = (conn, req)
                        debug(msg % args)

                        return conn

            debug('Going to create a new HTTPConnection')

            # If the connection pool is not full let's try to create a new conn
            conn_total = self.get_connections_total(host)
            if conn_total < self.MAX_CONNECTIONS:
                # Create a new connection
                conn = conn_factory(req)
                conn.current_request_start = time.time()

                # Store it internally
                self._used_conns.add(conn)

                # Log
                msg = 'Added %s to pool to use in %s, current %s pool size: %s'
                args = (conn, req, host, conn_total + 1)
                debug(msg % args)

                if waited_time_for_conn > 0:
                    msg = 'Waited %.2fs for a connection to be available in the pool.'
                    om.out.debug(msg % waited_time_for_conn)

                return conn

            # Well, the connection pool for this host is full, this
            # means that many threads are sending requests to the host
            # and using the connections. This is not bad, just shows
            # that w3af is keeping the connections busy
            #
            # Another reason for this situation is that the connections
            # are *really* slow => taking many seconds to retrieve the
            # HTTP response => not freeing often
            #
            # We should wait a little and try again
            args = (conn_total, host)
            msg = ('MAX_CONNECTIONS (%s) for host %s reached. Waiting for one'
                   ' to be released')
            debug(msg % args)

            waited_time_for_conn += self.GET_AVAILABLE_CONNECTION_RETRY_SECS
            time.sleep(self.GET_AVAILABLE_CONNECTION_RETRY_SECS)

            # Yet another potential situation is that w3af is not freeing the
            # connections properly because of a bug. Connections that never
            # leave the self._used_conns are going to slowly kill the HTTP
            # client, since at some point (when the max is reached) no more HTTP
            # requests will be sent.
            self.cleanup_broken_connections()

        msg = ('HTTP connection pool (keepalive) waited too long (%s sec)'
               ' for a free connection, giving up. This usually occurs'
               ' when w3af is scanning using a slow connection, the remote'
               ' server is slow (or applying QoS to IP addresses flagged'
               ' as attackers) or the configured number of threads in w3af'
               ' is too high compared with the connection manager'
               ' MAX_CONNECTIONS.')
        raise ConnectionPoolException(msg % self.GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME)

    def cleanup_broken_connections(self):
        """
        Find connections that have been in self._used_conns for more than
        FORCEFULLY_CLOSE_CONN_TIME. Close and remove them.

        :return: None
        """
        for conn in self._used_conns.copy():
            current_request_start = conn.current_request_start
            if current_request_start is None:
                continue

            time_in_used_state = time.time() - current_request_start
            if time_in_used_state > self.FORCEFULLY_CLOSE_CONN_TIME:
                reason = ('Connection %s has been in "used_conns" for more than'
                          ' FORCEFULLY_CLOSE_CONN_TIME. Forcefully closing it.')

                om.out.debug(reason % conn)

                self.remove_connection(conn,
                                       host=None,
                                       reason=reason)

    def iter_all_connections(self):
        for conns in (self._free_conns, self._used_conns):
            for conn in conns.copy():
                yield conn

    def get_all_free_for_host(self, host):
        """
        :param host: The host to filter by
        :return: All free connections for the specified host
        """
        free_conns = set()

        for conn in self._free_conns.copy():
            if conn.host == host:
                free_conns.add(conn)

        return free_conns

    def get_all_used_for_host(self, host):
        """
        :param host: The host to filter by
        :return: All in use connections for the specified host
        """
        used_conns = set()

        for conn in self._used_conns.copy():
            if conn.host == host:
                used_conns.add(conn)

        return used_conns

    def get_all(self, host=None):
        """
        If <host> is passed return a set containing the created connections
        for that host. Otherwise return a dict with 'host: str' and
        'conns: list' as items.

        :param host: Host
        """
        conns = set()

        for conn in self.iter_all_connections():
            if host is None:
                conns.add(conn)
            elif host == conn.host:
                conns.add(conn)

        return conns

    def get_connections_total(self, host=None):
        """
        If <host> is None return the grand total of open connections;
        otherwise return the total of created conns for <host>.
        """
        return len(self.get_all(host=host))
