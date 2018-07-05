.. _writing_affiliation_items:

Writing affiliation items
^^^^^^^^^^^^^^^^^^^^^^^^^

The task of writing affiliations is intended to be easy, i.e.,

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.
* the Hub then either sends the people identified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

As the structure of affiliations in the ORCID Message Schema is relatively simple, this information can be conveyed in csv or tsv formatted files with the Hub accepting either.
The file should be constructed with the first row containing only headers, with the following headers recognized:

Required
--------

+-----------------------+-------------------------------------------------------+
| Header                | Description                                           |
+=======================+=======================================================+
| Affiliation type      | A value to indicate whether to write the affiliation  |
|                       | to education or employment ("staff" or "student").    |
+-----------------------+-------------------------------------------------------+
| Email                 | The institutional email for the individual, and where |
|                       | the invitation will be sent if they're not already    |
|                       | known in the Hub for your organisation.               |
+-----------------------+-------------------------------------------------------+
| First name            | If the user does not have an ORCID iD, this field     |
+-----------------------+ together with 'Last name' and email, will be used to  |
| Last name             | pre-fill creation of an ORCID record.                 |
+-----------------------+-------------------------------------------------------+

Optional
--------

+-----------------------+-------------------------------------------------------+
| Header                | Description                                           |
+=======================+=======================================================+
| Identifier            | This can be any identifier used in your internal      |
|                       | systems and is to allow you to match the resulting    |
|                       | put-code from ORCID. To simplify making an update     |
|                       | to the item in the future.                            |
+-----------------------+-------------------------------------------------------+
| ORCID iD              | Once it has been authenticated, an ORCID iD can be    |
|                       | used instead of an email address; however, without an |
|                       | email address any invitation required cannot be sent. |
+-----------------------+-------------------------------------------------------+
| Organisation          | The organisation of the affiliation. NB you should    |
|                       | only write affiliations for organisations that know   |
|                       | to be true.                                           |
+-----------------------+-------------------------------------------------------+
| Department            | Where appropriate, the name of the department in the  |
|                       | the organisation.                                     |
+-----------------------+-------------------------------------------------------+
| City                  | The city of the department or organisation.           |
+-----------------------+-------------------------------------------------------+
| Region                | Where appropriate, the region (e.g. state)            |
+-----------------------+-------------------------------------------------------+
| Course                | For an education item, the course of study            |
| or Title              | or degree name; for an employment item, the name of   |
|                       | the role or a job title.                              |
+-----------------------+-------------------------------------------------------+
| Start date            | The affiliation's start date in ISO 8601 format to    |
|                       | desired/known level of precision.                     |
+-----------------------+-------------------------------------------------------+
| End date              | The affiliation end date in ISO 8601 format, leave    |
|                       | blank or omit for ongoing affiliations.               |
+-----------------------+-------------------------------------------------------+
| Country               | Two-letter country code in ISO 3166-1 alpha-2 format  |
|                       | and only necessary if different to your home campus's |
|                       | country code.                                         |
+-----------------------+-------------------------------------------------------+
| Disambiguated ID      | If different to your home campus's ID, the identifier |
|                       | for the organisation as given by the accompanying     |
|                       | Disambiguation Source.                                |
+-----------------------+-------------------------------------------------------+
| Disambiguation Source | Required if a Disambiguated ID is provided, and must  |
|                       | be one of: RINGGOLD; FUNDREF; or GRID.                |
+-----------------------+-------------------------------------------------------+

Headers that aren't controlled by you
-------------------------------------

+-----------------------+-------------------------------------------------------+
| Header                | Description                                           |
+=======================+=======================================================+
| Put-Code              | This is an integer that ORCID creates to identify the |
|                       | item and its place in the ORCID record. It is         |
|                       | returned to you in the Hub's affiliation report.      |
+-----------------------+-------------------------------------------------------+
| Visibility            | Ignored if included when writing the affiliation, but |
|                       | returned to you in the Hub's affiliation report as    |
|                       | is specified by the ORCID record holder.              |
+-----------------------+-------------------------------------------------------+

With a put-code the Hub attempts to overwrite an item; while without one, a new item is created together with a new put-code that is unique within
the ORCID record and section, i.e., it is possible for different ORCID records to have the same put-code for different items, and even, in rare cases,
for items in differnt sections of the same ORCID record (e.g. employment and education) to have the same put-code.

Notes
-----

Each record in the the affiliation file must contain either an email address or, **if** an individual has already gone through the Hub, an ORCID iD.
Dates are preferred in ISO 8601 format, i.e., **YYYY-MM-DD** with partial dates accepted, e.g, "2017", "2017-12", and "2017-12-15" are all valid;
however, the Hub will try to interpret any dates provided.

Where a field header or value is not provided, the value from your organisation will be used if it's available, e.g., Organisation, City, Country,
Disambiguation ID, and Disambiguation Source can be omitted where redundant.  This is why the Hub can write affilations without you specifying
the fields that ORCID requires for the message, i.e., organization, city and country.

NB as Excel's csv format will silently corrupt any unicode (e.g., vowels with macrons), the tsv format is recommended for those creating their files out of Excel. The easiest way to get a unicode .tsv file from Excel is to "Save As" type "Unicode Text (\*.txt)" and then rename the file's suffix to ".tsv".

Example files can be found here: :ref:`affiliation-entry-example-csv` and :ref:`affiliation-entry-example-tsv`.

.. _affiliation-entry-example-csv:

Example affiliation task in csv
-------------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_affiliations.csv
        :language: none

You can download **example_affiliations.csv** :download:`here <./examples/example_affiliations.csv>`.

.. _affiliation-entry-example-tsv:

Example affiliation task in tsv
-------------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_affiliations.csv
        :language: none

You can download **example_affiliations.tsv** :download:`here <./examples/example_affiliations.tsv>`.
