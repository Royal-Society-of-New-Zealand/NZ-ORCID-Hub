# Batch peer review schema in the NZ ORCID Hub for ORCID Message Schema v2.0/v2.1

Batch peer review files to be passed through the Hub must be presented in either of the json or YAML formats, with the files following the convention for complex Hub objects, i.e.:
* a list of items
  * with each item comprised of:
    * a list of invitees (i.e., the individuals whose ORCID records are to be affected); and,
    * the ORCID Message data that is to be asserted to each invitee's ORCID record

Examples can be found here: [**peer_reviews.json**](_downloads/example_peer_reviews.json) and [**peer_reviews.yaml**](_downloads/example_peer_reviews.yaml)

A guide to peer review assertion in V2.1 of the ORCID API can be found here [ORCID API v2.1 Peer Review Guide](https://github.com/ORCID/ORCID-Source/blob/master/orcid-model/src/main/resources/record_2.1/peer-review-guide-v2.1.md)

The Hub will consume any json or YAML file complying to the following schema.  NB additional validation will be performed when the data is sent to ORCID, and any errors in the message will be reported in the item's status field in the Hub's UI or task report.

## Peer Reviews

### Properties
Type | Description | Notes
------------- | ------------- | -------------
[**list[peer_review]**](#peer_review) | Container for the peer review item(s) to be written | [required]


## Peer Review

Minimum one - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invitees** | [**list[invitee]**](#invitee) | Container for individuals to be affected | [required]
**created-date** | [**CreatedDate**](#createddate-and-lastmodifieddate) | Container for work item's creation date | [optional, ignored]
**last-modified-date** | [**LastModifiedDate**](#createddate-and-lastmodifieddate) | Container for work item's last modification date | [optional, ignored]
**source** | [**Source**](#source) | Container for when/how the item was asserted | [optional, ignored]
**reviewer-role** | **str** | The role played by a person in their contribution to a review | "CHAIR", "EDITOR", "MEMBER", "ORGANIZER" or "REVIEWER" [required]
**review-identifiers** | [**list[external-id]**](#external-id) | Container for identifiers for the review | Used to group reviews [required]
**review-url** | [**Url**](#url) | Container for a url representation of the review | [optional]
**review-type** | **str** | The kind of review applied to the subject type reviewed | "REVIEW" or "EVALUATION" [required]
**review-completion-date** | [**ReviewCompletionDate**](#reviewcompletiondate) | The date on which the review was completed, given to any level of specificity | [optional]
**review-group-id** | **str** | Identifier for the group that this review should be a part of for aggregation purposes. | This review-group-id must be pre-registered [required]
**subject-external-identifier** | [**list[external-id]**](#external-id) | Container for the unique IDs of the object that was reviewed | [optional]
**subject-container-name** | [**SubjectContainerName**](#subjectcontainername) | Container for the name of the journal, conference, grant review panel, or other applicable object of which the review subject was a part | [optional]
**subject-type** | **str** | The object type of the review subject | See [here](https://members.orcid.org/api/resources/work-types) for the 38 allowed types [optional]
**subject-name** | [**SubjectName**](#subjectname) | Container for the name(s) of the object that was reviewed | [optional]
**subject-url** | [**Url**](#url) | Container for a url representation of the object reviewed | [optional]
**convening-organization** | [**ConveningOrganization**](#conveningorganization) | Container for information about the organization convening the review | [required]

[**back to Peer Reviews**](#peer-reviews)

## Invitee

Minimum one - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**identifier** | **str** | Internal identifier from your system for the funding-person relationship | [optional]
**first-name** | **str** | First name to assist ORCID iD registration | [required]
**last-name** | **str** | Last name to assist ORCID iD registration | [required]
**email** | **str** | The email address any permissions request will be sent to | [required unless Hub-known ORCID-iD present]
**ORCID-iD** | **str** | ORCID path (16-character identifier) of the ORCID iD | [optional unless no email]
**put-code** | **int** | If present the Hub will attempt to update an existing item | [optional]
**visibility** | **str** | The privacy level chosen by record holder for this item | "PUBLIC", "LIMITED" or "PRIVATE" [optional, ignored]

[**back to Peer Review**](#peer-review)

## CreatedDate and LastModifiedDate

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **datetime** | Milliseconds of the event that have elapsed since midnight 1970-01-01 | [optional]

[**back to Peer Review**](#peer-review)

## Source

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source-orcid** | [**SourceOrcid**](#sourceorcid-and-sourceclientid) | For legacy client applications, the ORCID iD that created the item | [optional]
**source-client-id** | [**SourceClientId**](#sourceorcid-and-sourceclientid) | The client id of the application that created the item | [optional]
**source-name** | [**SourceName**](#sourcename) | Container for the human-readable name of the client application | [optional]

[**back to Peer Review**](#peer-review)

## SourceOrcid and SourceClientId

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | Source iD in URI form, i.e., URL + path | [optional]
**path** | **str** | Application's 16-character client id or legacy ORCID iD | [optional]
**host** | **str** | URL for the environment of the Source iD, i.e., https://sandbox.orcid.org or https://orcid.org | [optional]

[**back to Source**](#source)

## SourceName

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The human-readable name of the client application | [optional]

[**back to Source**](#source)

## External ID

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id-type** | **str** | The type of the given external identifier | see [here](https://pub.orcid.org/v2.0/identifiers) for supported identifier types [required]
**external-id-value** | **str** | A reference to an external identifier to the review/subject | [required]
**external-id-url** | [**Url**](#url) | A container for the url value | [optional]
**external-id-relationship** | **str** | The relationship of this identifier to the review/subject | "SELF" or "PART-OF" [optional]

[**back to Peer Review**](#peer-review)

## Url

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | An external url for the review/subject or as specified by an external identifier | [optional]

[**back to Peer Review**](#peer-review)

## ReviewCompletionDate

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**year** | [**Year**](#year) | Container for year value | [required]
**month** | [**Month**](#month) | Container for month value | [optional]
**day** | [**Day**](#day) | Container for day value | [optional]

[**back to Peer Review**](#peer-review)

## Year, Month and Day

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Date values; Year in YYYY, Month in MM, Day in DD | [optional]

[**back to ReviewCompletionDate**](#reviewcompletionDate)

## SubjectContainerName

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The title/conference name of the publication, event or group under which the work appeared | [optional]

[**back to Peer Review**](#peer-review)

## SubjectName

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | [**Title**](#title-and-subtitle) | Container for the main name or title review's subject | [required]
**subtitle** | [**Subtitle**](#title-and-subtitle) | Container for any subtitle to the subject | [optional]
**translated-title** | [**TranslatedTitle**](#translatedtitle) | Container for any translations of the subject's title | [optional]

[**back to Peer Review**](#peer-review)

## Title and Subtitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main name/title or subtitle of the subject | [optional]

[**back to SubjectName**](#subjectname)

## TranslatedTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main title of the subject translated into another language | [optional]
**language-code** | **str** | Two-Four letter language code to identify the language of the translation| [required]

[**back to SubjectName**](#subjectname)

## ConveningOrganization

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The human-readable name of the organisation convening the review | [optional]
**address** | [**Address**](#address) | Container for organization location information | [optional]
**disambiguated-organization** | [**DisambiguatedOrganization**](#disambiguatedorganization) | A reference to a disambiguated version the convening organisation | [optional]

[**back to Peer Review**](#peer-review)

## Address

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**city** | **str** | The city center of the organization | [required]
**region** | **str** | Region within the country | [optional]
**country** | **str** | The country code of the national center of the convening organization | ISO 3166-1 alpha-2 [required]

[**back to ConveningOrganization**](#conveningorganization)

## DisambiguatedOrganization

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**disambiguated-organization-identifier** | **str** | The disambiguated organization identifier | [required]
**disambiguation-source** | **str** | The source providing the disambiguated organization ID | "ISNI", "RINGGOLD", "FUNDREF" or "GRID" [required]

[**back to ConveningOrganization**](#conveningorganization)

See the [ORCID V2.1 message schema for peer review](https://github.com/ORCID/ORCID-Source/blob/master/orcid-model/src/main/resources/record_2.1/peer-review-2.1.xsd) for further explanation of what peer-review attributes and values ORCID accepts, and what they're intended to convey
