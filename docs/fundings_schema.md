# Batch funding schema in the NZ ORCID Hub for ORCID Message Schema v2.0/v2.1

Batch funding files to be passed through the Hub must be presented in either of the json or YAML formats, with the files following the convention for complex Hub objects, i.e.:
* a list of items
  * with each item comprised of:
    * a list of invitees (i.e., the individuals whose ORCID records are to be affected); and,
    * the ORCID Message data that is to be asserted to each invitee's ORCID record

Examples can be found here: [**fundings.json**](_downloads/example_fundings.json) and [**fundings.yaml**](_downloads/example_fundings.yaml)

The Hub will consume any json or YAML file complying to the following schema.  NB additional validation will be performed when the data is sent to ORCID, and any errors in the message will be reported in the item's status field in the Hub's UI or task report.

## Fundings

### Properties
Type | Description | Notes
------------- | ------------- | -------------
[**list[funding]**](#funding) | Container for the funding item(s) to be written | [required]


## Funding

Minimum one - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invitees** | [**list[invitee]**](#invitee) | Container for individuals to be affected | [required]
**created-date** | [**CreatedDate**](#createddate-and-lastmodifieddate) | Container for work item's creation date | [optional, ignored]
**last-modified-date** | [**LastModifiedDate**](#createddate-and-lastmodifieddate) | Container for work item's last modification date | [optional, ignored]
**source** | [**Source**](#source) | Container for when/how the item was asserted | [optional, ignored]
**organization** | [**Organization**](#organization) | Container for elements describing the organization which awarded the funding | [required]
**title** | [**FundingTitle**](#fundingtitle) | Container for the title(s) of the award/project | [required]
**short-description** | **str** | An element for a few sentences describing the award/project, e.g., an abstract. | [optional]
**amount** | [**Amount**](#amount) | Container for the value and currentcy of the award/project | [optional]
**type** | **str** | The type of funding | "AWARD", "CONTRACT", "GRANT" or "SALARY-AWARD" [required]
**organization_defined_type** | [**FundingSubType**](#fundingsubtype) | Container for the organisation's category of funding | [optional]
**start-date** | [**StartDate**](#startdate-and-enddate) | The date the funding began, given to any level of specificity | [optional]
**end-date** | [**EndDate**](#startdate-and-enddate) | The date the funding ended or will end, given to any level of specificity | [optional]
**external-ids** | [**list[external-id]**](#externalid) | A non-repeatable container for identifiers of the funding | [optional]
**url** | [**Url**](#url) | A link to the funding or funding output (appears in the user interface under "Alternate URL") | [optional]
**contributors** | [**FundingContributors**](#fundingcontributors) | Container for information about the recipients of the funding | [optional]

[**back to Fundings**](#fundings)

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

[**back to Funding**](#funding)

## CreatedDate and LastModifiedDate

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **datetime** | Milliseconds of the event that have elapsed since midnight 1970-01-01 | [optional]

[**back to Funding**](#funding)

## Source

NB: Captured automatically by the ORCID Registry

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source-orcid** | [**SourceOrcid**](#sourceorcid-and-sourceclientid) | For legacy client applications, the ORCID iD that created the item | [optional]
**source-client-id** | [**SourceClientId**](#sourceorcid-and-sourceclientid) | The client id of the application that created the item | [optional]
**source-name** | [**SourceName**](#sourcename) | Container for the human-readable name of the client application | [optional]

[**back to Funding**](#funding)

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

## Organization

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** | The human-readable name of the funding organisation | [optional]
**address** | [**Address**](#address) | Container for organization location information | [optional]
**disambiguated-organization** | [**DisambiguatedOrganization**](#disambiguatedorganization) | A reference to a disambiguated version the funding organisation | [optional]

[**back to Funding**](#funding)

## Address

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**city** | **str** | The city center of the funding organization | [required]
**region** | **str** | Region within the country | [optional]
**country** | **str** | The country code of the national center of the funding organization | ISO 3166-1 alpha-2 [required]

[**back to Organization**](#organization)

## DisambiguatedOrganization

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**disambiguated-organization-identifier** | **str** | The disambiguated organization identifier | [required]
**disambiguation-source** | **str** | The source providing the disambiguated organization ID | "ISNI", "RINGGOLD", "FUNDREF" or "GRID" [required]

[**back to Organization**](#organization)

## FundingTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | [**Title**](#title-and-subtitle) | Container for the main name or title of the award/project | [required]
**translated-title** | [**TranslatedTitle**](#translatedtitle) | Container for any translations of the award's/project's title | [optional]

[**back to Funding**](#funding)

## Title and Subtitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main name/title or subtitle of the work | [optional]

[**back to FundingTitle**](#fundingtitle)

## TranslatedTitle

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The main title of the work or funding translated into another language | [optional]
**language-code** | **str** | Two-Four letter language code to identify the language of the translation| [required]

[**back to FundingTitle**](#fundingtitle)

## Amount

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | A numerical value for the amount of funding for the award/project | [optional]
**currency-code** | **str** | [Three letter currency code](https://www.iso.org/iso-4217-currency-codes.html) to identify the currency the amount is denominated in| [required]

### FundingSubType

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The organization's type for an external identifier | [optional]

[**back to Funding**](#funding)

## StartDate and EndDate

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**year** | [**Year**](#year) | Container for year value | [required]
**month** | [**Month**](#month) | Container for month value | [optional]
**day** | [**Day**](#day) | Container for day value | [optional]

[**back to Funding**](#funding)

## Year, Month and Day

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | Date values; Year in YYYY, Month in MM, Day in DD | [optional]

[**back to StartDate and EndDate**](#startdate-and-enddate)

## ExternalIDs

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id** | [**list[ExternalID]**](#externalid) | Container for external identifiers to the award/project | [optional]

[**back to Funding**](#funding)

## ExternalID

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id-type** | **str** | The type of the given external identifier | see [here](https://pub.orcid.org/v2.0/identifiers) for supported identifier types [required]
**external-id-value** | **str** | A reference to an external identifier to the award/project | [required]
**external-id-url** | [**Url**](#url) | A container for the url value | [optional]
**external-id-relationship** | **str** | The relationship of this identifier to the award/project | "SELF" or "PART-OF" [optional]

[**back to Funding**](#funding)

## Url

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | An external url for the award/project or as specified by an external identifier | [optional]

[**back to Funding**](#funding)

## FundingContributors

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor** | [**list[Contributor]**](#contributor) | A container for the award's/project's contributors | [optional]

[**back to Funding**](#funding)

## Contributor

Minimum none - maximum unbounded

### Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-orcid** | [**ContributorOrcid**](#contributororcid) | A container for the contributor's ORCID iD | [optional]
**credit-name** | [**CreditName**](#creditname) | A container for the contributor's name | [optional]
**contributor-email** | [**ContributorEmail**](#contributoremail) | A container for the contributor's email | [deprecated]
**contributor-attributes** | [**ContributorAttributes**](#contributorattributes) | A container for the contributor's role and order | [optional]

[**back to FundingContributors**](#fundingcontributors)

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
**contributor-role** | **str** | The role performed by this contributor | "LEAD", "CO-LEAD", "SUPPORTED-BY" or "OTHER-CONTRIBUTION" [optional]

[**back to Contributor**](#contributor)

See the [ORCID V2.1 message schema for funding](https://github.com/ORCID/ORCID-Source/blob/master/orcid-model/src/main/resources/record_2.1/funding-2.1.xsd) for further explanation of what funding attributes and values ORCID accepts, and what they're intended to convey
