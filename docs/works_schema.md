# Batch works schema in the NZ ORCID Hub for ORCID Message Schema v2.0/v2.1

Batch works files to be passed through the Hub must be presented in either of the json or YAML formats, with the files following the convention for complex Hub objects, i.e.:
* a list of items
  * with each item comprised of:
    * a list of invitees (i.e., the individuals whose ORCID records are to be affected); and,
    * the ORCID Message data that is to be asserted to each invitee's ORCID record

Examples can be found here: [**works.json**](_downloads/example_works.json) and [**works.yaml**](_downloads/example_works.yaml)

The Hub will consume any json or YAML file complying to the following schema.  NB additional validation will be performed when the data is sent to ORCID, and any errors in the message will be reported in the item's status field in the Hub's UI or task report.

## Works

### Properties
Type | Description | Notes
------------- | ------------- | -------------
[**list[work]**](#work) | Container for the works to be written | [required]


## Work

Minimum one - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invitees** | [**list[invitee]**](#invitee) | Container for individuals to be affected | [required]
**created-date** | [**CreatedDate**](#createddate-and-lastmodifieddate) | Container for work item's creation date | [optional, ignored]
**last-modified-date** | [**LastModifiedDate**](#createddate-and-lastmodifieddate) | Container for work item's last modification date | [optional, ignored]
**source** | [**Source**](#source) | Container for when/how the item was asserted | [optional, ignored]
**title** | [**WorkTitle**](#worktitle) | Container for the title(s) of the work | [required]
**journal-title** | [**JournalTitle**](#journaltitle) | Container for the title of the publication or group under which the work was published/presented | [optional]
**short-description** | **str** | An element for a few sentences describing the work, e.g., an abstract. | [optional]
**citation** | [**Citation**](#citation) | Container for a work citation | [optional]
**type** | **str** | The work's type, see [here](https://members.orcid.org/api/resources/work-types) for the 38 allowed types | [required]
**publication-date** | [**PublicationDate**](#publicationdate) | Container for the date(s) the work was available to the public | [optional]
**external-ids** | [**list[external-id]**](#externalid) | Container for the unique IDs of the work | [optional]
**url** | [**Url**](#url) | A container for the url representation of the work | [optional]
**contributors** | [**WorkContributors**](#workcontributors) | Container for the contributors of the work | [optional]
**language-code** | **str** | Two-Four letter language code to identify the language used in work fields | [optional]
**country** | [**Country**](#country) | Container to identify the work's original country of publication/presentation | [optional]

[**back to Works**](#works)

## Invitee

Minimum one - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**identifier** | **str** | Internal identifier from your system for the work-person relationship | [optional]
**first-name** | **str** | First name to assist ORCID iD registration | [required]
**last-name** | **str** | Last name to assist ORCID iD registration | [required]
**email** | **str** | The email address any permissions request will be sent to | [required unless Hub-known ORCID-iD present]
**ORCID-iD** | **str** | ORCID path (16-character identifier) of the ORCID iD | [optional unless no email]
**put-code** | **int** | If present the Hub will attempt to update an existing item | [optional]
**visibility** | **str** | The privacy level chosen by record holder for this item | "PUBLIC", "LIMITED" or "PRIVATE" [optional, ignored]

[**back to Work**](#work)

## CreatedDate and LastModifiedDate

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **datetime** | Milliseconds of the event that have elapsed since midnight 1970-01-01; Created automatically by the ORCID Registry | [optional]

[**back to Work**](#work)

## Source

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source-orcid** | [**SourceOrcid**](#sourceorcid-and-sourceclientid) | For legacy client applications, the ORCID iD that created the item | [optional]
**source-client-id** | [**SourceClientId**](#sourceorcid-and-sourceclientid) | The client id of the application that created the item | [optional]
**source-name** | [**SourceName**](#sourcename) | Container for the human-readable name of the client application | [optional]

[**back to Work**](#work)

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

## WorkTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | [**Title**](#title-and-subtitle) | Container for the main name or title of the work | [required]
**subtitle** | [**Subtitle**](#title-and-subtitle) | Container for any subtitle to the work | [optional]
**translated-title** | [**TranslatedTitle**](#translatedtitle) | Container for any translations of the work's title | [optional]

[**back to Work**](#work)

## Title and Subtitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main name/title or subtitle of the work | [optional]

[**back to WorkTitle**](#worktitle)

## TranslatedTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main title of the work or funding translated into another language | [optional]
**language-code** | **str** | Two-Four letter language code to identify the language of the translation | [optional]

[**back to WorkTitle**](#worktitle)

## JournalTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The title/conference name of the publication, event or group under which the work appeared | [optional]

[**back to Work**](#work)

## Citation

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**citation-type** | **str** | The type (format) of the citation. | "BIBTEX", "FORMATTED-APA", "FORMATTED-CHICAGO", "FORMATTED-HARVARD", "FORMATTED-IEEE", "FORMATTED-MLA", "FORMATTED-UNSPECIFIED", "FORMATTED-VANCOUVER" OR "RIS" [required, "BIBTEX" preferred]
**citation-value** | **str** | The citation formatted in the given citation type | [required]



## PublicationDate

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**year** | [**Year**](#year) | Container for year value | [required]
**month** | [**Month**](#month) | Container for month value | [optional]
**day** | [**Day**](#day) | Container for day value | [optional]
**media-type** | **str** | to indicate which version of the publication the date refers to | [optional]

[**back to Work**](#work)

## Year, Month and Day

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Date values; Year in YYYY, Month in MM, Day in DD | [optional]

[**back to PublicationDate**](#publicationdate)

## ExternalID

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id-type** | **str** | The type of the given external identifier | see [here](https://pub.orcid.org/v2.0/identifiers) for supported identifier types [required]
**external-id-value** | **str** | A reference to an external identifier to the work | [required]
**external-id-url** | [**Url**](#url) | A container for the url value | [optional]
**external-id-relationship** | **str** | The relationship of this identifier to the work | "SELF" or "PART-OF" [optional]

[**back to Work**](#work)

## Url

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | An external url for the work or as specified by an external identifier | [optional]

[**back to Work**](#work)

## WorkContributors

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor** | [**list[Contributor]**](#contributor) | A container for the work's contributors | [optional]

[**back to Work**](#work)

## Contributor

Minimum none - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-orcid** | [**ContributorOrcid**](#contributororcid) | A container for the contributor's ORCID iD | [optional]
**credit-name** | [**CreditName**](#creditname) | A container for the contributor's name | [optional]
**contributor-email** | [**ContributorEmail**](#contributoremail) | A container for the contributor's email | [deprecated]
**contributor-attributes** | [**ContributorAttributes**](#contributorattributes) | A container for the contributor's role and order | [optional]

[**back to WorkContributors**](#workcontributors)

## ContributorOrcid

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | ORCID iD in URI form, i.e., URL + path | [preferred, at least one of uri or path must be given]
**path** | **str** | 16-character ORCID iD | [optional]
**host** | **str** | URL for the environment of the ORCID iD, i.e., https://sandbox.orcid.org or https://orcid.org | [optional]

[**back to Contributor**](#contributor)

## Credit-Name

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The name to use for the researcher or contributor when credited or cited | [optional]

[**back to Contributor**](#contributor)

## Contributor-Email

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Email of the collaborator or other contributor | [Always private; deprecated do not use]

[**back to Contributor**](#contributor)

## ContributorAttributes

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-sequence** | **str** | Indication of where in the contributor list this contributor appears | "FIRST" or "ADDITIONAL" [optional]
**contributor-role** | **str** | The role performed by this contributor | "ASSIGNEE", "AUTHOR", "CHAIR-OR-TRANSLATOR", "CO-INVENTOR", "CO-INVESTIGATOR", "EDITOR", "GRADUATE-STUDENT", "OTHER-INVENTOR", "POSTDOCTORAL-RESEARCHER", "PRINCIPAL-INVESTIGATOR", or "SUPPORT-STAFF" [optional]

[**back to Contributor**](#contributor)

## Country

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | ISO 3166-1 alpha-2 code for the work's original country of publication/presentation | [optional]

[**back to Work**](#work)

See the [ORCID V2.1 message schema for works](https://github.com/ORCID/ORCID-Source/blob/master/orcid-model/src/main/resources/record_2.1/work-2.1.xsd) for further explanation of what works attributes and values ORCID accepts, and what they're intended to convey
