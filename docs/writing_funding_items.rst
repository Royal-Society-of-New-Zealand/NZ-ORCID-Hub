.. _writing_funding_items:

Writing funding items
^^^^^^^^^^^^^^^^^^^^^

The task of writing funding is very similar to writing affiliations, i.e.,

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.
* the Hub then either sends the people identified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

The main difference in writing funding is that while affiliation files are simple and can thus be given as either csv or tsv format, funding items in ORCID
are more complex requiring a structured file format such as the json or YAML formats to convey.
The Hub accepts batches of funding items where each item contains an initial invitees block
(detailing the names, email, and optionally ORCID iD and put-code for each individual to be affected) and following that invitee block, the data to be written to each invitee's ORCID record.
The funding data must comply with the structure of the ORCID V2.0/V2.1 funding schema, but omit put-code.
If the task describes an update to existing information in a users ORCID record the put-code will not apply to all invitees;
instead specify each put-code in the data of the relevant invitee::

    [{"invitees":[{invitee1}, {invitee2}, ...], funding},{"invitees":[{invitee4}, {invitee5}, ...], funding2}, ...]

Example files can be found here: :ref:`funding-entry-example-json` and :ref:`funding-entry-example-yaml`, while any uploaded funding file will be validated against the :ref:`funding-schema`.

For more information and guidance on the structure expected of funding task files see here: `Funding schema for ORCID API 2.0/2.1 <fundings_schema.html>`_

.. _funding-entry-example-json:

Example funding task in json
----------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_fundings.json
        :language: json

You can download **example_fundings.json** :download:`here <./examples/example_fundings.json>`.

.. _funding-entry-example-yaml:

Example funding task in yaml
----------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_fundings.yaml
        :language: yaml

You can download **example_fundings.yaml** :download:`here <./examples/example_fundings.yaml>`.

.. _funding-schema:

funding_schema.yaml
-------------------

Any funding task file that is uploaded is first validated against the funding_schema.yaml

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: ../funding_schema.yaml
        :language: yaml

You can download **funding_schema.yaml** :download:`here <../funding_schema.yaml>`.
