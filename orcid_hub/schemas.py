# -*- coding: utf-8 -*-
"""JSON Schemas."""

affiliation_record = {
    "title": "AffiliationRecord",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "put-code": {"type": ["string", "null", "integer"]},
        "external-id": {"type": ["string", "null"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "role": {"type": ["string", "null"]},
        "organisation": {"type": ["string", "null"]},
        "department": {"type": ["string", "null"]},
        "city": {"type": ["string", "null"]},
        "state": {"type": ["string", "null"]},
        "country": {"type": ["string", "null"]},
        "disambiguated-id": {"type": ["string", "null"]},
        "disambiguated-source": {"type": ["string", "null"]},
        "affiliation-type": {"type": ["string", "null"]},
        "start-date": {"type": ["string", "null"]},
        "end-date": {"type": ["string", "null"]},
        "processed-at": {"type": ["string", "null"], "format": "date-time"},
        "status": {"type": ["string", "null"]},
        "orcid": {
            "type": ["string", "null"],
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        }
    },
    "required": ["email", "first-name", "last-name", "affiliation-type"]
}

affiliation_task = {
    "title": "AffiliationTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {"type": ["string", "null"], "enum": ["AFFILIATION", "FUNDING", ]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": {
            "type": "array",
            "items": affiliation_record
        },
    },
    "required": ["records"]
}

researcher_url_record = {
    "title": "ResearcherUrlRecord",
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "put-code": {"type": ["string", "null", "integer"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "name": {"type": ["string", "null"]},
        "value": {"type": ["string", "null"]},
        "display-index": {"type": ["string", "null", "integer"]},
        "visibility": {"type": ["string", "null"]},
        "processed-at": {"type": ["string", "null"], "format": "date-time"},
        "status": {"type": ["string", "null"]},
        "orcid": {
            "type": ["string", "null"],
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        }
    },
    "anyOf": [
        {
            "required": ["name", "value", "email"]
        },
        {
            "required": ["name", "value", "orcid"]
        },
        {
            "required": ["url-name", "url-value", "email"]
        },
        {
            "required": ["url-name", "url-value", "orcid"]
        }
    ]
}

researcher_url_record_list = {
    "type": "array",
    "items": researcher_url_record
}

researcher_url_task = {
    "title": "ResearcherUrlTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {"type": ["string", "null"], "enum": ["RESEARCHER_URL", "RESEARCHER URL", ]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": researcher_url_record_list,
    },
    "required": ["records"]
}

other_name_keyword_record = {
    "title": "OtherNameRecord",
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "put-code": {"type": ["string", "null", "integer"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "content": {"type": ["string", "null"]},
        "display-index": {"type": ["string", "null", "integer"]},
        "visibility": {"type": ["string", "null"]},
        "processed-at": {"type": ["string", "null"], "format": "date-time"},
        "status": {"type": ["string", "null"]},
        "orcid": {
            "type": ["string", "null"],
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        }
    },
    "anyOf": [
        {
            "required": ["content", "email"]
        },
        {
            "required": ["content", "orcid"]
        }
    ]
}

other_name_keyword_record_list = {
    "type": "array",
    "items": other_name_keyword_record,
}

other_name_keyword_task = {
    "title": "OtherNameTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {"type": ["string", "null"], "enum": ["OTHER_NAME", "OTHER NAME", "KEYWORD"]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": other_name_keyword_record_list,
    },
    "required": ["records"]
}
