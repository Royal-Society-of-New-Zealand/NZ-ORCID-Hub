.. _writing_peer-review_items:

Writing peer review items
^^^^^^^^^^^^^^^^^^^^^

The task of writing peer review is very similar to writing works and funding, i.e.,

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.
* the Hub then either sends the people identified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

As with all complex objects passed through the Hub, peer review requires a structured file format such as the json or YAML formats to convey.

The main difference between peer review and other complex ORCID objects is that to assert peer review requires the pre-registration of a peer review group for the peer review to belong to.
As a best practice, you should use existing group IDs (so peer review activity can be grouped on the user's ORCID record as expected) before creating a new one.  To search for the existence of a peer review group requires the use of the ORCID API.  Until we've built the search feature of the Hub, let us know the group's name and we'll () run the search for you.

If you do need to create a new peer review group this can be accomplished from the '/Settings/GroupId Record' page available to Organisation Administrators.
Select 'Create', and you'll be able to specify::

Name:: The name of the group. This can be the name of a journal (Journal of Criminal Justice), a publisher (Society of Criminal Justice), or non-specific description (Legal Journal) as required.
Group ID:: The group's identifier, formatted as type:identifier, e.g. issn:12345678. This can be as specific (e.g. the journal's ISSN) or vague as required. Valid types include: issn, ringgold, orcid-generated, fundref, publons (contact ORCID if you require a different group ID type)
Description:: A brief textual description of the group. This can be as specific or vague as required.
Type:: One of the specified types: publisher; institution; journal; conference; newspaper; newsletter; magazine; peer-review service (contact ORCID if you require a different peer review type)

Once saved, from the '/Settings/GroupId Record' page, select the group you've just created and the click 'With selected' > 'Insert or Update record'.  As soon as the record shows a put code, the group's "Group Id" can be referred to in a peer-review file.

NB: you only need to do this once for each peer review group.

The Hub accepts batches of peer review items where each item contains an initial invitees block (detailing the names, email, and optionally ORCID iD and put-code for each individual to be affected) and following that invitee block, the data to be written to each invitee's ORCID record.  The peer review data must comply with the structure of the ORCID V2.0/V2.1 peer review schema, but omit put-code.  If the task describes an update to existing information in a users ORCID record the put-code will not apply to all invitees; instead specify each put-code in the data of the relevant invitee::

    [{"invitees":[{invitee1}, {invitee2}, ...], peer review},{"invitees":[{invitee4}, {invitee5}, ...], peer review2}, ...]

Example files can be found here: `peer_review.json <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/docs/examples/peer_reviews.json>`_ and `peer_reviews.yaml <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/docs/examples/peer_reviews.yaml>`_, while any uploaded peer review file will be validated against the `peer review schema in YAML <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/peer_review_schema.yaml>`_.

For more information on the structure of the peer review files see here: `Peer review schema for ORCID API 2.0/2.1 </peer_review_schema.html>`_
For an overview of peer review in ORCID see here: `Workflow: Peer Review <https://members.orcid.org/api/workflow/peer-review>`_
