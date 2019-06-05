# orcid_api_v3.MemberAPIV20Api

All URIs are relative to *//api.orcid.org/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_permission_notification**](MemberAPIV20Api.md#add_permission_notification) | **POST** /v2.0/{orcid}/notification-permission | Add a notification
[**create_address**](MemberAPIV20Api.md#create_address) | **POST** /v2.0/{orcid}/address | Add an address
[**create_education**](MemberAPIV20Api.md#create_education) | **POST** /v2.0/{orcid}/education | Create an Education
[**create_employment**](MemberAPIV20Api.md#create_employment) | **POST** /v2.0/{orcid}/employment | Create an Employment
[**create_external_identifier**](MemberAPIV20Api.md#create_external_identifier) | **POST** /v2.0/{orcid}/external-identifiers | Add external identifier
[**create_funding**](MemberAPIV20Api.md#create_funding) | **POST** /v2.0/{orcid}/funding | Create a Funding
[**create_group_id_record**](MemberAPIV20Api.md#create_group_id_record) | **POST** /v2.0/group-id-record | Create a Group
[**create_keyword**](MemberAPIV20Api.md#create_keyword) | **POST** /v2.0/{orcid}/keywords | Add keyword
[**create_other_name**](MemberAPIV20Api.md#create_other_name) | **POST** /v2.0/{orcid}/other-names | Add other name
[**create_peer_review**](MemberAPIV20Api.md#create_peer_review) | **POST** /v2.0/{orcid}/peer-review | Create a Peer Review
[**create_researcher_url**](MemberAPIV20Api.md#create_researcher_url) | **POST** /v2.0/{orcid}/researcher-urls | Add a new researcher url for an ORCID ID
[**create_work**](MemberAPIV20Api.md#create_work) | **POST** /v2.0/{orcid}/work | Create a Work
[**create_works**](MemberAPIV20Api.md#create_works) | **POST** /v2.0/{orcid}/works | Create a list of Work
[**delete_address**](MemberAPIV20Api.md#delete_address) | **DELETE** /v2.0/{orcid}/address/{putCode} | Delete an address
[**delete_education**](MemberAPIV20Api.md#delete_education) | **DELETE** /v2.0/{orcid}/education/{putCode} | Delete an Education
[**delete_employment**](MemberAPIV20Api.md#delete_employment) | **DELETE** /v2.0/{orcid}/employment/{putCode} | Delete an Employment
[**delete_external_identifier**](MemberAPIV20Api.md#delete_external_identifier) | **DELETE** /v2.0/{orcid}/external-identifiers/{putCode} | Delete external identifier
[**delete_funding**](MemberAPIV20Api.md#delete_funding) | **DELETE** /v2.0/{orcid}/funding/{putCode} | Delete a Funding
[**delete_group_id_record**](MemberAPIV20Api.md#delete_group_id_record) | **DELETE** /v2.0/group-id-record/{putCode} | Delete a Group
[**delete_keyword**](MemberAPIV20Api.md#delete_keyword) | **DELETE** /v2.0/{orcid}/keywords/{putCode} | Delete keyword
[**delete_other_name**](MemberAPIV20Api.md#delete_other_name) | **DELETE** /v2.0/{orcid}/other-names/{putCode} | Delete other name
[**delete_peer_review**](MemberAPIV20Api.md#delete_peer_review) | **DELETE** /v2.0/{orcid}/peer-review/{putCode} | Delete a Peer Review
[**delete_researcher_url**](MemberAPIV20Api.md#delete_researcher_url) | **DELETE** /v2.0/{orcid}/researcher-urls/{putCode} | Delete one researcher url from an ORCID ID
[**delete_work**](MemberAPIV20Api.md#delete_work) | **DELETE** /v2.0/{orcid}/work/{putCode} | Delete a Work
[**edit_address**](MemberAPIV20Api.md#edit_address) | **PUT** /v2.0/{orcid}/address/{putCode} | Edit an address
[**edit_external_identifier**](MemberAPIV20Api.md#edit_external_identifier) | **PUT** /v2.0/{orcid}/external-identifiers/{putCode} | Edit external identifier
[**edit_keyword**](MemberAPIV20Api.md#edit_keyword) | **PUT** /v2.0/{orcid}/keywords/{putCode} | Edit keyword
[**edit_other_name**](MemberAPIV20Api.md#edit_other_name) | **PUT** /v2.0/{orcid}/other-names/{putCode} | Edit other name
[**edit_researcher_url**](MemberAPIV20Api.md#edit_researcher_url) | **PUT** /v2.0/{orcid}/researcher-urls/{putCode} | Edits researcher url for an ORCID ID
[**flag_as_archived_permission_notification**](MemberAPIV20Api.md#flag_as_archived_permission_notification) | **DELETE** /v2.0/{orcid}/notification-permission/{id} | Archive a notification
[**search_by_query**](MemberAPIV20Api.md#search_by_query) | **GET** /v2.0/search | Search records
[**update_education**](MemberAPIV20Api.md#update_education) | **PUT** /v2.0/{orcid}/education/{putCode} | Update an Education
[**update_employment**](MemberAPIV20Api.md#update_employment) | **PUT** /v2.0/{orcid}/employment/{putCode} | Update an Employment
[**update_funding**](MemberAPIV20Api.md#update_funding) | **PUT** /v2.0/{orcid}/funding/{putCode} | Update a Funding
[**update_group_id_record**](MemberAPIV20Api.md#update_group_id_record) | **PUT** /v2.0/group-id-record/{putCode} | Update a Group
[**update_peer_review**](MemberAPIV20Api.md#update_peer_review) | **PUT** /v2.0/{orcid}/peer-review/{putCode} | Update a Peer Review
[**update_work**](MemberAPIV20Api.md#update_work) | **PUT** /v2.0/{orcid}/work/{putCode} | Update a Work
[**view_activities**](MemberAPIV20Api.md#view_activities) | **GET** /v2.0/{orcid}/activities | Fetch all activities
[**view_address**](MemberAPIV20Api.md#view_address) | **GET** /v2.0/{orcid}/address/{putCode} | Fetch an address
[**view_addresses**](MemberAPIV20Api.md#view_addresses) | **GET** /v2.0/{orcid}/address | Fetch all addresses of a profile
[**view_biography**](MemberAPIV20Api.md#view_biography) | **GET** /v2.0/{orcid}/biography | Get biography details
[**view_client**](MemberAPIV20Api.md#view_client) | **GET** /v2.0/client/{client_id} | Fetch client details
[**view_education**](MemberAPIV20Api.md#view_education) | **GET** /v2.0/{orcid}/education/{putCode} | Fetch an Education
[**view_education_summary**](MemberAPIV20Api.md#view_education_summary) | **GET** /v2.0/{orcid}/education/summary/{putCode} | Fetch an Education summary
[**view_educations**](MemberAPIV20Api.md#view_educations) | **GET** /v2.0/{orcid}/educations | Fetch all educations
[**view_emails**](MemberAPIV20Api.md#view_emails) | **GET** /v2.0/{orcid}/email | Fetch all emails for an ORCID ID
[**view_employment**](MemberAPIV20Api.md#view_employment) | **GET** /v2.0/{orcid}/employment/{putCode} | Fetch an Employment
[**view_employment_summary**](MemberAPIV20Api.md#view_employment_summary) | **GET** /v2.0/{orcid}/employment/summary/{putCode} | Fetch an Employment Summary
[**view_employments**](MemberAPIV20Api.md#view_employments) | **GET** /v2.0/{orcid}/employments | Fetch all employments
[**view_external_identifier**](MemberAPIV20Api.md#view_external_identifier) | **GET** /v2.0/{orcid}/external-identifiers/{putCode} | Fetch external identifier
[**view_external_identifiers**](MemberAPIV20Api.md#view_external_identifiers) | **GET** /v2.0/{orcid}/external-identifiers | Fetch external identifiers
[**view_funding**](MemberAPIV20Api.md#view_funding) | **GET** /v2.0/{orcid}/funding/{putCode} | Fetch a Funding
[**view_funding_summary**](MemberAPIV20Api.md#view_funding_summary) | **GET** /v2.0/{orcid}/funding/summary/{putCode} | Fetch a Funding Summary
[**view_fundings**](MemberAPIV20Api.md#view_fundings) | **GET** /v2.0/{orcid}/fundings | Fetch all fundings
[**view_group_id_record**](MemberAPIV20Api.md#view_group_id_record) | **GET** /v2.0/group-id-record/{putCode} | Fetch a Group
[**view_group_id_records**](MemberAPIV20Api.md#view_group_id_records) | **GET** /v2.0/group-id-record | Fetch Groups
[**view_keyword**](MemberAPIV20Api.md#view_keyword) | **GET** /v2.0/{orcid}/keywords/{putCode} | Fetch keyword
[**view_keywords**](MemberAPIV20Api.md#view_keywords) | **GET** /v2.0/{orcid}/keywords | Fetch keywords
[**view_other_name**](MemberAPIV20Api.md#view_other_name) | **GET** /v2.0/{orcid}/other-names/{putCode} | Fetch Other name
[**view_other_names**](MemberAPIV20Api.md#view_other_names) | **GET** /v2.0/{orcid}/other-names | Fetch Other names
[**view_peer_review**](MemberAPIV20Api.md#view_peer_review) | **GET** /v2.0/{orcid}/peer-review/{putCode} | Fetch a Peer Review
[**view_peer_review_summary**](MemberAPIV20Api.md#view_peer_review_summary) | **GET** /v2.0/{orcid}/peer-review/summary/{putCode} | Fetch a Peer Review Summary
[**view_peer_reviews**](MemberAPIV20Api.md#view_peer_reviews) | **GET** /v2.0/{orcid}/peer-reviews | Fetch all peer reviews
[**view_permission_notification**](MemberAPIV20Api.md#view_permission_notification) | **GET** /v2.0/{orcid}/notification-permission/{id} | Fetch a notification by id
[**view_person**](MemberAPIV20Api.md#view_person) | **GET** /v2.0/{orcid}/person | Fetch person details
[**view_personal_details**](MemberAPIV20Api.md#view_personal_details) | **GET** /v2.0/{orcid}/personal-details | Fetch personal details for an ORCID ID
[**view_record**](MemberAPIV20Api.md#view_record) | **GET** /v2.0/{orcid} | Fetch record details
[**view_researcher_url**](MemberAPIV20Api.md#view_researcher_url) | **GET** /v2.0/{orcid}/researcher-urls/{putCode} | Fetch one researcher url for an ORCID ID
[**view_researcher_urls**](MemberAPIV20Api.md#view_researcher_urls) | **GET** /v2.0/{orcid}/researcher-urls | Fetch all researcher urls for an ORCID ID
[**view_specified_works**](MemberAPIV20Api.md#view_specified_works) | **GET** /v2.0/{orcid}/works/{putCodes} | Fetch specified works
[**view_work**](MemberAPIV20Api.md#view_work) | **GET** /v2.0/{orcid}/work/{putCode} | Fetch a Work
[**view_work_summary**](MemberAPIV20Api.md#view_work_summary) | **GET** /v2.0/{orcid}/work/summary/{putCode} | Fetch a Work Summary
[**view_works**](MemberAPIV20Api.md#view_works) | **GET** /v2.0/{orcid}/works | Fetch all works

# **add_permission_notification**
> str add_permission_notification(orcid, body=body)

Add a notification

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.NotificationPermissionV20() # NotificationPermissionV20 |  (optional)

try:
    # Add a notification
    api_response = api_instance.add_permission_notification(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->add_permission_notification: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**NotificationPermissionV20**](NotificationPermissionV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_address**
> create_address(orcid, body=body)

Add an address

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.AddressV20() # AddressV20 |  (optional)

try:
    # Add an address
    api_instance.create_address(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_address: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**AddressV20**](AddressV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_education**
> str create_education(orcid, body=body)

Create an Education

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.EducationV20() # EducationV20 |  (optional)

try:
    # Create an Education
    api_response = api_instance.create_education(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_education: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**EducationV20**](EducationV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_employment**
> str create_employment(orcid, body=body)

Create an Employment

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.EmploymentV20() # EmploymentV20 |  (optional)

try:
    # Create an Employment
    api_response = api_instance.create_employment(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_employment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**EmploymentV20**](EmploymentV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_external_identifier**
> create_external_identifier(orcid, body=body)

Add external identifier

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.PersonExternalIdentifierV20() # PersonExternalIdentifierV20 |  (optional)

try:
    # Add external identifier
    api_instance.create_external_identifier(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_external_identifier: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**PersonExternalIdentifierV20**](PersonExternalIdentifierV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_funding**
> str create_funding(orcid, body=body)

Create a Funding

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.FundingV20() # FundingV20 |  (optional)

try:
    # Create a Funding
    api_response = api_instance.create_funding(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_funding: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**FundingV20**](FundingV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_group_id_record**
> create_group_id_record(body=body)

Create a Group

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
body = orcid_api_v3.GroupIdRecord() # GroupIdRecord |  (optional)

try:
    # Create a Group
    api_instance.create_group_id_record(body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**GroupIdRecord**](GroupIdRecord.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_keyword**
> create_keyword(orcid, body=body)

Add keyword

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.KeywordV20() # KeywordV20 |  (optional)

try:
    # Add keyword
    api_instance.create_keyword(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_keyword: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**KeywordV20**](KeywordV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_other_name**
> create_other_name(orcid, body=body)

Add other name

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.OtherNameV20() # OtherNameV20 |  (optional)

try:
    # Add other name
    api_instance.create_other_name(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_other_name: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**OtherNameV20**](OtherNameV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_peer_review**
> str create_peer_review(orcid, body=body)

Create a Peer Review

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.PeerReviewV20() # PeerReviewV20 |  (optional)

try:
    # Create a Peer Review
    api_response = api_instance.create_peer_review(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_peer_review: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**PeerReviewV20**](PeerReviewV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_researcher_url**
> create_researcher_url(orcid, body=body)

Add a new researcher url for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.ResearcherUrlV20() # ResearcherUrlV20 |  (optional)

try:
    # Add a new researcher url for an ORCID ID
    api_instance.create_researcher_url(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_researcher_url: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**ResearcherUrlV20**](ResearcherUrlV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_work**
> str create_work(orcid, body=body)

Create a Work

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.WorkV20() # WorkV20 |  (optional)

try:
    # Create a Work
    api_response = api_instance.create_work(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_work: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**WorkV20**](WorkV20.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_works**
> create_works(orcid, body=body)

Create a list of Work

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.WorkBulkV20() # WorkBulkV20 |  (optional)

try:
    # Create a list of Work
    api_instance.create_works(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->create_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**WorkBulkV20**](WorkBulkV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_address**
> delete_address(orcid, put_code)

Delete an address

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an address
    api_instance.delete_address(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_address: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_education**
> delete_education(orcid, put_code)

Delete an Education

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an Education
    api_instance.delete_education(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_education: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_employment**
> delete_employment(orcid, put_code)

Delete an Employment

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an Employment
    api_instance.delete_employment(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_employment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_external_identifier**
> delete_external_identifier(orcid, put_code)

Delete external identifier

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete external identifier
    api_instance.delete_external_identifier(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_external_identifier: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_funding**
> delete_funding(orcid, put_code)

Delete a Funding

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Funding
    api_instance.delete_funding(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_funding: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_group_id_record**
> delete_group_id_record(put_code)

Delete a Group

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 

try:
    # Delete a Group
    api_instance.delete_group_id_record(put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_keyword**
> delete_keyword(orcid, put_code)

Delete keyword

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete keyword
    api_instance.delete_keyword(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_keyword: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_other_name**
> delete_other_name(orcid, put_code)

Delete other name

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete other name
    api_instance.delete_other_name(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_other_name: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_peer_review**
> delete_peer_review(orcid, put_code)

Delete a Peer Review

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Peer Review
    api_instance.delete_peer_review(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_peer_review: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_researcher_url**
> delete_researcher_url(orcid, put_code)

Delete one researcher url from an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete one researcher url from an ORCID ID
    api_instance.delete_researcher_url(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_researcher_url: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_work**
> delete_work(orcid, put_code)

Delete a Work

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Work
    api_instance.delete_work(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->delete_work: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_address**
> edit_address(orcid, put_code, body=body)

Edit an address

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.AddressV20() # AddressV20 |  (optional)

try:
    # Edit an address
    api_instance.edit_address(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->edit_address: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**AddressV20**](AddressV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_external_identifier**
> edit_external_identifier(orcid, put_code, body=body)

Edit external identifier

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.PersonExternalIdentifierV20() # PersonExternalIdentifierV20 |  (optional)

try:
    # Edit external identifier
    api_instance.edit_external_identifier(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->edit_external_identifier: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**PersonExternalIdentifierV20**](PersonExternalIdentifierV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_keyword**
> edit_keyword(orcid, put_code, body=body)

Edit keyword

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.KeywordV20() # KeywordV20 |  (optional)

try:
    # Edit keyword
    api_instance.edit_keyword(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->edit_keyword: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**KeywordV20**](KeywordV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_other_name**
> edit_other_name(orcid, put_code, body=body)

Edit other name

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.OtherNameV20() # OtherNameV20 |  (optional)

try:
    # Edit other name
    api_instance.edit_other_name(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->edit_other_name: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**OtherNameV20**](OtherNameV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_researcher_url**
> edit_researcher_url(orcid, put_code, body=body)

Edits researcher url for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.ResearcherUrlV20() # ResearcherUrlV20 |  (optional)

try:
    # Edits researcher url for an ORCID ID
    api_instance.edit_researcher_url(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->edit_researcher_url: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**ResearcherUrlV20**](ResearcherUrlV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **flag_as_archived_permission_notification**
> Notification flag_as_archived_permission_notification(orcid, id)

Archive a notification

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
id = 789 # int | 

try:
    # Archive a notification
    api_response = api_instance.flag_as_archived_permission_notification(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->flag_as_archived_permission_notification: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **id** | **int**|  | 

### Return type

[**Notification**](Notification.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_by_query**
> SearchV20 search_by_query(q=q)

Search records

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
q = 'q_example' # str |  (optional)

try:
    # Search records
    api_response = api_instance.search_by_query(q=q)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->search_by_query: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**|  | [optional] 

### Return type

[**SearchV20**](SearchV20.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_education**
> update_education(orcid, put_code, body=body)

Update an Education

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.EducationV20() # EducationV20 |  (optional)

try:
    # Update an Education
    api_instance.update_education(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_education: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**EducationV20**](EducationV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_employment**
> update_employment(orcid, put_code, body=body)

Update an Employment

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.EmploymentV20() # EmploymentV20 |  (optional)

try:
    # Update an Employment
    api_instance.update_employment(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_employment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**EmploymentV20**](EmploymentV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_funding**
> update_funding(orcid, put_code, body=body)

Update a Funding

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.FundingV20() # FundingV20 |  (optional)

try:
    # Update a Funding
    api_instance.update_funding(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_funding: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**FundingV20**](FundingV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_group_id_record**
> update_group_id_record(put_code, body=body)

Update a Group

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 
body = orcid_api_v3.GroupIdRecord() # GroupIdRecord |  (optional)

try:
    # Update a Group
    api_instance.update_group_id_record(put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 
 **body** | [**GroupIdRecord**](GroupIdRecord.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_peer_review**
> update_peer_review(orcid, put_code, body=body)

Update a Peer Review

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.PeerReviewV20() # PeerReviewV20 |  (optional)

try:
    # Update a Peer Review
    api_instance.update_peer_review(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_peer_review: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**PeerReviewV20**](PeerReviewV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_work**
> update_work(orcid, put_code, body=body)

Update a Work

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.WorkV20() # WorkV20 |  (optional)

try:
    # Update a Work
    api_instance.update_work(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->update_work: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**WorkV20**](WorkV20.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_activities**
> ActivitiesSummaryV20 view_activities(orcid)

Fetch all activities

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all activities
    api_response = api_instance.view_activities(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_activities: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**ActivitiesSummaryV20**](ActivitiesSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_address**
> AddressV20 view_address(orcid, put_code)

Fetch an address

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an address
    api_response = api_instance.view_address(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_address: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**AddressV20**](AddressV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_addresses**
> AddressesV20 view_addresses(orcid)

Fetch all addresses of a profile

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all addresses of a profile
    api_response = api_instance.view_addresses(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_addresses: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**AddressesV20**](AddressesV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_biography**
> BiographyV20 view_biography(orcid)

Get biography details

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Get biography details
    api_response = api_instance.view_biography(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_biography: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**BiographyV20**](BiographyV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_client**
> ClientSummary view_client(client_id)

Fetch client details

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
client_id = 'client_id_example' # str | 

try:
    # Fetch client details
    api_response = api_instance.view_client(client_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_client: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **client_id** | **str**|  | 

### Return type

[**ClientSummary**](ClientSummary.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_education**
> EducationV20 view_education(orcid, put_code)

Fetch an Education

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Education
    api_response = api_instance.view_education(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_education: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EducationV20**](EducationV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_education_summary**
> EducationSummaryV20 view_education_summary(orcid, put_code)

Fetch an Education summary

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Education summary
    api_response = api_instance.view_education_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_education_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EducationSummaryV20**](EducationSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_educations**
> EducationsSummaryV20 view_educations(orcid)

Fetch all educations

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all educations
    api_response = api_instance.view_educations(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_educations: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**EducationsSummaryV20**](EducationsSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_emails**
> EmailsV20 view_emails(orcid)

Fetch all emails for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all emails for an ORCID ID
    api_response = api_instance.view_emails(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_emails: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**EmailsV20**](EmailsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employment**
> EmploymentV20 view_employment(orcid, put_code)

Fetch an Employment

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Employment
    api_response = api_instance.view_employment(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_employment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EmploymentV20**](EmploymentV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employment_summary**
> EmploymentSummaryV20 view_employment_summary(orcid, put_code)

Fetch an Employment Summary

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Employment Summary
    api_response = api_instance.view_employment_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_employment_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EmploymentSummaryV20**](EmploymentSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employments**
> EmploymentsSummaryV20 view_employments(orcid)

Fetch all employments

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all employments
    api_response = api_instance.view_employments(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_employments: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**EmploymentsSummaryV20**](EmploymentsSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_external_identifier**
> PersonExternalIdentifierV20 view_external_identifier(orcid, put_code)

Fetch external identifier

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch external identifier
    api_response = api_instance.view_external_identifier(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_external_identifier: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**PersonExternalIdentifierV20**](PersonExternalIdentifierV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_external_identifiers**
> PersonExternalIdentifiersV20 view_external_identifiers(orcid)

Fetch external identifiers

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch external identifiers
    api_response = api_instance.view_external_identifiers(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_external_identifiers: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**PersonExternalIdentifiersV20**](PersonExternalIdentifiersV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_funding**
> FundingV20 view_funding(orcid, put_code)

Fetch a Funding

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Funding
    api_response = api_instance.view_funding(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_funding: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**FundingV20**](FundingV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_funding_summary**
> FundingSummaryV20 view_funding_summary(orcid, put_code)

Fetch a Funding Summary

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Funding Summary
    api_response = api_instance.view_funding_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_funding_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**FundingSummaryV20**](FundingSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_fundings**
> FundingsV20 view_fundings(orcid)

Fetch all fundings

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all fundings
    api_response = api_instance.view_fundings(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_fundings: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**FundingsV20**](FundingsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_group_id_record**
> GroupIdRecord view_group_id_record(put_code)

Fetch a Group

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 

try:
    # Fetch a Group
    api_response = api_instance.view_group_id_record(put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 

### Return type

[**GroupIdRecord**](GroupIdRecord.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_group_id_records**
> GroupIdRecords view_group_id_records(page_size=page_size, page=page, name=name, group_id=group_id)

Fetch Groups

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
page_size = 'page_size_example' # str |  (optional)
page = 'page_example' # str |  (optional)
name = 'name_example' # str |  (optional)
group_id = 'group_id_example' # str |  (optional)

try:
    # Fetch Groups
    api_response = api_instance.view_group_id_records(page_size=page_size, page=page, name=name, group_id=group_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_group_id_records: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page_size** | **str**|  | [optional] 
 **page** | **str**|  | [optional] 
 **name** | **str**|  | [optional] 
 **group_id** | **str**|  | [optional] 

### Return type

[**GroupIdRecords**](GroupIdRecords.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_keyword**
> KeywordV20 view_keyword(orcid, put_code)

Fetch keyword

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch keyword
    api_response = api_instance.view_keyword(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_keyword: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**KeywordV20**](KeywordV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_keywords**
> KeywordsV20 view_keywords(orcid)

Fetch keywords

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch keywords
    api_response = api_instance.view_keywords(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_keywords: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**KeywordsV20**](KeywordsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_other_name**
> OtherNameV20 view_other_name(orcid, put_code)

Fetch Other name

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch Other name
    api_response = api_instance.view_other_name(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_other_name: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**OtherNameV20**](OtherNameV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_other_names**
> OtherNamesV20 view_other_names(orcid)

Fetch Other names

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch Other names
    api_response = api_instance.view_other_names(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_other_names: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**OtherNamesV20**](OtherNamesV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_review**
> PeerReviewV20 view_peer_review(orcid, put_code)

Fetch a Peer Review

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Peer Review
    api_response = api_instance.view_peer_review(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_peer_review: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**PeerReviewV20**](PeerReviewV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_review_summary**
> PeerReviewSummaryV20 view_peer_review_summary(orcid, put_code)

Fetch a Peer Review Summary

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Peer Review Summary
    api_response = api_instance.view_peer_review_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_peer_review_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**PeerReviewSummaryV20**](PeerReviewSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_reviews**
> PeerReviewsV20 view_peer_reviews(orcid)

Fetch all peer reviews

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all peer reviews
    api_response = api_instance.view_peer_reviews(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_peer_reviews: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**PeerReviewsV20**](PeerReviewsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_permission_notification**
> Notification view_permission_notification(orcid, id)

Fetch a notification by id

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
id = 789 # int | 

try:
    # Fetch a notification by id
    api_response = api_instance.view_permission_notification(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_permission_notification: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **id** | **int**|  | 

### Return type

[**Notification**](Notification.md)

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_person**
> PersonV20 view_person(orcid)

Fetch person details

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch person details
    api_response = api_instance.view_person(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_person: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**PersonV20**](PersonV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_personal_details**
> PersonalDetailsV20 view_personal_details(orcid)

Fetch personal details for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch personal details for an ORCID ID
    api_response = api_instance.view_personal_details(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_personal_details: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**PersonalDetailsV20**](PersonalDetailsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_record**
> RecordV20 view_record(orcid)

Fetch record details

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch record details
    api_response = api_instance.view_record(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**RecordV20**](RecordV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_researcher_url**
> ResearcherUrlsV20 view_researcher_url(orcid, put_code)

Fetch one researcher url for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch one researcher url for an ORCID ID
    api_response = api_instance.view_researcher_url(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_researcher_url: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**ResearcherUrlsV20**](ResearcherUrlsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_researcher_urls**
> ResearcherUrlsV20 view_researcher_urls(orcid)

Fetch all researcher urls for an ORCID ID

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all researcher urls for an ORCID ID
    api_response = api_instance.view_researcher_urls(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_researcher_urls: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**ResearcherUrlsV20**](ResearcherUrlsV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_specified_works**
> WorkBulkV20 view_specified_works(orcid, put_codes)

Fetch specified works

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_codes = 'put_codes_example' # str | 

try:
    # Fetch specified works
    api_response = api_instance.view_specified_works(orcid, put_codes)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_specified_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_codes** | **str**|  | 

### Return type

[**WorkBulkV20**](WorkBulkV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_work**
> WorkV20 view_work(orcid, put_code)

Fetch a Work

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Work
    api_response = api_instance.view_work(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_work: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**WorkV20**](WorkV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_work_summary**
> WorkSummaryV20 view_work_summary(orcid, put_code)

Fetch a Work Summary

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Work Summary
    api_response = api_instance.view_work_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_work_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**WorkSummaryV20**](WorkSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_works**
> WorksSummaryV20 view_works(orcid)

Fetch all works

### Example
```python
from __future__ import print_function
import time
import orcid_api_v3
from orcid_api_v3.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
configuration = orcid_api_v3.Configuration()
configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = orcid_api_v3.MemberAPIV20Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all works
    api_response = api_instance.view_works(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV20Api->view_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**WorksSummaryV20**](WorksSummaryV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

