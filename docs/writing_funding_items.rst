.. _writing_funding_items:

Writing funding items
^^^^^^^^^^^^^^^^^^^^^

Writing funding works very similarly to affiliations, i.e., a funding file containing the email or ORCID iD of researcher/contributors and funding data is uploaded to the Hub and the Hub either sends the researcher/contributor invitations or uses the access token it already has to write the information to their ORCID records.

The main difference is that while affiliation files can be either csv or tsv, for funding the file must be in either json or YAML formats.  The Hub accepts these files structured in the same way as the ORCID 2.0/2.1 schema, and the contributors block is where each individual to be invited/written is specified.

