.. _writing_funding_items:

Writing funding items
^^^^^^^^^^^^^^^^^^^^^

The task of writing funding works very similarly to writing affiliations, i.e., 

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.  
* the Hub then either sends the people identitified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

The main difference in writing funding is that while affiliation files are simple and can thus be given as either csv or tsv format, funnding in ORCID is more complex requiring a structured file format such as the json or YAML formats to convey. The Hub accepts batches of funding items where each item contains an initial invitees block (detailing the names, email, and optionally ORCID iD and put-code for each individual to be affected) and following that invitee block, the data to be written to each invitee's ORCID record. The funding data must comply with the structure of the ORCID V2.0/V2.1 funding schema, but omit put-code. If the task describes an update to existing information in a users ORCID record the put-code will not apply to all invitees; instead specify each put-code in the data of the relevant invitee:::

    [{"invitees":[{invitee1}, {invitee2}, ...], funding},{"invitees":[{invitee4}, {invitee5}, ...], funding2}, ...]

Example files can be found in the project's `JIRA issue relating to this task <https://jira.auckland.ac.nz/browse/ORCIDHUB-274>`_, while any uploaded funding file will be validated against the `funding schema in YAML <https://github.com/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/blob/master/funding_schema.yaml>`_.

Each invitee is specified as:

:first-name: 
    required - if the user does not have an ORCID iD, this field together with 'Last name' and email, will be used to pre-fill ORCID registration
:last-name: required
:\email: the institutional email for the individual, and where the invitation will be sent if they're not known by the Hub
:ORCID-iD: once it has been authenticated, an ORCID iD can be used instead of an email address; however, without an email address any invitation required cannot be sent
:identifier: this can be any identifier used in your internal systems and is to allow you to match the resulting put-code from ORCID to simplify making future updates to the item
:put-code: this is a numeric code which identifies the item in the ORCID registryu, and is returned to you in the Hub's funding report once the item has been successfully written. 
    With a put-code the Hub attempts to overwrite an item; while without one, a new item is created having a new put-code
