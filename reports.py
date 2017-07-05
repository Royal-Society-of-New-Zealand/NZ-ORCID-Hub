# -*- coding: utf-8 -*-
"""Application views."""

from collections import namedtuple

from flask import render_template

from application import app, db
from login_provider import roles_required
from models import Role


@app.route("/user_summary")
@roles_required(Role.SUPERUSER)
def user_summary():
    sql = """
SELECT st.*, o.name
FROM (
    SELECT o.id, count(u.id) AS user_count, count(u.orcid) AS linked_user_count
    FROM organisation AS o
        LEFT JOIN user_org AS uo ON uo.org_id=o.id
        LEFT JOIN "user" AS u ON u.id=uo.user_id
    GROUP BY o.id) AS st
NATURAL JOIN organisation AS o
ORDER BY o.name"""

    print("$$$$$$", db,  db.connect_kwargs)
    cr = db.execute_sql(sql)
    columns = [c[0] for c in cr.description]
    Row = namedtuple("Row", columns)
    rows = [Row(*r) for r in cr.fetchall()]
    total_user_count = sum(r.user_count for r in rows)
    total_linked_user_count = sum(r.linked_user_count for r in rows)

    return render_template(
        "user_summary.html",
        rows=rows,
        total_user_count=total_user_count,
        total_linked_user_count=total_linked_user_count)
