# -*- coding: utf-8 -*-
"""Application views for reporting."""

import json
import re
import zipstream

from datetime import datetime
from flask import flash, make_response, Response, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from peewee import JOIN, SQL, fn

from . import app, cache
from .forms import DateRangeForm
from .login_provider import roles_required
from .models import OrcidToken, Organisation, OrgInvitation, Role, User, UserInvitation, UserOrg, NestedDict
from .orcid_client import MemberAPI


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


@app.route("/user_cv")
@app.route("/user_cv/<string:op>")
@login_required
def user_cv(op=None):
    """Create user CV using the CV templage filled with the ORCID profile data."""
    user = User.get(current_user.id)
    if not user.orcid:
        flash("You haven't linked your account with ORCID.", "warning")
        return redirect(request.referrer or url_for("index"))

    record = cache.get(user.orcid)
    if not record:
        token = OrcidToken.select(OrcidToken.access_token).where(
            OrcidToken.user_id == user.id, OrcidToken.org_id == user.organisation_id,
            OrcidToken.scopes.contains("read-limited")).first()
        if token is None:
            flash("You haven't granted your organisation necessary access to your profile..",
                  "danger")
            return redirect(url_for("link"))
        api = MemberAPI(user=user, access_token=token.access_token)
        try:
            record = api.get_record()
            works = [w for g in record.get("activities-summary", "works", "group") for w in g.get("work-summary")]
            combine_detail_works_summary = []
            for w in works:
                work_api_response = api.view_work(user.orcid, w.get("put-code"))
                work_data = json.loads(json.dumps(work_api_response.to_dict()), object_pairs_hook=NestedDict)
                combine_detail_works_summary.append(work_data)

            record['detail-works-summary'] = combine_detail_works_summary
            cache.set(user.orcid, record)
        except Exception as ex:
            flash(f"Failed to retrieve the profile: {ex}", "danger")
            return redirect(url_for("link"))

    if op is None:
        return render_template("user_cv.html")
    else:

        work_type_journal = []
        work_type_books = []
        work_type_book_chapter = []
        work_type_conference = []
        work_type_patent = []
        work_type_other = []
        educations = []
        employments = []
        first_name = None
        second_names = None
        family_name = None
        countries = []
        emails = []
        researcher_urls = []

        if record:
            works = record.get("detail-works-summary")
            for w in works:
                if w.get("type") in ['JOURNAL_ARTICLE', 'JOURNAL_ISSUE']:
                    work_type_journal.append(w)
                elif w.get("type") in ['BOOK', 'BOOK_REVIEW']:
                    work_type_books.append(w)
                elif w.get("type") in ['BOOK_CHAPTER', 'EDITED_BOOK']:
                    work_type_book_chapter.append(w)
                elif w.get("type") in ['CONFERENCE_PAPER', 'CONFERENCE_ABSTRACT', 'CONFERENCE_POSTER']:
                    work_type_conference.append(w)
                elif w.get("type") in ['PATENT']:
                    work_type_patent.append(w)
                else:
                    work_type_other.append(w)

            educations = record.get("activities-summary", "educations", "education-summary")
            employments = record.get("activities-summary", "employments", "employment-summary")

            first_name, *second_names = re.split("[,; \t]", str(
                record.get("person", "name", "given-names", "value", default=user.first_name)))

            family_name = record.get("person", "name", "family-name", "value", default=user.last_name)

            countries = [a.get("country", "value") for a in record.get("person", "addresses", "address")]

            emails = [e.get("email") for e in record.get("person", "emails", "email")] if record.get(
                "person", "emails", "email") else [user.email]

            researcher_urls = [r.get("url", "value") for r in record.get("person", "researcher-urls", "researcher-url")]

        person_data = dict(first_name=first_name, second_names=second_names, family_name=family_name, address=countries,
                           emails=emails, researcher_urls=researcher_urls)
        resp = make_response(
            render_template(
                "CV.html",
                user=user,
                now=datetime.now(),
                record=record,
                person_data=person_data,
                work_type_books=work_type_books,
                work_type_book_chapter=work_type_book_chapter,
                work_type_journal=work_type_journal,
                work_type_conference=work_type_conference,
                work_type_patent=work_type_patent,
                work_type_other=work_type_other,
                educations=educations,
                employments=employments))
        resp.headers["Cache-Control"] = "private, max-age=60"
        if op == "download" or "download" in request.args:
            meta_xml_data = render_template("CV/meta.xml", user=user, now=datetime.now())
            content_xml_data = render_template("CV/content.xml", user=user, now=datetime.now(), record=record,
                                               person_data=person_data, work_type_books=work_type_books,
                                               work_type_book_chapter=work_type_book_chapter,
                                               work_type_journal=work_type_journal,
                                               work_type_conference=work_type_conference,
                                               work_type_patent=work_type_patent, work_type_other=work_type_other,
                                               educations=educations, employments=employments)

            response = Response(cv_generator(meta_xml_data, content_xml_data),
                                mimetype='application/vnd.oasis.opendocument.text')
            response.headers["Content-Type"] = "application/vnd.oasis.opendocument.text"
            response.headers[
                'Content-Disposition'] = f"attachment; filename={current_user.name.replace(' ', '_')}_CV.odt"

            return response

    return resp


def cv_generator(meta_xml_data, content_xml_data):
    """Zip all CV XML files into one odt file."""
    z = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED)

    z.writestr("content.xml", content_xml_data.encode("UTF-8"))
    z.writestr("meta.xml", meta_xml_data.encode("UTF-8"))

    z.write(app.root_path + "/templates/CV/META-INF/manifest.xml", "/META-INF/manifest.xml")
    z.write(app.root_path + "/templates/CV/layout-cache", "layout-cache")
    z.write(app.root_path + "/templates/CV/manifest.rdf", "manifest.rdf")
    z.write(app.root_path + "/templates/CV/mimetype", "mimetype")
    z.write(app.root_path + "/templates/CV/settings.xml", "settings.xml")
    z.write(app.root_path + "/templates/CV/styles.xml", "styles.xml")

    for chunk in z:
        yield chunk
    z.close()
