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

    def remove_connection(self, conn, reason=UNKNOWN):
        """
        Remove a connection, it was closed by the server.

        :param conn: Connection to remove
        :param reason: Why this connection is removed
        """
        # Just make sure we don't leak open connections
        try:
            conn.close()
        except (AttributeError, OpenSSL.SSL.SysCallError):
            # This exception is raised when the remote end closes the connection
            # before we do. We continue as if nothing happen, because our goal
            # is to have a closed connection, and we already got that.
            pass

        # Remove it from out internal DB
        for conns in (self._free_conns, self._used_conns):
            conns.discard(conn)

        msg = 'Removed %s from pool. Reason "%s"'
        args = (conn, reason)
        debug(msg % args)

        msg = 'Free connection size %s / Used connection size %s'
        args = (len(self._free_conns), len(self._used_conns))
        debug(msg % args)

    def free_connection(self, conn):
        """
        Mark connection as available for being reused
        """
        if conn in self._used_conns.copy():
            self._used_conns.discard(conn)
            self._free_conns.add(conn)
            conn.current_request_start = None
            conn.connection_manager_move_ts = time.time()

    def replace_connection(self, bad_conn, req, conn_factory):
        """
        Replace a broken connection.

        :param bad_conn: The bad connection
        :param req: The request we want to send using the new connection
        :param conn_factory: The factory function for new connection creation.
        """
        # Remove
        self.remove_connection(bad_conn, reason='replace connection')

        # Create the new one
        new_conn = conn_factory(req)
        new_conn.current_request_start = time.time()
        new_conn.connection_manager_move_ts = time.time()
        self._used_conns.add(new_conn)

        # Log
        args = (bad_conn, new_conn)
        debug('Replaced broken %s with the new %s' % args)

        return new_conn

    def get_connection_pool_stats(self, host_port):
        # General stats
        free = len(self.get_all_free_for_host_port(host_port))
        in_use = list(self.get_all_used_for_host_port(host_port))
        args = (host_port, free, len(in_use), self.MAX_CONNECTIONS, len(in_use) + free)

        msg = '%s connection pool stats (free:%s / in_use:%s / max:%s / total:%s)'
        return msg % args

    def log_stats(self, host_port):
        """
        Log stats every N requests for a connection (which in most cases translate
        1:1 to HTTP requests).

        :return: None, write output to log file.
        """
        # Log this information only once every N requests
        self.request_counter += 1
        if self.request_counter % self.LOG_STATS_EVERY != 0:
            return

        stats = self.get_connection_pool_stats(host_port)
        om.out.debug(stats)

        # Connection in use time stats
        def sort_by_time(c1, c2):
            return cmp(c1.current_request_start, c2.current_request_start)

        in_use = list(self.get_all_used_for_host_port(host_port))
        in_use.sort(sort_by_time)
        top_offenders = in_use[:5]

        connection_info = []

        for conn in top_offenders:
            try:
                spent = time.time() - conn.current_request_start
            except TypeError:
                # This is a race condition where conn.current_request_start is
                # None, thus the - raises TypeError
                continue

            args = (conn.id, spent)
            connection_info.append('(%s, %.2f sec)' % args)

        if connection_info:
            connection_info = ' '.join(connection_info)
            om.out.debug('Connections with more in use time: %s' % connection_info)
            return

        if not top_offenders:
            om.out.debug('There are no connections marked as in use in the'
                         ' connection pool at this time')
            return

        without_request_start = ' '.join([conn.id for conn in top_offenders])
        msg = ('Connections with more in use time: No connections marked'
               ' as in_use have started to send the first byte. They are'
               ' in_use but still inactive. The in_use connections are: %s'
               % without_request_start)
        om.out.debug(msg)

    def get_free_connection_to_close(self):
        """
        Find a connection that is in self._free and return it.
        :return: An HTTP connection that will be closed
        """
        try:
            return self._free_conns.pop()
        except KeyError:
            return None

    def _reuse_connection(self, req, host_port):
        """
        Find an existing connection to reuse

        :param req: HTTP request
        :param host: The host to connect to
        :return:
        """
        for conn in self.get_all_free_for_host_port(host_port):
            try:
                self._free_conns.remove(conn)
            except KeyError:
                # The connection was removed from the set by another thread
                continue
            else:
                self._used_conns.add(conn)
                conn.current_request_start = time.time()
                conn.connection_manager_move_ts = time.time()

                msg = 'Reusing free %s to use in %s'
                args = (conn, req)
                debug(msg % args)

                return conn

    def _create_new_connection(self, req, conn_factory, host_port, conn_total):
        """
        Creates a new HTTP connection using conn_factory

        :return: An HTTP connection
        """
        debug('Creating a new HTTPConnection for request %s' % req)

        # Create a new connection
        conn = conn_factory(req)
        conn.current_request_start = time.time()
        conn.connection_manager_move_ts = time.time()

        # Store it internally
        self._used_conns.add(conn)

        # Log
        msg = 'Added %s to pool to use in %s, current %s pool size: %s'
        args = (conn, req, host_port, conn_total + 1)
        debug(msg % args)

        return conn

    def _log_waited_time_for_conn(self, waited_time_for_conn):
        if waited_time_for_conn <= 0:
            return

        msg = 'Waited %.2fs for a connection to be available in the pool'
        om.out.debug(msg % waited_time_for_conn)

    def get_available_connection(self, req, conn_factory):
        """
        Return an available connection ready to be reused

        :param req: Request we want to send using the connection.
        :param conn_factory: Factory function for connection creation. Receives
                             req as parameter.
        """
        host_port = req.get_netloc()
        self.log_stats(host_port)

        waited_time_for_conn = 0.0

        while waited_time_for_conn < self.GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME:
            #
            # One potential situation is that w3af is not freeing the
            # connections properly because of a bug. Connections that never
            # leave self._used_conns or self._free_conns are going to slowly kill
            # the HTTP connection pool, and then the whole framework, since at
            # some point (when the max is reached) no more HTTP requests will be
            # sent.
            #
            self.cleanup_broken_connections()

            conn_total = self.get_connections_total(host_port)

            #
            # If the connection pool is not full let's try to create a new connection
            # this is the default case, we want to quickly populate the connection
            # pool and, only if the pool is full, re-use the existing connections
            #
            # FIXME: Doing this here without a lock leads to a situation where
            #        the total connections exceed the MAX_CONNECTIONS
            #
            if conn_total < self.MAX_CONNECTIONS:
                conn = self._create_new_connection(req, conn_factory, host_port, conn_total)

                self._log_waited_time_for_conn(waited_time_for_conn)
                return conn

            if req.new_connection:
                #
                # The user is requesting a new HTTP connection, this is a rare
                # case because req.new_connection is False by default.
                #
                # Before this feature was used together with req.timeout, but
                # now it is not required anymore.
                #
                # This code path is reached when there is no more space in the
                # connection pool, but because new_connection is set, it is
                # possible to force a free connection to be closed:
                #
                if len(self._free_conns) > len(self._used_conns):
                    #
                    # Close one of the free connections and create a new one.
                    #
                    # Close an existing free connection because the framework
                    # is not using them (more free than used), this action should
                    # not degrade the connection pool performance
                    #
                    conn = self.get_free_connection_to_close()

                    if conn is not None:
                        self.remove_connection(conn, reason='need fresh connection')

                        self._log_waited_time_for_conn(waited_time_for_conn)
                        return self._create_new_connection(req,
                                                           conn_factory,
                                                           host_port,
                                                           conn_total)

                msg = ('The HTTP request %s has new_connection set to True.'
                       ' This forces the ConnectionManager to wait until a'
                       ' new connection can be created. No pre-existing'
                       ' connections can be reused.')
                args = (req,)
                debug(msg % args)

            else:
                #
                # If the user is not specifying that he needs a new HTTP
                # connection for this request then check if we can reuse an
                # existing free connection from the connection pool
                #
                # By default req.new_connection is False, meaning that we'll
                # most likely re-use the connections
                #
                # A user sets req.new_connection to True when he wants to
                # do something special with the connection. In the past a
                # new_connection was set to True when a timeout was specified,
                # that is not required anymore!
                #
                conn = self._reuse_connection(req, host_port)
                if conn is not None:
                    self._log_waited_time_for_conn(waited_time_for_conn)
                    return conn

            #
            # Well, the connection pool for this host is full AND there are
            # no free connections to re-use, this means that many threads are
            # sending requests to the host and using the connections. This is
            # not bad, just shows that w3af is keeping the connections busy
            #
            # Another reason for this situation is that the connections
            # are *really* slow => taking many seconds to retrieve the
            # HTTP response => not freeing often
            #
            # We should wait a little and try again
            #
            msg = ('Will not create a new connection because MAX_CONNECTIONS'
                   ' (%s) for host %s was reached. Waiting for a connection'
                   ' to be released to send HTTP request %s. %s')

            stats = self.get_connection_pool_stats(host_port)
            args = (self.MAX_CONNECTIONS, host_port, req, stats)

            debug(msg % args)

            waited_time_for_conn += self.GET_AVAILABLE_CONNECTION_RETRY_SECS
            time.sleep(self.GET_AVAILABLE_CONNECTION_RETRY_SECS)

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
        Find connections that have been in self._used_conns or self._free_conns
        for more than FORCEFULLY_CLOSE_CONN_TIME. Close and remove them.

        :return: None
        """
        now = time.time()

        for conn in self._used_conns.copy():
            current_request_start = conn.current_request_start
            if current_request_start is None:
                continue

            time_in_used_state = now - current_request_start

            if time_in_used_state > self.FORCEFULLY_CLOSE_CONN_TIME:
                reason = ('Connection %s has been in "used_conns" for more than'
                          ' %.2f seconds, forcefully closing it')
                args = (conn, self.FORCEFULLY_CLOSE_CONN_TIME)

                om.out.debug(reason % args)

                # This does a conn.close() and removes from self._used_conns
                self.remove_connection(conn, reason=reason)
            else:
                msg = '%s has been in used state for %.2f seconds'
                args = (conn, time_in_used_state)
                debug(msg % args)

        for conn in self._free_conns.copy():
            connection_manager_move_ts = conn.connection_manager_move_ts
            if connection_manager_move_ts is None:
                continue

            time_in_free_state = now - connection_manager_move_ts

            if time_in_free_state > self.FORCEFULLY_CLOSE_CONN_TIME:
                reason = ('Connection %s has been in "free_conns" for more than'
                          ' %.2f seconds, forcefully closing it')
                args = (conn, self.FORCEFULLY_CLOSE_CONN_TIME)

                om.out.debug(reason % args)

                # This does a conn.close() and removes from self._used_conns
                self.remove_connection(conn, reason=reason)
            else:
                msg = '%s has been in free state for %.2f seconds'
                args = (conn, time_in_free_state)
                debug(msg % args)

    def iter_all_connections(self):
        for conns in (self._free_conns, self._used_conns):
            for conn in conns.copy():
                yield conn

    def get_all_free_for_host_port(self, host_port):
        """
        :param host_port: The host and port to filter by
        :return: All free connections for the specified host
        """
        free_conns = set()

        for conn in self._free_conns.copy():
            if conn.host_port == host_port:
                free_conns.add(conn)

        return free_conns

    def get_all_used_for_host_port(self, host_port):
        """
        :param host_port: The host and port to filter by
        :return: All in use connections for the specified host
        """
        used_conns = set()

        for conn in self._used_conns.copy():
            if conn.host_port == host_port:
                used_conns.add(conn)

        return used_conns

    def get_all(self, host_port=None):
        """
        If <host> is passed return a set containing the created connections
        for that host. Otherwise return a dict with 'host: str' and
        'conns: list' as items.

        :param host_port: Host and port to filter by
        """
        conns = set()

        for conn in self.iter_all_connections():
            if host_port is None:
                conns.add(conn)
            elif conn.host_port == host_port:
                conns.add(conn)

        return conns

    def get_connections_total(self, host_port=None):
        """
        If <host> is None return the grand total of open connections;
        otherwise return the total of created conns for <host>.
        """
        return len(self.get_all(host_port=host_port))
