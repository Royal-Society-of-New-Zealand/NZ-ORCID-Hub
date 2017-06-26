# -*- coding: utf-8 -*-
"""Failover DB connection. """

import logging

from peewee import PostgresqlDatabase
from psycopg2 import OperationalError


class PgDbWithFailover(PostgresqlDatabase):
    """Postgres DB connection with a failover server. """

    def __init__(self, *args, failover_host=None, **kwargs):
        self.failover_host = failover_host
        super().__init__(*args, **kwargs)

    def _connect(self, database, encoding=None, **kwargs):
        try:
            return super()._connect(database, encoding=encoding, **kwargs)
        except OperationalError as ex:
            logging.warning("Failingover to %s", self.failover_host)

            if "could not connect to server" in ex.args[0]:
                kwargs["host"] = self.failover_host
                conn = super()._connect(database, encoding=encoding, **kwargs)
                conn.raw_sql("COPY (SELECT 1) TO '/tmp/pg_failover_trigger.00';")
                self.connect_kwargs[
                    "host"], self.failover_host = self.failover_host, self.connect_kwargs["host"]
                return conn
            else:
                raise ex
