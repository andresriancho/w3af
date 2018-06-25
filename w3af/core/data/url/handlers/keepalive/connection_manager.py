import operator
import threading
import time

import w3af.core.controllers.output_manager as om

from .utils import debug
from w3af.core.controllers.exceptions import ConnectionPoolException

# Max connections allowed per host
MAX_CONNECTIONS = 50


class ConnectionManager(object):
    """
    The connection manager must be able to:
        * Keep track of all existing HTTPConnections
        * Kill the connections that we're not going to use anymore
        * Create/reuse connections when needed.
        * Control the size of the pool.
    """
    # Used in get_available_connection
    GET_AVAILABLE_CONNECTION_RETRY_SECS = 0.05
    GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME = 60.00

    UNKNOWN = 'unknown'

    def __init__(self):
        self._lock = threading.RLock()
        self._host_pool_size = MAX_CONNECTIONS
        self._hostmap = {}        # map hosts to a list of connections
        self._used_cons = set()   # connections being used per host
        self._free_conns = set()  # available connections

    def remove_connection(self, conn, host=None, reason=UNKNOWN):
        """
        Remove a connection, it was closed by the server.

        :param conn: Connection to remove
        :param host: The host for to the connection. If passed, the connection
                     will be removed faster.
        :param reason: Why this connection is removed
        """
        # Just make sure we don't leak open connections
        conn.close()
        removed_from_hostmap = False

        if host:
            host_connections = self._hostmap.get(host, set())
            if conn in host_connections:
                host_connections.discard(conn)
                removed_from_hostmap = True

        else:
            # We don't know the host. Need to find it by looping
            # TODO: dict.items() will crash if the dict is modified while we iterate
            for _host, host_connections in self._hostmap.items():
                if conn in host_connections:
                    host = _host
                    host_connections.discard(conn)
                    removed_from_hostmap = True
                    break

        if not removed_from_hostmap:
            msg = '%s was NOT removed from hostmap pool.'
            debug(msg % conn)

        for lst in (self._free_conns, self._used_cons):
            lst.discard(conn)

        # If no more conns for 'host', remove it from mapping
        conn_total = self.get_connections_total(host)
        if host and host in self._hostmap and not conn_total:
            del self._hostmap[host]

        msg = 'Removed %s, reason %s, %s pool size is %s'
        debug(msg % (conn, reason, host, conn_total))

    def free_connection(self, conn):
        """
        Recycle a connection. Mark it as available for being reused.
        """
        if conn in self._used_cons:
            self._used_cons.discard(conn)
            self._free_conns.add(conn)

    def replace_connection(self, bad_conn, req, conn_factory):
        """
        Replace a broken connection.

        :param bad_conn: The bad connection
        :param req: The request we want to send using the new connection
        :param conn_factory: The factory function for new connection creation.
        """
        # This connection is dead anyways
        bad_conn.close()
        host = req.get_host()

        # Remove
        self.remove_connection(bad_conn, host, reason='replace connection')

        # Create the new one
        new_conn = conn_factory(req)
        conns = self._hostmap.setdefault(host, set())
        conns.add(new_conn)
        self._used_cons.add(new_conn)

        # Log
        args = (bad_conn, new_conn)
        debug('Replaced broken %s with the new %s' % args)

        return new_conn

    def get_available_connection(self, req, conn_factory):
        """
        Return an available connection ready to be reused

        :param req: Request we want to send using the connection.
        :param conn_factory: Factory function for connection creation. Receives
                             req as parameter.
        """
        waited_time_for_conn = 0.0
        host = req.get_host()

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
                hostmap = self._hostmap.setdefault(host, set())
                hostmap = hostmap.copy()

                for conn in hostmap:
                    try:
                        self._free_conns.remove(conn)
                    except KeyError:
                        continue
                    else:
                        self._used_cons.add(conn)

                        msg = 'Reusing free %s to use in new request'
                        debug(msg % conn)

                        return conn

            debug('Forcing the use of a new HTTPConnection')

            # If the connection pool is not full let's try to create a new conn
            conn_total = self.get_connections_total(host)
            if conn_total < self._host_pool_size:
                # Create a new connection
                conn = conn_factory(req)

                # Store it internally
                self._used_cons.add(conn)
                hostmap = self._hostmap.setdefault(host, set())
                hostmap.add(conn)

                # logging
                msg = 'Added %s to pool, current %s pool size: %s'
                debug(msg % (conn, host, conn_total + 1))

                if waited_time_for_conn > 0:
                    msg = 'Waited %.2fs for a connection to be available in the pool.'
                    om.out.debug(msg % waited_time_for_conn)

                return conn

            # Well, the connection pool for this host is full, this
            # means that many threads are sending request to the host
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

        msg = ('HTTP connection pool (keepalive) waited too long (%s sec)'
               ' for a free connection, giving up. This usually occurs'
               ' when w3af is scanning using a slow connection, the remote'
               ' server is slow (or applying QoS to IP addresses flagged'
               ' as attackers) or the configured number of threads in w3af'
               ' is too high compared with the connection manager'
               ' MAX_CONNECTIONS.')
        raise ConnectionPoolException(msg % self.GET_AVAILABLE_CONNECTION_RETRY_MAX_TIME)

    def get_all(self, host=None):
        """
        If <host> is passed return a set containing the created connections
        for that host. Otherwise return a dict with 'host: str' and
        'conns: list' as items.

        :param host: Host
        """
        if host:
            return self._hostmap.get(host, set()).copy()
        else:
            return self._hostmap.copy()

    def get_connections_total(self, host=None):
        """
        If <host> is None return the grand total of created connections;
        otherwise return the total of created conns. for <host>.
        """
        if host not in self._hostmap:
            return 0

        values = self._hostmap.values() if (host is None) else [self._hostmap[host]]
        return reduce(operator.add, map(len, values or [set()]))
