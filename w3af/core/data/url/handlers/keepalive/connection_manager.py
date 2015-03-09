import operator
import threading
import time

from .utils import debug
from w3af.core.controllers.exceptions import ConnectionPoolException

# Max connections allowed per host
MAX_CONNECTIONS = 50


class ConnectionManager(object):
    """
    The connection manager must be able to:
        * keep track of all existing HTTPConnections
        * kill the connections that we're not going to use anymore
        * Create/reuse connections when needed.
        * Control the size of the pool.
    """
    # Used in get_available_connection
    GET_AVAILABLE_CONNECTION_RETRY_SECS = 0.25
    GET_AVAILABLE_CONNECTION_RETRY_NUM = 25
    UNKNOWN = 'unknown'

    def __init__(self):
        self._lock = threading.RLock()
        self._host_pool_size = MAX_CONNECTIONS
        self._hostmap = {}     # map hosts to a list of connections
        self._used_cons = []   # connections being used per host
        self._free_conns = []  # available connections

    def remove_connection(self, conn, host=None, reason=UNKNOWN):
        """
        Remove a connection, it was closed by the server.

        :param conn: Connection to remove
        :param host: The host for to the connection. If passed, the connection
        will be removed faster.
        """
        # Just make sure we don't leak open connections
        conn.close()

        with self._lock:
            removed_from_hostmap = False

            if host:
                if host in self._hostmap:
                    if conn in self._hostmap[host]:
                        self._hostmap[host].remove(conn)
                        removed_from_hostmap = True

            else:
                # We don't know the host. Need to find it by looping
                for _host, conns in self._hostmap.items():
                    if conn in conns:
                        host = _host
                        conns.remove(conn)
                        removed_from_hostmap = True
                        break

            if not removed_from_hostmap:
                msg = '%s was NOT removed from hostmap pool.'
                debug(msg % conn)

            removed_from_free_or_used = False
            for lst in (self._free_conns, self._used_cons):
                try:
                    lst.remove(conn)
                except ValueError:
                    # I don't care much about the connection not being in
                    # the free_conns or used_conns. This might happen because
                    # of a thread locking issue (basically, someone is not
                    # locking before moving connections around).
                    pass
                else:
                    removed_from_free_or_used = True

            if not removed_from_free_or_used:
                msg = '%s was NOT in free/used connection lists.'
                debug(msg % conn)

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
        with self._lock:
            if conn in self._used_cons:
                self._used_cons.remove(conn)
                self._free_conns.append(conn)

    def replace_connection(self, bad_conn, req, conn_factory):
        """
        Re-create a mal-functioning connection.

        :param bad_conn: The bad connection
        :param req: The request we want to send using the new connection
        :param conn_factory: The factory function for new connection creation.
        """
        # This connection is dead anyways
        bad_conn.close()

        host = req.get_host()

        with self._lock:
            # Remove
            self.remove_connection(bad_conn, host, reason='replace connection')

            # Create the new one
            new_conn = conn_factory(req)
            conns = self._hostmap.setdefault(host, [])
            conns.append(new_conn)
            self._used_cons.append(new_conn)

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
        with self._lock:
            retry_count = self.GET_AVAILABLE_CONNECTION_RETRY_NUM
            host = req.get_host()

            while retry_count > 0:
                # First check if we can reuse an existing free connection from
                # the connection pool
                for conn in self._hostmap.setdefault(host, []):
                    try:
                        self._free_conns.remove(conn)
                    except ValueError:
                        continue
                    else:
                        self._used_cons.append(conn)

                        msg = 'Reusing free %s to use in new request'
                        debug(msg % conn)

                        return conn

                # No? Well, if the connection pool is not full let's try to
                # create a new one.
                conn_total = self.get_connections_total(host)
                if conn_total < self._host_pool_size:
                    # Add the connection
                    conn = conn_factory(req)
                    self._used_cons.append(conn)
                    self._hostmap[host].append(conn)

                    # logging
                    msg = 'Added %s to pool, current %s pool size: %s'
                    debug(msg % (conn, host, conn_total + 1))

                    return conn

                else:
                    args = (conn_total, self._host_pool_size)
                    msg = 'No free connections in pool with size %s/%s. Wait...'
                    debug(msg % args)

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
                    retry_count -= 1
                    time.sleep(self.GET_AVAILABLE_CONNECTION_RETRY_SECS)

            msg = 'HTTP connection pool (keepalive) waited too long (%s sec)' \
                  ' for a free connection, giving up. This usually occurs' \
                  ' when w3af is scanning using a slow connection, the remote' \
                  ' server is slow (or applying QoS to IP addresses flagged' \
                  ' as attackers).'
            seconds = (self.GET_AVAILABLE_CONNECTION_RETRY_NUM *
                       self.GET_AVAILABLE_CONNECTION_RETRY_SECS)
            raise ConnectionPoolException(msg % seconds)

    def get_all(self, host=None):
        """
        If <host> is passed return a list containing the created connections
        for that host. Otherwise return a dict with 'host: str' and
        'conns: list' as items.

        :param host: Host
        """
        if host:
            return list(self._hostmap.get(host, []))
        else:
            return dict(self._hostmap)

    def get_connections_total(self, host=None):
        """
        If <host> is None return the grand total of created connections;
        otherwise return the total of created conns. for <host>.
        """
        if host not in self._hostmap:
            return 0

        values = self._hostmap.values() if (host is None) \
            else [self._hostmap[host]]
        return reduce(operator.add, map(len, values or [[]]))
