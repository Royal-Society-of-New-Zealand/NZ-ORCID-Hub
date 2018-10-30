# -*- coding: utf-8 -*-
"""Failover DB connection."""

import logging

from peewee import DatabaseError, InterfaceError, PostgresqlDatabase
from psycopg2 import OperationalError


class PgDbWithFailover(PostgresqlDatabase):
    """Postgres DB connection with a failover server."""

    def __init__(self, *args, failover_host=None, **kwargs):
        """Set up the connction paramers with an additional failover host name."""
        self.failover_host = failover_host
        super().__init__(*args, **kwargs)

    def connect(self):
        """Attempt to connect or reconnect."""
        if not self._local.closed:
            with self._conn_lock:
                with self.exception_wrapper:
                    try:
                        self._close(self._local.conn)
                    except Exception:
                        pass
                    self._local.closed = True
        super().connect()

    def _connect(self, database, encoding=None, **kwargs):
        """Attempt to connect to the DB.

        In case it's not available, 'fail over' to the back-up stand-by DB and propagete
        it to the master DB.
        """
        try:
            return super()._connect(database, encoding=encoding, **kwargs)
        except OperationalError as ex:
            logging.info("Failing over to %s", self.failover_host)

            if "could not connect to server" in ex.args[0] or "could not translate host name" in ex.args[0]:
                kwargs["host"] = self.failover_host
                conn = super()._connect(database, encoding=encoding, **kwargs)
                with conn.cursor() as cr:
                    cr.execute("SELECT promote_standby();")
                self.connect_kwargs[
                    "host"], self.failover_host = self.failover_host, self.connect_kwargs["host"]
                return conn
            else:
                raise ex

    def execute_sql(self, sql, params=None, require_commit=True):
        """Attempt to exectute a SQL statement. If it fails try to fail over ..."""
        try:
            return super().execute_sql(sql, params=params, require_commit=require_commit)
        except (DatabaseError, InterfaceError):
            self.connect()
            return super().execute_sql(sql, params=params, require_commit=False)
