# -*- coding: utf-8 -*-
"""Application views."""

from collections import namedtuple

from flask import render_template

from application import app, db
from forms import DateRangeForm
from login_provider import roles_required
from models import Role


@app.route("/user_summary")
@roles_required(Role.SUPERUSER)
def user_summary():
    form = DateRangeForm()
    if not (form.from_date.data and form.to_date.data):
        date_range = User.select(fn.MIN(User.created_at).alias('from_date'), fn.MAX(User.created_at).alias('to_date')).first()
        if date_range:
            if not form.from_date.data:
                form.from_date.data = date_range.from_date
            if not form.to_date.data:
                form.to_date.data = date_range.to_date

    from_date, to_date = form.from_date.data, form.to_date.data

    sql = """
SELECT st.*, o.name
FROM (
    SELECT o.id, count(u.id) AS user_count, count(u.orcid) AS linked_user_count
    FROM organisation AS o
        LEFT JOIN user_org AS uo ON uo.org_id=o.id
        LEFT JOIN "user" AS u ON u.id=uo.user_id
    WHERE u.created_at BETWEEN % AND %s
    GROUP BY o.id) AS st
NATURAL JOIN organisation AS o
ORDER BY o.name"""

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
