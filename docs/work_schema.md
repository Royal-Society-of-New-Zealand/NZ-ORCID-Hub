# Batch works schema in the NZ ORCID Hub for ORCID Message Schema v2.0/v2.1

Batch works files passed through the HUB are presented in either json or YAML formats.  The files must follow the convention for complex Hub objects, i.e. being:
* a list of items 
  * each item comprised of:
    * a list of invitees (the individuals whose ORCID records are to be affected); and,
    * the ORCID Message data that is to be asserted to each invitee's ORCID record

The Hub will consume any json or YAML file complying the following schema.  NB additional validation will be performed when the data is sent to ORCID, and on error the message will be reported in the item's status field in the UI. 

# Works

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**works** | [**list[work]**](#Work) |  | [required] 


# Work

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**invitees** | [**list[invitee]**](#Invitee) |  | [required] 
**created-date** | [**CreatedDate**](#CreatedDate-and-LastModifiedDate) |  | [optional, ignored] 
**last-modified-date** | [**LastModifiedDate**](#CreatedDate-and-LastModifiedDate) |  | [optional, ignored] 
**source** | [**Source**](#Source) |  | [optional, ignored] 
**title** | [**WorkTitle**](#WorkTitle) |  | [required] 
**journal-title** | [**Title**](#Title) |  | [optional] 
**short-description** | **str** |  | [optional] 
**citation** | [**Citation**](#Citation) |  | [optional] 
**type** | **str** |  | [required] 
**publication-date** | [**PublicationDate**](#PublicationDate) |  | [optional] 
**external-ids** | [**ExternalIDs**](#ExternalIDs) |  | [optional] 
**url** | [**Url**](#Url) |  | [optional] 
**contributors** | [**WorkContributors**](#WorkContributors) |  | [optional] 
**language-code** | **str** |  | [optional] 
**country** | [**Country**](#Country) |  | [optional] 
**visibility** | **str** |  | [optional, ignored] 


# Invitee

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**identifier** | **str** |  | [optional]
**first-name** | **str** |  | [required]
**last-name** | **str** |  | [required]
**email** | **str** |  | [unless ORCID-iD required]
**ORCID-iD** | **str** |  | [unless email required]
**put-code** | **int** |  | [optional]

# CreatedDate and LastModifiedDate

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **datetime** |  | [optional] 

# Source

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**source-orcid** | [**SourceOrcid**](#SourceOrcid-and-SourceClientId) |  | [optional] 
**source-client-id** | [**SourceClientId**](#SourceOrcid-and-SourceClientId) |  | [optional] 
**source-name** | [**SourceName**](#SourceName) |  | [optional] 

# SourceOrcid and SourceClientId

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** |  | [optional] 
**path** | **str** |  | [optional] 
**host** | **str** |  | [optional] 

# SourceName

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 

# WorkTitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**title** | [**Title**](Title.md) |  | [optional] 
**subtitle** | [**Subtitle**](Subtitle.md) |  | [optional] 
**translated-title** | [**TranslatedTitle**](TranslatedTitle.md) |  | [optional] 

# Title and Subtitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 

# TranslatedTitle

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 
**language-code** | **str** |  | [optional] 

# Citation

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**citation-type** | **str** |  | 
**citation-value** | **str** |  | 

# PublicationDate

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**year** | [**Year**](Year.md) |  | 
**month** | [**Month**](Month.md) |  | [optional] 
**day** | [**Day**](Day.md) |  | [optional] 
**media-type** | **str** |  | [optional] 

# Year, Month and Day

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 

# ExternalIDs

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id** | [**list[ExternalID]**](ExternalID.md) |  | [optional] 

# ExternalID

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**external-id-type** | **str** |  | 
**external-id-value** | **str** |  | 
**external-id-url** | [**Url**](Url.md) |  | [optional] 
**external-id-relationship** | **str** |  | [optional] 

# Url

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 

# WorkContributors

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor** | [**list[Contributor]**](Contributor.md) |  | [optional] 

# Contributor

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-orcid** | [**ContributorOrcid**](ContributorOrcid.md) |  | [optional] 
**credit-name** | [**CreditName**](CreditName.md) |  | [optional] 
**contributor-email** | [**ContributorEmail**](ContributorEmail.md) |  | [optional] 
**contributor-attributes** | [**ContributorAttributes**](ContributorAttributes.md) |  | [optional] 

# ContributorOrcid

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**uri** | **str** |  | [optional] 
**path** | **str** |  | [optional] 
**host** | **str** |  | [optional] 

# Credit-Name and Contributor-Email

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 

# ContributorAttributes

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**contributor-sequence** | **str** |  | 
**contributor-role** | **str** |  | 

# Country

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** |  | [optional] 
