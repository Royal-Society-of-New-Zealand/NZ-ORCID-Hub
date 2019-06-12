# -*- coding: utf-8 -*-
"""JSON Schemas."""

affiliation_record = {
    "title": "AffiliationRecord",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "put-code": {"type": ["string", "null", "integer"]},
        "local-id": {"type": ["string", "null"]},
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
        "url": {"type": ["string", "null"]},
        "visibility": {"type": ["string", "null"]},
        "display_index": {"type": ["string", "null"]},
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

hub_user = {
    "title": "HubUser",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "name": {"type": ["string", "null"]},
        "orcid": {
            "type": ["string", "null"],
            "format": "^[0-9]{4}-?[0-9]{4}-?[0-9]{4}-?[0-9]{4}$",
        },
        "email": {"type": ["string", "null"], "format": ".{1,}@.{1,}"},
        "eppn": {"type": ["string", "null"]},
        "confirmed": {"type": ["boolean", "null"]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
    },
    "anyOf": [{"required": ["email"]}, {"required": ["orcid"]}]
}


other_id_record = {
    "title": "OtherIdRecord",
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "put-code": {"type": ["string", "null", "integer"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "type": {"type": ["string", "null"]},
        "value": {"type": ["string", "null"]},
        "url": {"type": ["string", "null"]},
        "relationship": {"type": ["string", "null"]},
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
            "required": ["type", "value", "url", "relationship", "email"]
        },
        {
            "required": ["type", "value", "url", "relationship", "orcid"]
        },
        {
            "required": ["external-id-type", "external-id-value", "external-id-url", "external-id-relationship",
                         "email"]
        },
        {
            "required": ["external-id-type", "external-id-value", "external-id-url", "external-id-relationship",
                         "orcid"]
        }
    ]
}

other_id_record_list = {
    "type": "array",
    "items": other_id_record
}

other_id_task = {
    "title": "OtherIDTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {"type": ["string", "null"], "enum": ["OTHER_ID", "OTHER ID", ]},
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": other_id_record_list,
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

property_record = {
    "title": "PropertyRecord",
    "type": "object",
    "properties": {
        "id": {"type": ["integer", "null"]},
        "type": {
            "type": ["string", "null", "integer"],
            "enum": ["URL", "NAME", "KEYWORD", "COUNTRY", "url", "name", "keyword", "country", None]
        },
        "put-code": {"type": ["string", "null", "integer"]},
        "is-active": {"type": "boolean"},
        "email": {"type": ["string", "null"]},
        "first-name": {"type": ["string", "null"]},
        "last-name": {"type": ["string", "null"]},
        "name": {"type": ["string", "null"]},
        "value": {"type": ["string", "null"]},
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
            "required": ["url-name", "url-value", "email"]
        },
        {
            "required": ["url-name", "url-value", "orcid"]
        },
        {
            "required": ["type", "value", "email"]
        },
        {
            "required": ["type", "value", "orcid"]
        },
        {
            "required": ["content", "email"]
        },
        {
            "required": ["content", "orcid"]
        },
        {
            "required": ["name", "value", "email"]
        },
        {
            "required": ["name", "value", "orcid"]
        },
        {
            "required": ["country", "email"]
        },
        {
            "required": ["country", "orcid"]
        },
    ]
}

property_record_list = {
    "type": "array",
    "items": property_record,
}

property_task = {
    "title": "OtherNameTask",
    "type": "object",
    "properties": {
        "id": {"type": "integer", "format": "int64"},
        "filename": {"type": ["string", "null"]},
        "task-type": {
            "type": ["string", "null"],
            "enum": ["PROPERTY", "OTHER_NAME", "OTHER NAME", "KEYWORD"]
        },
        "created-at": {"type": ["string", "null"], "format": "date-time"},
        "updated-at": {"type": ["string", "null"], "format": "date-time"},
        "expires-at": {"type": ["string", "null"], "format": "date-time"},
        "completed-at": {"type": ["string", "null"], "format": "date-time"},
        "records": property_record_list,
    },
    "required": ["records"]
}
