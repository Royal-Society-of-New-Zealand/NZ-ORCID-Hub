# NZ-ORCID-Hub [![Build Status](https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub.svg?branch=master)](https://travis-ci.org/Royal-Society-of-New-Zealand/NZ-ORCID-Hub)[![Coverage Status](https://coveralls.io/repos/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub/badge.svg?branch=HEAD)](https://coveralls.io/github/Royal-Society-of-New-Zealand/NZ-ORCID-Hub?branch=HEAD)[![RTD Status](https://readthedocs.org/projects/nz-orcid-hub/badge/)](http://docs.orcidhub.org.nz/)

Work undertaken as part of the MBIE-led ORCID Working Group confirmed the view that New Zealand's research organisations exist in a wide range of sizes and ability to access IT support. As a consequence, the ability of organisations to respond to the ORCID Joint Statement of Principle that New Zealand adopt ORCID as the national researcher identifier also varied widely. In recognition that assisting all Consortia-eligible organisations to productively engage with ORCID would lead to national benefits, the Ministry has provided support for the development of the New Zealand ORCID Hub. As designed, the core function of the Hub is to provide all New Zealand ORCID Consortium members with the ability to make authoritative assertions of their relationship with researchers on the researcher's ORCID record, irrespective of their size or technical resource.

Throughout 2017 to June 2018, this project is being developed by a team at the University of Auckland under contract to the Royal Society of New Zealand. As the phenomena of small research organisations is not limited to New Zealand, it is a principle of the Hub's development that it be architected for use by the global ORCID community. To support this design principle, development is being pursued in as transparent a nature as possible, with the Hub itself being developed under the permissive MIT License.

The core development team at the University of Auckland consists of: jeff kennedy, Enterprise Architecture Manager; Radomirs Cirskis, ORCID Project Architect; and Roshan Pawar, ORCID Developer.

At this stage of the Hub's development it currently operates in two modes: Tuakiri-member organisation login; and file upload (typically associated with an email invitation for researchers with non-Tuakiri member organisations).

The Tuakiri login flow takes the information presented as part of the log in process and uses this to write a minimal affiliation of organisation, city, country and employment/education. The benefit of the Tuakiri-style is that the affiliation is written though researcher interaction, with anyone having credentials at a Tuakiri-member organisation able to initiate this process. This process is also very secure as the user's email and EPPN is authenticated as part of the exchange
The File upload flow uses additional data provided by the organisation to write richer affiliations. If the user has already logged in with Tuakiri, the affiliation written replaces the minimal affiliation item. If the Hub has no record of the individual, an email invitation is sent asking permission to write to their ORCID record, with receipt of permission resulting in the record being updated. The advantage of this flow is that fewer user interactions are required, and the result is typically a richer affiliation. It's also the only way non-Tuakiri members have for interacting with the Hub. The disadvantage is that the ability of the user to receive the invitation is the only assurance of the user's identity.
The Hub has been awarded the following Collect and Connect badges recognising it follows ORCID's recommendations for integrating with ORCID in these stages:

![ORCID Badge 00 AUTHENTICATE](https://orcidhub.org.nz/static/images/ORCID-Badge-00-s-AUTHENTICATE.png)
![ORCID Badge 01 COLLECT](https://orcidhub.org.nz/static/images/ORCID-Badge-01-s-COLLECT.png)
![ORCID Badge 02 DISPLAY](https://orcidhub.org.nz/static/images/ORCID-Badge-02-s-DISPLAY.png)
![ORCID Badge 03 CONNECT](https://orcidhub.org.nz/static/images/ORCID-Badge-03-s-CONNECT.png)

Consortium members who use the NZ ORCID Hub and who provide adequate communications to their users about what ORCID is, why its use is being encouraged within the organisation and how it is being used in the organisation’s internal systems are also eligible for these four badges.

For more information on the Hub's background and links to resources please visit the Hub page of the Royal Society Te Apārangi’s website.

##### Contact Details

Royal Society of New Zealand
Phone: +64 (04) 472 7421
PO Box 598, Wellington 6140
New Zealand
Email: orcid@royalsociety.org.nz
