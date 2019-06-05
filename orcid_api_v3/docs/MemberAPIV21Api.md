# orcid_api_v3.MemberAPIV21Api

All URIs are relative to *//api.orcid.org/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_permission_notification_v21**](MemberAPIV21Api.md#add_permission_notification_v21) | **POST** /v2.1/{orcid}/notification-permission | Add a notification
[**create_address_v21**](MemberAPIV21Api.md#create_address_v21) | **POST** /v2.1/{orcid}/address | Add an address
[**create_education_v21**](MemberAPIV21Api.md#create_education_v21) | **POST** /v2.1/{orcid}/education | Create an Education
[**create_employment_v21**](MemberAPIV21Api.md#create_employment_v21) | **POST** /v2.1/{orcid}/employment | Create an Employment
[**create_external_identifier_v21**](MemberAPIV21Api.md#create_external_identifier_v21) | **POST** /v2.1/{orcid}/external-identifiers | Add external identifier
[**create_funding_v21**](MemberAPIV21Api.md#create_funding_v21) | **POST** /v2.1/{orcid}/funding | Create a Funding
[**create_group_id_record_v21**](MemberAPIV21Api.md#create_group_id_record_v21) | **POST** /v2.1/group-id-record | Create a Group
[**create_keyword_v21**](MemberAPIV21Api.md#create_keyword_v21) | **POST** /v2.1/{orcid}/keywords | Add keyword
[**create_other_name_v21**](MemberAPIV21Api.md#create_other_name_v21) | **POST** /v2.1/{orcid}/other-names | Add other name
[**create_peer_review_v21**](MemberAPIV21Api.md#create_peer_review_v21) | **POST** /v2.1/{orcid}/peer-review | Create a Peer Review
[**create_researcher_url_v21**](MemberAPIV21Api.md#create_researcher_url_v21) | **POST** /v2.1/{orcid}/researcher-urls | Add a new researcher url for an ORCID ID
[**create_work_v21**](MemberAPIV21Api.md#create_work_v21) | **POST** /v2.1/{orcid}/work | Create a Work
[**create_works_v21**](MemberAPIV21Api.md#create_works_v21) | **POST** /v2.1/{orcid}/works | Create a list of Work
[**delete_address_v21**](MemberAPIV21Api.md#delete_address_v21) | **DELETE** /v2.1/{orcid}/address/{putCode} | Delete an address
[**delete_education_v21**](MemberAPIV21Api.md#delete_education_v21) | **DELETE** /v2.1/{orcid}/education/{putCode} | Delete an Education
[**delete_employment_v21**](MemberAPIV21Api.md#delete_employment_v21) | **DELETE** /v2.1/{orcid}/employment/{putCode} | Delete an Employment
[**delete_external_identifier_v21**](MemberAPIV21Api.md#delete_external_identifier_v21) | **DELETE** /v2.1/{orcid}/external-identifiers/{putCode} | Delete external identifier
[**delete_funding_v21**](MemberAPIV21Api.md#delete_funding_v21) | **DELETE** /v2.1/{orcid}/funding/{putCode} | Delete a Funding
[**delete_group_id_record_v21**](MemberAPIV21Api.md#delete_group_id_record_v21) | **DELETE** /v2.1/group-id-record/{putCode} | Delete a Group
[**delete_keyword_v21**](MemberAPIV21Api.md#delete_keyword_v21) | **DELETE** /v2.1/{orcid}/keywords/{putCode} | Delete keyword
[**delete_other_name_v21**](MemberAPIV21Api.md#delete_other_name_v21) | **DELETE** /v2.1/{orcid}/other-names/{putCode} | Delete other name
[**delete_peer_review_v21**](MemberAPIV21Api.md#delete_peer_review_v21) | **DELETE** /v2.1/{orcid}/peer-review/{putCode} | Delete a Peer Review
[**delete_researcher_url_v21**](MemberAPIV21Api.md#delete_researcher_url_v21) | **DELETE** /v2.1/{orcid}/researcher-urls/{putCode} | Delete one researcher url from an ORCID ID
[**delete_work_v21**](MemberAPIV21Api.md#delete_work_v21) | **DELETE** /v2.1/{orcid}/work/{putCode} | Delete a Work
[**edit_address_v21**](MemberAPIV21Api.md#edit_address_v21) | **PUT** /v2.1/{orcid}/address/{putCode} | Edit an address
[**edit_external_identifier_v21**](MemberAPIV21Api.md#edit_external_identifier_v21) | **PUT** /v2.1/{orcid}/external-identifiers/{putCode} | Edit external identifier
[**edit_keyword_v21**](MemberAPIV21Api.md#edit_keyword_v21) | **PUT** /v2.1/{orcid}/keywords/{putCode} | Edit keyword
[**edit_other_name_v21**](MemberAPIV21Api.md#edit_other_name_v21) | **PUT** /v2.1/{orcid}/other-names/{putCode} | Edit other name
[**edit_researcher_url_v21**](MemberAPIV21Api.md#edit_researcher_url_v21) | **PUT** /v2.1/{orcid}/researcher-urls/{putCode} | Edits researcher url for an ORCID ID
[**flag_as_archived_permission_notification_v21**](MemberAPIV21Api.md#flag_as_archived_permission_notification_v21) | **DELETE** /v2.1/{orcid}/notification-permission/{id} | Archive a notification
[**search_by_query_v21**](MemberAPIV21Api.md#search_by_query_v21) | **GET** /v2.1/search | Search records
[**update_education_v21**](MemberAPIV21Api.md#update_education_v21) | **PUT** /v2.1/{orcid}/education/{putCode} | Update an Education
[**update_employment_v21**](MemberAPIV21Api.md#update_employment_v21) | **PUT** /v2.1/{orcid}/employment/{putCode} | Update an Employment
[**update_funding_v21**](MemberAPIV21Api.md#update_funding_v21) | **PUT** /v2.1/{orcid}/funding/{putCode} | Update a Funding
[**update_group_id_record_v21**](MemberAPIV21Api.md#update_group_id_record_v21) | **PUT** /v2.1/group-id-record/{putCode} | Update a Group
[**update_peer_review_v21**](MemberAPIV21Api.md#update_peer_review_v21) | **PUT** /v2.1/{orcid}/peer-review/{putCode} | Update a Peer Review
[**update_work_v21**](MemberAPIV21Api.md#update_work_v21) | **PUT** /v2.1/{orcid}/work/{putCode} | Update a Work
[**view_activities_v21**](MemberAPIV21Api.md#view_activities_v21) | **GET** /v2.1/{orcid}/activities | Fetch all activities
[**view_address_v21**](MemberAPIV21Api.md#view_address_v21) | **GET** /v2.1/{orcid}/address/{putCode} | Fetch an address
[**view_addresses_v21**](MemberAPIV21Api.md#view_addresses_v21) | **GET** /v2.1/{orcid}/address | Fetch all addresses of a profile
[**view_biography_v21**](MemberAPIV21Api.md#view_biography_v21) | **GET** /v2.1/{orcid}/biography | Get biography details
[**view_client_v21**](MemberAPIV21Api.md#view_client_v21) | **GET** /v2.1/client/{client_id} | Fetch client details
[**view_education_summary_v21**](MemberAPIV21Api.md#view_education_summary_v21) | **GET** /v2.1/{orcid}/education/summary/{putCode} | Fetch an Education summary
[**view_education_v21**](MemberAPIV21Api.md#view_education_v21) | **GET** /v2.1/{orcid}/education/{putCode} | Fetch an Education
[**view_educations_v21**](MemberAPIV21Api.md#view_educations_v21) | **GET** /v2.1/{orcid}/educations | Fetch all educations
[**view_emails_v21**](MemberAPIV21Api.md#view_emails_v21) | **GET** /v2.1/{orcid}/email | Fetch all emails for an ORCID ID
[**view_employment_summary_v21**](MemberAPIV21Api.md#view_employment_summary_v21) | **GET** /v2.1/{orcid}/employment/summary/{putCode} | Fetch an Employment Summary
[**view_employment_v21**](MemberAPIV21Api.md#view_employment_v21) | **GET** /v2.1/{orcid}/employment/{putCode} | Fetch an Employment
[**view_employments_v21**](MemberAPIV21Api.md#view_employments_v21) | **GET** /v2.1/{orcid}/employments | Fetch all employments
[**view_external_identifier_v21**](MemberAPIV21Api.md#view_external_identifier_v21) | **GET** /v2.1/{orcid}/external-identifiers/{putCode} | Fetch external identifier
[**view_external_identifiers_v21**](MemberAPIV21Api.md#view_external_identifiers_v21) | **GET** /v2.1/{orcid}/external-identifiers | Fetch external identifiers
[**view_funding_summary_v21**](MemberAPIV21Api.md#view_funding_summary_v21) | **GET** /v2.1/{orcid}/funding/summary/{putCode} | Fetch a Funding Summary
[**view_funding_v21**](MemberAPIV21Api.md#view_funding_v21) | **GET** /v2.1/{orcid}/funding/{putCode} | Fetch a Funding
[**view_fundings_v21**](MemberAPIV21Api.md#view_fundings_v21) | **GET** /v2.1/{orcid}/fundings | Fetch all fundings
[**view_group_id_record_v21**](MemberAPIV21Api.md#view_group_id_record_v21) | **GET** /v2.1/group-id-record/{putCode} | Fetch a Group
[**view_group_id_records_v21**](MemberAPIV21Api.md#view_group_id_records_v21) | **GET** /v2.1/group-id-record | Fetch Groups
[**view_keyword_v21**](MemberAPIV21Api.md#view_keyword_v21) | **GET** /v2.1/{orcid}/keywords/{putCode} | Fetch keyword
[**view_keywords_v21**](MemberAPIV21Api.md#view_keywords_v21) | **GET** /v2.1/{orcid}/keywords | Fetch keywords
[**view_other_name_v21**](MemberAPIV21Api.md#view_other_name_v21) | **GET** /v2.1/{orcid}/other-names/{putCode} | Fetch Other name
[**view_other_names_v21**](MemberAPIV21Api.md#view_other_names_v21) | **GET** /v2.1/{orcid}/other-names | Fetch Other names
[**view_peer_review_summary_v21**](MemberAPIV21Api.md#view_peer_review_summary_v21) | **GET** /v2.1/{orcid}/peer-review/summary/{putCode} | Fetch a Peer Review Summary
[**view_peer_review_v21**](MemberAPIV21Api.md#view_peer_review_v21) | **GET** /v2.1/{orcid}/peer-review/{putCode} | Fetch a Peer Review
[**view_peer_reviews_v21**](MemberAPIV21Api.md#view_peer_reviews_v21) | **GET** /v2.1/{orcid}/peer-reviews | Fetch all peer reviews
[**view_permission_notification_v21**](MemberAPIV21Api.md#view_permission_notification_v21) | **GET** /v2.1/{orcid}/notification-permission/{id} | Fetch a notification by id
[**view_person_v21**](MemberAPIV21Api.md#view_person_v21) | **GET** /v2.1/{orcid}/person | Fetch person details
[**view_personal_details_v21**](MemberAPIV21Api.md#view_personal_details_v21) | **GET** /v2.1/{orcid}/personal-details | Fetch personal details for an ORCID ID
[**view_record_v21**](MemberAPIV21Api.md#view_record_v21) | **GET** /v2.1/{orcid} | Fetch record details
[**view_researcher_url_v21**](MemberAPIV21Api.md#view_researcher_url_v21) | **GET** /v2.1/{orcid}/researcher-urls/{putCode} | Fetch one researcher url for an ORCID ID
[**view_researcher_urls_v21**](MemberAPIV21Api.md#view_researcher_urls_v21) | **GET** /v2.1/{orcid}/researcher-urls | Fetch all researcher urls for an ORCID ID
[**view_specified_works_v21**](MemberAPIV21Api.md#view_specified_works_v21) | **GET** /v2.1/{orcid}/works/{putCodes} | Fetch specified works
[**view_work_summary_v21**](MemberAPIV21Api.md#view_work_summary_v21) | **GET** /v2.1/{orcid}/work/summary/{putCode} | Fetch a Work Summary
[**view_work_v21**](MemberAPIV21Api.md#view_work_v21) | **GET** /v2.1/{orcid}/work/{putCode} | Fetch a Work
[**view_works_v21**](MemberAPIV21Api.md#view_works_v21) | **GET** /v2.1/{orcid}/works | Fetch all works

# **add_permission_notification_v21**
> str add_permission_notification_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.NotificationPermissionV20() # NotificationPermissionV20 |  (optional)

try:
    # Add a notification
    api_response = api_instance.add_permission_notification_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->add_permission_notification_v21: %s\n" % e)
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

# **create_address_v21**
> create_address_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.AddressV20() # AddressV20 |  (optional)

try:
    # Add an address
    api_instance.create_address_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_address_v21: %s\n" % e)
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

# **create_education_v21**
> str create_education_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.EducationV20() # EducationV20 |  (optional)

try:
    # Create an Education
    api_response = api_instance.create_education_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_education_v21: %s\n" % e)
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

# **create_employment_v21**
> str create_employment_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.EmploymentV20() # EmploymentV20 |  (optional)

try:
    # Create an Employment
    api_response = api_instance.create_employment_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_employment_v21: %s\n" % e)
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

# **create_external_identifier_v21**
> create_external_identifier_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.PersonExternalIdentifierV20() # PersonExternalIdentifierV20 |  (optional)

try:
    # Add external identifier
    api_instance.create_external_identifier_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_external_identifier_v21: %s\n" % e)
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

# **create_funding_v21**
> str create_funding_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.FundingV20() # FundingV20 |  (optional)

try:
    # Create a Funding
    api_response = api_instance.create_funding_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_funding_v21: %s\n" % e)
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

# **create_group_id_record_v21**
> create_group_id_record_v21(body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
body = orcid_api_v3.GroupIdRecord() # GroupIdRecord |  (optional)

try:
    # Create a Group
    api_instance.create_group_id_record_v21(body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_group_id_record_v21: %s\n" % e)
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

# **create_keyword_v21**
> create_keyword_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.KeywordV20() # KeywordV20 |  (optional)

try:
    # Add keyword
    api_instance.create_keyword_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_keyword_v21: %s\n" % e)
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

# **create_other_name_v21**
> create_other_name_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.OtherNameV20() # OtherNameV20 |  (optional)

try:
    # Add other name
    api_instance.create_other_name_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_other_name_v21: %s\n" % e)
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

# **create_peer_review_v21**
> str create_peer_review_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.PeerReviewV20() # PeerReviewV20 |  (optional)

try:
    # Create a Peer Review
    api_response = api_instance.create_peer_review_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_peer_review_v21: %s\n" % e)
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

# **create_researcher_url_v21**
> create_researcher_url_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.ResearcherUrlV20() # ResearcherUrlV20 |  (optional)

try:
    # Add a new researcher url for an ORCID ID
    api_instance.create_researcher_url_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_researcher_url_v21: %s\n" % e)
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

# **create_work_v21**
> str create_work_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.WorkV20() # WorkV20 |  (optional)

try:
    # Create a Work
    api_response = api_instance.create_work_v21(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_work_v21: %s\n" % e)
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

# **create_works_v21**
> create_works_v21(orcid, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
body = orcid_api_v3.WorkBulkV20() # WorkBulkV20 |  (optional)

try:
    # Create a list of Work
    api_instance.create_works_v21(orcid, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->create_works_v21: %s\n" % e)
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

# **delete_address_v21**
> delete_address_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an address
    api_instance.delete_address_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_address_v21: %s\n" % e)
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

# **delete_education_v21**
> delete_education_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an Education
    api_instance.delete_education_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_education_v21: %s\n" % e)
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

# **delete_employment_v21**
> delete_employment_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete an Employment
    api_instance.delete_employment_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_employment_v21: %s\n" % e)
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

# **delete_external_identifier_v21**
> delete_external_identifier_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete external identifier
    api_instance.delete_external_identifier_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_external_identifier_v21: %s\n" % e)
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

# **delete_funding_v21**
> delete_funding_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Funding
    api_instance.delete_funding_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_funding_v21: %s\n" % e)
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

# **delete_group_id_record_v21**
> delete_group_id_record_v21(put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 

try:
    # Delete a Group
    api_instance.delete_group_id_record_v21(put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_group_id_record_v21: %s\n" % e)
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

# **delete_keyword_v21**
> delete_keyword_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete keyword
    api_instance.delete_keyword_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_keyword_v21: %s\n" % e)
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

# **delete_other_name_v21**
> delete_other_name_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete other name
    api_instance.delete_other_name_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_other_name_v21: %s\n" % e)
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

# **delete_peer_review_v21**
> delete_peer_review_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Peer Review
    api_instance.delete_peer_review_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_peer_review_v21: %s\n" % e)
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

# **delete_researcher_url_v21**
> delete_researcher_url_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete one researcher url from an ORCID ID
    api_instance.delete_researcher_url_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_researcher_url_v21: %s\n" % e)
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

# **delete_work_v21**
> delete_work_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Delete a Work
    api_instance.delete_work_v21(orcid, put_code)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->delete_work_v21: %s\n" % e)
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

# **edit_address_v21**
> edit_address_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.AddressV20() # AddressV20 |  (optional)

try:
    # Edit an address
    api_instance.edit_address_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->edit_address_v21: %s\n" % e)
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

# **edit_external_identifier_v21**
> edit_external_identifier_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.PersonExternalIdentifierV20() # PersonExternalIdentifierV20 |  (optional)

try:
    # Edit external identifier
    api_instance.edit_external_identifier_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->edit_external_identifier_v21: %s\n" % e)
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

# **edit_keyword_v21**
> edit_keyword_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.KeywordV20() # KeywordV20 |  (optional)

try:
    # Edit keyword
    api_instance.edit_keyword_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->edit_keyword_v21: %s\n" % e)
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

# **edit_other_name_v21**
> edit_other_name_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.OtherNameV20() # OtherNameV20 |  (optional)

try:
    # Edit other name
    api_instance.edit_other_name_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->edit_other_name_v21: %s\n" % e)
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

# **edit_researcher_url_v21**
> edit_researcher_url_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.ResearcherUrlV20() # ResearcherUrlV20 |  (optional)

try:
    # Edits researcher url for an ORCID ID
    api_instance.edit_researcher_url_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->edit_researcher_url_v21: %s\n" % e)
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

# **flag_as_archived_permission_notification_v21**
> Notification flag_as_archived_permission_notification_v21(orcid, id)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
id = 789 # int | 

try:
    # Archive a notification
    api_response = api_instance.flag_as_archived_permission_notification_v21(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->flag_as_archived_permission_notification_v21: %s\n" % e)
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

# **search_by_query_v21**
> SearchV20 search_by_query_v21(q=q)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
q = 'q_example' # str |  (optional)

try:
    # Search records
    api_response = api_instance.search_by_query_v21(q=q)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->search_by_query_v21: %s\n" % e)
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

# **update_education_v21**
> update_education_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.EducationV20() # EducationV20 |  (optional)

try:
    # Update an Education
    api_instance.update_education_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_education_v21: %s\n" % e)
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

# **update_employment_v21**
> update_employment_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.EmploymentV20() # EmploymentV20 |  (optional)

try:
    # Update an Employment
    api_instance.update_employment_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_employment_v21: %s\n" % e)
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

# **update_funding_v21**
> update_funding_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.FundingV20() # FundingV20 |  (optional)

try:
    # Update a Funding
    api_instance.update_funding_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_funding_v21: %s\n" % e)
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

# **update_group_id_record_v21**
> update_group_id_record_v21(put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 
body = orcid_api_v3.GroupIdRecord() # GroupIdRecord |  (optional)

try:
    # Update a Group
    api_instance.update_group_id_record_v21(put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_group_id_record_v21: %s\n" % e)
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

# **update_peer_review_v21**
> update_peer_review_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.PeerReviewV20() # PeerReviewV20 |  (optional)

try:
    # Update a Peer Review
    api_instance.update_peer_review_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_peer_review_v21: %s\n" % e)
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

# **update_work_v21**
> update_work_v21(orcid, put_code, body=body)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = orcid_api_v3.WorkV20() # WorkV20 |  (optional)

try:
    # Update a Work
    api_instance.update_work_v21(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->update_work_v21: %s\n" % e)
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

# **view_activities_v21**
> ActivitiesSummaryV20 view_activities_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all activities
    api_response = api_instance.view_activities_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_activities_v21: %s\n" % e)
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

# **view_address_v21**
> AddressV20 view_address_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an address
    api_response = api_instance.view_address_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_address_v21: %s\n" % e)
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

# **view_addresses_v21**
> AddressesV20 view_addresses_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all addresses of a profile
    api_response = api_instance.view_addresses_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_addresses_v21: %s\n" % e)
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

# **view_biography_v21**
> view_biography_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Get biography details
    api_instance.view_biography_v21(orcid)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_biography_v21: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_client_v21**
> ClientSummary view_client_v21(client_id)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
client_id = 'client_id_example' # str | 

try:
    # Fetch client details
    api_response = api_instance.view_client_v21(client_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_client_v21: %s\n" % e)
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

# **view_education_summary_v21**
> EducationSummaryV20 view_education_summary_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Education summary
    api_response = api_instance.view_education_summary_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_education_summary_v21: %s\n" % e)
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

# **view_education_v21**
> EducationV20 view_education_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Education
    api_response = api_instance.view_education_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_education_v21: %s\n" % e)
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

# **view_educations_v21**
> EducationsSummaryV20 view_educations_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all educations
    api_response = api_instance.view_educations_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_educations_v21: %s\n" % e)
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

# **view_emails_v21**
> EmailsV20 view_emails_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all emails for an ORCID ID
    api_response = api_instance.view_emails_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_emails_v21: %s\n" % e)
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

# **view_employment_summary_v21**
> EmploymentSummaryV20 view_employment_summary_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Employment Summary
    api_response = api_instance.view_employment_summary_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_employment_summary_v21: %s\n" % e)
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

# **view_employment_v21**
> EmploymentV20 view_employment_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch an Employment
    api_response = api_instance.view_employment_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_employment_v21: %s\n" % e)
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

# **view_employments_v21**
> EmploymentsSummaryV20 view_employments_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all employments
    api_response = api_instance.view_employments_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_employments_v21: %s\n" % e)
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

# **view_external_identifier_v21**
> PersonExternalIdentifierV20 view_external_identifier_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch external identifier
    api_response = api_instance.view_external_identifier_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_external_identifier_v21: %s\n" % e)
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

# **view_external_identifiers_v21**
> PersonExternalIdentifiersV20 view_external_identifiers_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch external identifiers
    api_response = api_instance.view_external_identifiers_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_external_identifiers_v21: %s\n" % e)
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

# **view_funding_summary_v21**
> FundingSummaryV20 view_funding_summary_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Funding Summary
    api_response = api_instance.view_funding_summary_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_funding_summary_v21: %s\n" % e)
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

# **view_funding_v21**
> FundingV20 view_funding_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Funding
    api_response = api_instance.view_funding_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_funding_v21: %s\n" % e)
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

# **view_fundings_v21**
> FundingsV20 view_fundings_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all fundings
    api_response = api_instance.view_fundings_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_fundings_v21: %s\n" % e)
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

# **view_group_id_record_v21**
> GroupIdRecord view_group_id_record_v21(put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
put_code = 'put_code_example' # str | 

try:
    # Fetch a Group
    api_response = api_instance.view_group_id_record_v21(put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_group_id_record_v21: %s\n" % e)
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

# **view_group_id_records_v21**
> GroupIdRecords view_group_id_records_v21(page_size=page_size, page=page, name=name, group_id=group_id)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
page_size = 'page_size_example' # str |  (optional)
page = 'page_example' # str |  (optional)
name = 'name_example' # str |  (optional)
group_id = 'group_id_example' # str |  (optional)

try:
    # Fetch Groups
    api_response = api_instance.view_group_id_records_v21(page_size=page_size, page=page, name=name, group_id=group_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_group_id_records_v21: %s\n" % e)
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

# **view_keyword_v21**
> KeywordV20 view_keyword_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch keyword
    api_response = api_instance.view_keyword_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_keyword_v21: %s\n" % e)
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

# **view_keywords_v21**
> KeywordsV20 view_keywords_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch keywords
    api_response = api_instance.view_keywords_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_keywords_v21: %s\n" % e)
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

# **view_other_name_v21**
> OtherNameV20 view_other_name_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch Other name
    api_response = api_instance.view_other_name_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_other_name_v21: %s\n" % e)
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

# **view_other_names_v21**
> OtherNameV20 view_other_names_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch Other names
    api_response = api_instance.view_other_names_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_other_names_v21: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**OtherNameV20**](OtherNameV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_review_summary_v21**
> PeerReviewSummaryV20 view_peer_review_summary_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Peer Review Summary
    api_response = api_instance.view_peer_review_summary_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_peer_review_summary_v21: %s\n" % e)
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

# **view_peer_review_v21**
> PeerReviewV20 view_peer_review_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Peer Review
    api_response = api_instance.view_peer_review_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_peer_review_v21: %s\n" % e)
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

# **view_peer_reviews_v21**
> PeerReviewsV20 view_peer_reviews_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all peer reviews
    api_response = api_instance.view_peer_reviews_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_peer_reviews_v21: %s\n" % e)
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

# **view_permission_notification_v21**
> Notification view_permission_notification_v21(orcid, id)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
id = 789 # int | 

try:
    # Fetch a notification by id
    api_response = api_instance.view_permission_notification_v21(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_permission_notification_v21: %s\n" % e)
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

# **view_person_v21**
> PersonV20 view_person_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch person details
    api_response = api_instance.view_person_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_person_v21: %s\n" % e)
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

# **view_personal_details_v21**
> PersonalDetailsV20 view_personal_details_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch personal details for an ORCID ID
    api_response = api_instance.view_personal_details_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_personal_details_v21: %s\n" % e)
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

# **view_record_v21**
> RecordV20 view_record_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch record details
    api_response = api_instance.view_record_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_record_v21: %s\n" % e)
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

# **view_researcher_url_v21**
> ResearcherUrlV20 view_researcher_url_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch one researcher url for an ORCID ID
    api_response = api_instance.view_researcher_url_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_researcher_url_v21: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**ResearcherUrlV20**](ResearcherUrlV20.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: */*

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_researcher_urls_v21**
> ResearcherUrlsV20 view_researcher_urls_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all researcher urls for an ORCID ID
    api_response = api_instance.view_researcher_urls_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_researcher_urls_v21: %s\n" % e)
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

# **view_specified_works_v21**
> WorkBulkV20 view_specified_works_v21(orcid, put_codes)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_codes = 'put_codes_example' # str | 

try:
    # Fetch specified works
    api_response = api_instance.view_specified_works_v21(orcid, put_codes)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_specified_works_v21: %s\n" % e)
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

# **view_work_summary_v21**
> WorkSummaryV20 view_work_summary_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Work Summary
    api_response = api_instance.view_work_summary_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_work_summary_v21: %s\n" % e)
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

# **view_work_v21**
> WorkV20 view_work_v21(orcid, put_code)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try:
    # Fetch a Work
    api_response = api_instance.view_work_v21(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_work_v21: %s\n" % e)
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

# **view_works_v21**
> WorksSummaryV20 view_works_v21(orcid)

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
api_instance = orcid_api_v3.MemberAPIV21Api(orcid_api_v3.ApiClient(configuration))
orcid = 'orcid_example' # str | 

try:
    # Fetch all works
    api_response = api_instance.view_works_v21(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling MemberAPIV21Api->view_works_v21: %s\n" % e)
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

