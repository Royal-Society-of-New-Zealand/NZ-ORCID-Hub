# -*- coding: utf-8 -*-
"""Application views for reporting."""

from flask import redirect, render_template, request, url_for
from peewee import JOIN, SQL, fn

from . import app
from .forms import DateRangeForm
from .login_provider import roles_required
from .models import OrcidToken, Organisation, OrgInvitation, Role, User, UserInvitation, UserOrg


@app.route("/user_summary")
@roles_required(Role.SUPERUSER)
def user_summary():  # noqa: D103

    form = DateRangeForm(request.args)
    sort = request.args.get("sort")
    if sort:
        try:
            sort = int(sort)
        except:
            sort = None
    desc = request.args.get("desc")
    if desc:
        try:
            desc = int(desc)
        except:
            desc = None

    if not (form.from_date.data and form.to_date.data):
        date_range = User.select(
            fn.MIN(User.created_at).alias('from_date'),
            fn.MAX(User.created_at).alias('to_date')).first()
        return redirect(
            url_for(
                "user_summary",
                from_date=date_range.from_date.date().isoformat(),
                to_date=date_range.to_date.date().isoformat(),
                sort=sort, desc=desc))

    user_counts = (User.select(
        User.organisation.alias("org_id"),
        fn.COUNT(fn.DISTINCT(User.id)).alias("user_count")).where(
            User.created_at.between(form.from_date.data, form.to_date.data)).join(
                UserOrg, JOIN.LEFT_OUTER, on=(UserOrg.org_id == User.id)).group_by(
                    User.organisation)).alias("user_counts")

    linked_counts = (OrcidToken.select(
        OrcidToken.org.alias("org_id"),
        fn.COUNT(fn.DISTINCT(OrcidToken.user)).alias("linked_user_count")).where(
            OrcidToken.created_at.between(form.from_date.data, form.to_date.data)).group_by(
                OrcidToken.org).alias("linked_counts"))

    query = (Organisation.select(
        Organisation.name,
        fn.COALESCE(user_counts.c.user_count, 0).alias("user_count"),
        fn.COALESCE(linked_counts.c.linked_user_count, 0).alias("linked_user_count")).join(
            user_counts, on=(Organisation.id == user_counts.c.org_id)).join(
                linked_counts, JOIN.LEFT_OUTER,
                on=(Organisation.id == linked_counts.c.org_id)))

    if sort == 1:
        order_fields = [SQL("user_count"), SQL("linked_user_count"), ]
    else:
        order_fields = [Organisation.name, ]
    if desc:
        order_fields = [f.desc() for f in order_fields]
    query = query.order_by(*order_fields)

    total_user_count = sum(r.user_count for r in query if r.user_count)
    total_linked_user_count = sum(r.linked_user_count for r in query if r.linked_user_count)

    headers = [(h,
                url_for(
                    "user_summary",
                    from_date=form.from_date.data,
                    to_date=form.to_date.data,
                    sort=i,
                    desc=1 if sort == i and not desc else 0))
               for i, h in enumerate(["Name", "Linked User Count / User Count (%)"])]

    return render_template(
        "user_summary.html",
        form=form,
        query=query,
        total_user_count=total_user_count,
        total_linked_user_count=total_linked_user_count,
        sort=sort, desc=desc,
        headers=headers)


@app.route("/org_invitatin_summary")
@roles_required(Role.SUPERUSER)
def org_invitation_summary():  # noqa: D103

    summary = OrgInvitation.select(
        fn.COUNT(OrgInvitation.id).alias("total"),
        fn.COUNT(OrgInvitation.confirmed_at).alias("confirmed")).first()
    unconfirmed_invitations = OrgInvitation.select().where(
        OrgInvitation.confirmed_at >> None).order_by(OrgInvitation.created_at)

    return render_template(
        "invitation_summary.html",
        title="Organisation Invitation Summary",
        summary=summary,
        unconfirmed_invitations=unconfirmed_invitations)


@app.route("/user_invitatin_summary")
@roles_required(Role.SUPERUSER)
def user_invitation_summary():  # noqa: D103

    summary = UserInvitation.select(
        fn.COUNT(UserInvitation.id).alias("total"),
        fn.COUNT(UserInvitation.confirmed_at).alias("confirmed")).first()
    unconfirmed_invitations = UserInvitation.select().where(
        UserInvitation.confirmed_at >> None).order_by(UserInvitation.created_at)

    return render_template(
        "invitation_summary.html",
        title="User Invitation Summary",
        summary=summary,
        unconfirmed_invitations=unconfirmed_invitations)
