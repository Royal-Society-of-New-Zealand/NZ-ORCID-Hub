.. _writing_works_items:

Writing works items
^^^^^^^^^^^^^^^^^^^

The task of writing works is very similar to writing affiliations, i.e.,

* a batch file containing information to be written to ORCID records, together with the email or ORCID iD of the researcher/contributors to be affected, is uploaded to the Hub.
* the Hub then either sends the people identified email invitations and/or uses the access tokens it already has to write the information to their ORCID records.

The main difference in writing works is that while affiliation files are simple and can thus be given as either csv or tsv format, works in ORCID are more complex requiring a structured file format such as the json or YAML formats to convey.
The Hub accepts batches of works items where each item contains an initial invitees block (detailing the names, email, and optionally ORCID iD and put-code for each individual to be affected) and following that invitee block, the data to be written to each invitee's ORCID record.  The work data must comply with the structure of the ORCID V2.0/V2.1 works schema, but omit put-code.  If the task describes an update to existing information in a users ORCID record the put-code will not apply to all invitees; instead specify each put-code in the data of the relevant invitee::

    [{"invitees":[{invitee1}, {invitee2}, ...], work},{"invitees":[{invitee4}, {invitee5}, ...], work2}, ...]

Example files can be found here: :ref:`works-entry-example-json` and :ref:`works-entry-example-yaml`, while any uploaded works file will be validated against the :ref:`works-schema`.

For more information and guidance on the structure expected of works task files see here: `Works schema for ORCID API 2.0/2.1 <works_schema.html>`_

.. _works-entry-example-json:

Example works task in json
--------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_works.json
        :language: json

You can download **example_works.json** :download:`here <./examples/example_works.json>`.

.. _works-entry-example-yaml:

Example works task in yaml
--------------------------

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: examples/example_works.yaml
        :language: yaml

You can download **example_works.yaml** :download:`here <./examples/example_works.yaml>`.

.. _works-schema:

work_schema.yaml
----------------

Any works task file that is uploaded is first validated against the work_schema.yaml

.. container:: toggle

    .. container:: header

        **Show/Hide Code**

    .. literalinclude:: ../work_schema.yaml
        :language: yaml

You can download **work_schema.yaml** :download:`here <../work_schema.yaml>`.
