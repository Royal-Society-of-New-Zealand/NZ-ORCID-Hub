# -*- coding: utf-8 -*-
"""Helpers for testing."""

import json
from orcid_hub import orcid_client


def get_profile(org=None, user=None):
    """Mock ORCID profile api call."""
    orcid = user.orcid if user else "0000-0003-1255-9023"
    if org and org.orcid_client_id:
        client_id = org.orcid_client_id
    else:
        client_id = "APP-5ZVH4JRQ0C27RVH5"
    resp = {
        "person": {
            "other-names": {
                "other-name": [
                    {
                        "source": {
                            "source-client-id": {
                                "uri": f"https://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "content": "dummy 4",
                        "visibility": "PUBLIC",
                        "path": f"/{orcid}/other-names/16871",
                        "put-code": 16871,
                        "display-index": 2
                    }
                ],
                "path": f"/{orcid}/other-names"
            },
            "keywords": {
                "keyword": [
                    {
                        "source": {
                            "source-client-id": {
                                "uri": f"https://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "content": "xyz",
                        "visibility": "PUBLIC",
                        "path": f"/{orcid}/keywords/43944",
                        "put-code": 43944,
                        "display-index": 0
                    }
                ],
                "path": f"/{orcid}/keywords"
            },
            "researcher-urls": {
                "researcher-url": [
                    {
                        "source": {
                            "source-client-id": {
                                "uri": f"http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "url-name": "xyzurl",
                        "url": {
                            "value": "https://fb.com"
                        },
                        "visibility": "PUBLIC",
                        "path": f"/{orcid}/researcher-urls/43944",
                        "put-code": 43944,
                        "display-index": 0
                    }
                ],
                "path": f"/{orcid}/researcher-urls"
            },
            "addresses": {
                "address": [
                    {
                        "source": {
                            "source-client-id": {
                                "uri": f"http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "country": {
                            "value": "NZ"
                        },
                        "visibility": "PUBLIC",
                        "path": f"/{orcid}/address/5373",
                        "put-code": 5373,
                        "display-index": 0
                    }
                ],
                "path": f"/{orcid}/address"
            },
            "external-identifiers": {
                "external-identifier": [
                    {
                        "source": {
                            "source-client-id": {
                                "uri": f"http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "external-id-type": "cba",
                        "external-id-value": "dfdsfd",
                        "external-id-url": {
                            "value": "dfsdfs"
                        },
                        "external-id-relationship": "SELF",
                        "visibility": "PUBLIC",
                        "path": f"/{orcid}/external-identifiers/5373",
                        "put-code": 5373,
                        "display-index": 0
                    }
                ],
                "path": f"/{orcid}/external-identifiers"
            },
            "path": f"/{orcid}/person"
        },
        'activities-summary': {
            'educations': {
                "affiliation-group": [
                    {
                        "summaries": [
                            {
                                'education-summary': {
                                    "created-date": {
                                        "value": 1532322530230
                                    },
                                    "last-modified-date": {
                                        "value": 1532322530230
                                    },
                                    "source": {
                                        "source-client-id": {
                                            "uri": f"http://sandbox.orcid.org/client/{client_id}",
                                            "path": client_id,
                                            "host": "sandbox.orcid.org"
                                        },
                                        "source-name": {
                                            "value": "The University of Auckland - MyORCiD"
                                        }
                                    },
                                    "department-name": "",
                                    "role-title": "ROLE",
                                    "start-date": {
                                        "year": {"value": "1996"},
                                        "month": {"value": "11"}},
                                    "end-date": {
                                        "year": {"value": "2019"},
                                        "month": {"value": "02"},
                                        "day": {"value": "29"}},
                                    "organization": {
                                        "name": "The University of Auckland",
                                        "address": {
                                            "city": "Auckland",
                                            "region": "Auckland",
                                            "country": "NZ"
                                        },
                                        "disambiguated-organization": {
                                            "disambiguated-organization-identifier": "123456",
                                            "disambiguation-source": "RINGGOLD"
                                        }
                                    },
                                    "visibility": "PUBLIC",
                                    "put-code": 1,
                                    "path": f"/{orcid}/education/1"
                                }
                            }
                        ]
                    }
                ],
                'path':
                    f"/{orcid}/educations"
            },
            "employments": {
                "affiliation-group": [
                    {
                        "summaries": [
                            {
                                "employment-summary": {
                                    "source": {
                                        "source-client-id": {
                                            "uri": "http://sandbox.orcid.org/client/{client_id}",
                                            "path": client_id,
                                            "host": "sandbox.orcid.org"
                                        },
                                        "source-name": {
                                            "value": "The University of Auckland - MyORCiD"
                                        }
                                    },
                                    "department-name": None,
                                    "role-title": None,
                                    "start-date": None,
                                    "end-date": None,
                                    "organization": {
                                        "name": "The University of Auckland",
                                        "address": {
                                            "city": "Auckland",
                                            "region": None,
                                            "country": "NZ"
                                        },
                                        "disambiguated-organization": None
                                    },
                                    "visibility": "PUBLIC",
                                    "put-code": 2,
                                    "path": f"/{orcid}/employment/2"
                                }
                            }
                        ]
                    }
                ],
                "path":
                    f"//employments"
            },
            "invited-positions": {
                "last-modified-date": None,
                "affiliation-group": [

                ],
                "path": f"/{orcid}/invited-positions"
            },
            "memberships": {
                "last-modified-date": None,
                "affiliation-group": [

                ],
                "path": f"/{orcid}/memberships"
            },
            "qualifications": {
                "last-modified-date": None,
                "affiliation-group": [

                ],
                "path": f"/{orcid}/qualifications"
            },
            "services": {
                "last-modified-date": None,
                "affiliation-group": [

                ],
                "path": f"/{orcid}/services"
            },
            "distinctions": {
                "last-modified-date": None,
                "affiliation-group": [

                ],
                "path": f"/{orcid}/distinctions"
            },
            'fundings': {
                'last-modified-date': {
                    'value': 1513136293368
                },
                'group': [{
                    'last-modified-date': {
                        'value': 1513136293368
                    },
                    'external-ids': {
                        'external-id': [{
                            'external-id-type': 'grant_number',
                            'external-id-value': 'GNS1701',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }, {
                            'external-id-type': 'grant_number',
                            'external-id-value': '17-GNS-022',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }]
                    },
                    "funding-summary": [{
                        "created-date": {
                            "value": 1511935227017
                        },
                        "last-modified-date": {
                            "value": 1513136293368
                        },
                        "source": {
                            "source-client-id": {
                                "uri": "http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "title": {
                            "title": {
                                "value": "Probing the crust with zirco"
                            },
                            "translated-title": {
                                "value": "नमस्ते",
                                "language-code": "hi"
                            }
                        },
                        "type": "CONTRACT",
                        "start-date": None,
                        "end-date": {
                            'year': {
                                'value': '2025'
                            },
                            'month': None,
                            'day': None
                        },
                        "organization": {
                            "name": "Royal Society Te Apārangi"
                        },
                        "put-code": 9597,
                        "path": f"/{orcid}/funding/9597"
                    }]
                }],
                'path':
                    '/0000-0002-3879-2651/fundings'
            },
            "peer-reviews": {
                "group": [{
                    "external-ids": {
                        "external-id": [{
                            "external-id-type": "peer-review",
                            "external-id-value": "issn:12131",
                            "external-id-url": None,
                            "external-id-relationship": None
                        }]
                    },
                    "peer-review-summary": [{
                        "source": {
                            "source-client-id": {
                                "uri": "http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "external-ids": {
                            "external-id": [{
                                "external-id-type": "source-work-id",
                                "external-id-value": "122334",
                                "external-id-url": {
                                    "value": "https://localsystem.org/1234"
                                },
                                "external-id-relationship": "SELF"
                            }]
                        },
                        "review-group-id": "issn:12131",
                        "convening-organization": {
                            "name": "The University of Auckland",
                            "address": {
                                "city": "Auckland",
                                "region": "Auckland",
                                "country": "NZ"
                            },
                            "disambiguated-organization": None
                        },
                        "visibility": "PUBLIC",
                        "put-code": 2622,
                    }]
                }],
                "path":
                    f"/{orcid}/peer-reviews"
            },
            'works': {
                'group': [{
                    'external-ids': {
                        'external-id': [{
                            'external-id-type': 'grant_number',
                            'external-id-value': 'GNS1701',
                            'external-id-url': None,
                            'external-id-relationship': 'SELF'
                        }]
                    },
                    "work-summary": [{
                        "source": {
                            "source-client-id": {
                                "uri": "http://sandbox.orcid.org/client/{client_id}",
                                "path": client_id,
                                "host": "sandbox.orcid.org"
                            },
                            "source-name": {
                                "value": "The University of Auckland - MyORCiD"
                            }
                        },
                        "title": {
                            "title": {
                                "value": "Test titile2"
                            },
                            "translated-title": {
                                "value": "नमस्ते",
                                "language-code": "hi"
                            }
                        },
                        'type': 'BOOK_CHAPTER',
                        'put-code': 9597,
                        'path': f"/{orcid}/works/9597"
                    }]
                }],
                "path":
                    f"/{orcid}/works"
            },
            "path": f"/{orcid}/activities"
        },
        "path": f"/{orcid}"
    }
    return json.loads(json.dumps(resp), object_pairs_hook=orcid_client.NestedDict)
