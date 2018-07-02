.. _writing_works_items:

Writing works items
^^^^^^^^^^^^^^^^^^^^^

The task of writing works is very similar to writing affiliations, i.e.,

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.
* the Hub then either sends the people identified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

The main difference in writing works is that while affiliation files are simple and can thus be given as either csv or tsv format, works in ORCID are more complex requiring a structured file format such as the json or YAML formats to convey.
The Hub accepts batches of works items where each item contains an initial invitees block (detailing the names, email, and optionally ORCID iD and put-code for each individual to be affected) and following that invitee block, the data to be written to each invitee's ORCID record.  The work data must comply with the structure of the ORCID V2.0/V2.1 works schema, but omit put-code.  If the task describes an update to existing information in a users ORCID record the put-code will not apply to all invitees; instead specify each put-code in the data of the relevant invitee::

    [{"invitees":[{invitee1}, {invitee2}, ...], work},{"invitees":[{invitee4}, {invitee5}, ...], work2}, ...]

Example files can be found here: `works.json <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/docs/examples/works.json>`_ and `works.yaml <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/docs/examples/works.yaml>`_, while any uploaded works file will be validated against the `works schema in YAML <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/work_schema.yaml>`_.

For more information on the structure of the works files see here: `Works schema for ORCID API 2.0/2.1 </works_schema.html>`_

