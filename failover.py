# -*- coding: utf-8 -*-
"""Failover DB connection. """

import logging

from peewee import DatabaseError, InterfaceError, PostgresqlDatabase
from psycopg2 import OperationalError


class PgDbWithFailover(PostgresqlDatabase):
    """Postgres DB connection with a failover server. """

    def __init__(self, *args, failover_host=None, **kwargs):
        self.failover_host = failover_host
        super().__init__(*args, **kwargs)

    def connect(self):
        if not self._local.closed:
            with self._conn_lock:
                with self.exception_wrapper:
                    try:
                        self._close(self._local.conn)
                    except:
                        pass
                    self._local.closed = True
        super().connect()

    def _connect(self, database, encoding=None, **kwargs):
        try:
            return super()._connect(database, encoding=encoding, **kwargs)
        except OperationalError as ex:
            logging.warning("Failing over to %s", self.failover_host)

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
        try:
            return super().execute_sql(sql, params=params, require_commit=require_commit)
        except (DatabaseError, InterfaceError) as ex:
            self.connect()
            return super().execute_sql(sql, params=params, require_commit=False)
