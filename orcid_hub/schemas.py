# -*- coding: utf-8 -*-
"""JSON Schemas."""

affiliation_record_schema = {
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

affiliation_task_schema = {
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
            "items": affiliation_record_schema
        },
    },
    "required": ["records"]
}

researcher_url_record_schema = {
    "title": "ResearcherUrlRecord",
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "put-code": {"type": ["string", "null", "integer"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "url-name": {"type": ["string", "null"]},
        "url-value": {"type": ["string", "null"]},
        "display-index": {"type": ["string", "null", "integer"]},
        "visibility": {"type": ["string", "null"]},
        "processed-at": {"type": ["string", "null"], "format": "date-time"},
        "status": {"type": ["string", "null"]},
        "orcid": {
            "type": ["string", "null"],
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        }
    },
    "required": ["email", "first-name", "last-name", "url-name", "url-value"]
}

researcher_url_task_schema = {
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
        "records": {
            "type": "array",
            "items": researcher_url_record_schema
        },
    },
    "required": ["records"]
}

other_name_record_schema = {
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
    "required": ["email", "first-name", "last-name", "content"]
}

other_name_task_schema = {
    "title": "OtherNameTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {"type": ["string", "null"], "enum": ["OTHER_NAME", "OTHER NAME", ]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": {
            "type": "array",
            "items": other_name_record_schema
        },
    },
    "required": ["records"]
}
