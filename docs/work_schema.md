# Batch works schema in the NZ ORCID Hub for ORCID Message Schema v2.0/v2.1

Batch works files to be passed through the Hub must be presented in either of the json or YAML formats, with the files following the convention for complex Hub objects, i.e.:
* a list of items 
  * with each item comprised of:
    * a list of invitees (i.e., the individuals whose ORCID records are to be affected); and,
    * the ORCID Message data that is to be asserted to each invitee's ORCID record

The Hub will consume any json or YAML file complying to the following schema.  NB additional validation will be performed when the data is sent to ORCID, and any errors in the message will be reported in the item's status field in the Hub's UI or task report. 

# Works

## Properties
Type | Description | Notes
------------- | ------------- | -------------
[**list[work]**](#work) | Container for the works to be written | [required] 


# Work

Minimum one - maximum unbounded

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invitees** | [**list[invitee]**](#Invitee) | Container for individuals to be affected | [required] 
**created-date** | [**CreatedDate**](#CreatedDate-and-LastModifiedDate) | Container for work item's creation date | [optional, ignored] 
**last-modified-date** | [**LastModifiedDate**](#CreatedDate-and-LastModifiedDate) | Container for work item's last modification date | [optional, ignored] 
**source** | [**Source**](#Source) | Container for when/how the item was asserted | [optional, ignored] 
**title** | [**WorkTitle**](#WorkTitle) | Container for the title(s) of the work | [required] 
**journal-title** | [**Title**](#Title) | Container for the title of the publication or group under which the work was published/presented | [optional] 
**short-description** | **str** | An element for a few sentences describing the work, e.g., an abstract. | [optional] 
**citation** | [**Citation**](#Citation) | Container for a work citation | [optional] 
**type** | **str** | see [here](https://members.orcid.org/api/resources/work-types) for the 38 allowed work types | [required] 
**publication-date** | [**PublicationDate**](#PublicationDate) | Container for the date(s) the work was available to the public | [optional] 
**external-ids** | [**ExternalIDs**](#ExternalIDs) | Container for a work citation | [optional] 
**url** | [**Url**](#Url) | A container for the url value | [optional] 
**contributors** | [**WorkContributors**](#WorkContributors) | Container for the contributors of the work | [optional] 
**language-code** | **str** | Two-Four letter language code to identify the language used in work fields | [optional] 
**country** | [**Country**](#Country) | Container to identify the work's original country of publication/presentation | [optional] 
**visibility** | **str** | NB: Chosen by each invitee/user | [optional, ignored] 


# Invitee

Minimum one - maximum unbounded

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**identifier** | **str** | Internal idenifier from your system for the work-person relationship | [optional]
**first-name** | **str** | First name to assist ORCID iD registration | [required]
**last-name** | **str** | Last name to assist ORCID iD registration | [required]
**email** | **str** | The email address any permissions request will be sent to | [required unless Hub-known ORCID-iD present]
**ORCID-iD** | **str** | ORCID path (16-character identifier) of the ORCID iD | [optional unless no email]
**put-code** | **int** | If present the Hub will attempt to update an existing item | [optional]

# CreatedDate and LastModifiedDate

NB: Captured automatically by the ORCID Registry

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **datetime** | Milliseconds of the event that have elapsed since midnight 1970-01-01; Created automatically by the ORCID Registry | [optional] 

# Source

NB: Captured automatically by the ORCID Registry

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source-orcid** | [**SourceOrcid**](#SourceOrcid-and-SourceClientId) | For legacy client applications, the ORCID iD that created the item | [optional] 
**source-client-id** | [**SourceClientId**](#SourceOrcid-and-SourceClientId) | The client id of the application that created the item | [optional] 
**source-name** | [**SourceName**](#SourceName) | Container for the human-readable name of the client application | [optional] 

# SourceOrcid and SourceClientId

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | Source iD in URI form, i.e., URL + path | [optional] 
**path** | **str** | Application's 16-character client id or legacy ORCID iD | [optional] 
**host** | **str** | URL for the environment of the Source iD, i.e., https://sandbox.orcid.org or https://orcid.org | [optional] 

# SourceName

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The human-readable name of the client application | [optional] 

# WorkTitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | [**Title**](#Title-and-Subtitle) | Container for the main name or title of the work | [required] 
**subtitle** | [**Subtitle**](#Title-and-Subtitle) | Container for any subtitle to the work | [optional] 
**translated-title** | [**TranslatedTitle**](#TranslatedTitle) | Container for any translations of the work's title | [optional] 

# Title and Subtitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main name/title or subtitle of the work | [optional] 

# TranslatedTitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main title of the work or funding translated into another language | [optional] 
**language-code** | **str** | Two-Four letter language code to identify the language of the translation| [optional] 

# Citation

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**citation-type** | **str** | The type (format) of the citation. | "BIBTEX", "FORMATTED-APA", "FORMATTED-CHICAGO", "FORMATTED-HARVARD", "FORMATTED-IEEE", "FORMATTED-MLA", "FORMATTED-UNSPECIFIED", "FORMATTED-VANCOUVER" OR "RIS" [required, "BIBTEX" preferred]
**citation-value** | **str** | The citation formatted in the given citation type | [required]

# PublicationDate

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**year** | [**Year**](#Year) | Container for year value | [required]
**month** | [**Month**](#Month) | Container for month value | [optional] 
**day** | [**Day**](#Day) | Container for day value | [optional] 
**media-type** | **str** | to indicate which version of the publication the date refers to | [optional] 

# Year, Month and Day

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Date values; Year in YYYY, Month in MM, Day in DD | [optional] 

# ExternalIDs

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id** | [**list[ExternalID]**](#ExternalID) | Container for external identifiers to the work | [optional] 

# ExternalID

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id-type** | **str** | The type of the given external identifier | see [here](https://pub.orcid.org/v2.0/identifiers) for supported identifier types [required]
**external-id-value** | **str** | A reference to an external identifier to the work | [required]
**external-id-url** | [**Url**](#Url) | A container for the url value | [optional] 
**external-id-relationship** | **str** | The relationship of this identifier to the work | "SELF" or "PART-OF" [optional] 

# Url

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | An external url for the work or as specified by an external identifier | [optional] 

# WorkContributors

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor** | [**list[Contributor]**](#Contributor) | A container for the work's contributors | [optional] 

# Contributor

Minimum none - maximum unbounded

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-orcid** | [**ContributorOrcid**](#ContributorOrcid) | A container for the contributor's ORCID iD | [optional] 
**credit-name** | [**CreditName**](#CreditName) | A container for the contributor's name | [optional] 
**contributor-email** | [**ContributorEmail**](#ContributorEmail) | A container for the contributor's email | [optional] 
**contributor-attributes** | [**ContributorAttributes**](#ContributorAttributes) | A container for the contributor's role and order | [optional] 

# ContributorOrcid

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** | ORCID iD in URI form, i.e., URL + path | [preferred, at least one of uri or path must be given] 
**path** | **str** | 16-character ORCID iD | [optional] 
**host** | **str** | URL for the environment of the ORCID iD, i.e., https://sandbox.orcid.org or https://orcid.org | [optional] 

# Credit-Name

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The name to use for the researcher or contributor when credited or cited | [optional] 

# Contributor-Email

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Email of the collaborator or other contributor | [Always private, used to look and add ORCID iDs; optional] 


# ContributorAttributes

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-sequence** | **str** | Indication of where in the contributor list this contributor appears | "FIRST" or "ADDITIONAL" [optional]
**contributor-role** | **str** | The role performed by this contributor | "ASSIGNEE", "AUTHOR", "CHAIR-OR-TRANSLATOR", "CO-INVENTOR", "CO-INVESTIGATOR", "EDITOR", "GRADUATE-STUDENT", "OTHER-INVENTOR", "POSTDOCTORAL-RESEARCHER", "PRINCIPAL-INVESTIGATOR", or "SUPPORT-STAFF" [optional]

# Country

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | ISO 3166-1 alpha-2 code for the work's original country of publication/presentation | [optional] 
