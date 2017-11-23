# swagger_client.DevelopmentMemberAPIV30Dev1Api

All URIs are relative to *https://api.orcid.org*

Method | HTTP request | Description
------------- | ------------- | -------------
[**add_permission_notification_json**](DevelopmentMemberAPIV30Dev1Api.md#add_permission_notification_json) | **POST** /v3.0_dev1/{orcid}/notification-permission | Add a notification
[**create_address_json**](DevelopmentMemberAPIV30Dev1Api.md#create_address_json) | **POST** /v3.0_dev1/{orcid}/address | Add an address
[**create_education_json**](DevelopmentMemberAPIV30Dev1Api.md#create_education_json) | **POST** /v3.0_dev1/{orcid}/education | Create an Education
[**create_employment_json**](DevelopmentMemberAPIV30Dev1Api.md#create_employment_json) | **POST** /v3.0_dev1/{orcid}/employment | Create an Employment
[**create_external_identifier_json**](DevelopmentMemberAPIV30Dev1Api.md#create_external_identifier_json) | **POST** /v3.0_dev1/{orcid}/external-identifiers | Add external identifier
[**create_funding_json**](DevelopmentMemberAPIV30Dev1Api.md#create_funding_json) | **POST** /v3.0_dev1/{orcid}/funding | Create a Funding
[**create_group_id_record_json**](DevelopmentMemberAPIV30Dev1Api.md#create_group_id_record_json) | **POST** /v3.0_dev1/group-id-record | Create a Group
[**create_keyword_json**](DevelopmentMemberAPIV30Dev1Api.md#create_keyword_json) | **POST** /v3.0_dev1/{orcid}/keywords | Add keyword
[**create_other_name_json**](DevelopmentMemberAPIV30Dev1Api.md#create_other_name_json) | **POST** /v3.0_dev1/{orcid}/other-names | Add other name
[**create_peer_review_json**](DevelopmentMemberAPIV30Dev1Api.md#create_peer_review_json) | **POST** /v3.0_dev1/{orcid}/peer-review | Create a Peer Review
[**create_researcher_url_json**](DevelopmentMemberAPIV30Dev1Api.md#create_researcher_url_json) | **POST** /v3.0_dev1/{orcid}/researcher-urls | Add a new researcher url for an ORCID ID
[**create_work_json**](DevelopmentMemberAPIV30Dev1Api.md#create_work_json) | **POST** /v3.0_dev1/{orcid}/work | Create a Work
[**create_works**](DevelopmentMemberAPIV30Dev1Api.md#create_works) | **POST** /v3.0_dev1/{orcid}/works | Create a listo of Work
[**delete_address**](DevelopmentMemberAPIV30Dev1Api.md#delete_address) | **DELETE** /v3.0_dev1/{orcid}/address/{putCode} | Delete an address
[**delete_education**](DevelopmentMemberAPIV30Dev1Api.md#delete_education) | **DELETE** /v3.0_dev1/{orcid}/education/{putCode} | Delete an Education
[**delete_employment**](DevelopmentMemberAPIV30Dev1Api.md#delete_employment) | **DELETE** /v3.0_dev1/{orcid}/employment/{putCode} | Delete an Employment
[**delete_external_identifier**](DevelopmentMemberAPIV30Dev1Api.md#delete_external_identifier) | **DELETE** /v3.0_dev1/{orcid}/external-identifiers/{putCode} | Delete external identifier
[**delete_funding**](DevelopmentMemberAPIV30Dev1Api.md#delete_funding) | **DELETE** /v3.0_dev1/{orcid}/funding/{putCode} | Delete a Funding
[**delete_group_id_record**](DevelopmentMemberAPIV30Dev1Api.md#delete_group_id_record) | **DELETE** /v3.0_dev1/group-id-record/{putCode} | Delete a Group
[**delete_keyword**](DevelopmentMemberAPIV30Dev1Api.md#delete_keyword) | **DELETE** /v3.0_dev1/{orcid}/keywords/{putCode} | Delete keyword
[**delete_other_name**](DevelopmentMemberAPIV30Dev1Api.md#delete_other_name) | **DELETE** /v3.0_dev1/{orcid}/other-names/{putCode} | Delete other name
[**delete_peer_review**](DevelopmentMemberAPIV30Dev1Api.md#delete_peer_review) | **DELETE** /v3.0_dev1/{orcid}/peer-review/{putCode} | Delete a Peer Review
[**delete_researcher_url**](DevelopmentMemberAPIV30Dev1Api.md#delete_researcher_url) | **DELETE** /v3.0_dev1/{orcid}/researcher-urls/{putCode} | Delete one researcher url from an ORCID ID
[**delete_work**](DevelopmentMemberAPIV30Dev1Api.md#delete_work) | **DELETE** /v3.0_dev1/{orcid}/work/{putCode} | Delete a Work
[**edit_address**](DevelopmentMemberAPIV30Dev1Api.md#edit_address) | **PUT** /v3.0_dev1/{orcid}/address/{putCode} | Edit an address
[**edit_external_identifier_json**](DevelopmentMemberAPIV30Dev1Api.md#edit_external_identifier_json) | **PUT** /v3.0_dev1/{orcid}/external-identifiers/{putCode} | Edit external identifier
[**edit_keyword_json**](DevelopmentMemberAPIV30Dev1Api.md#edit_keyword_json) | **PUT** /v3.0_dev1/{orcid}/keywords/{putCode} | Edit keyword
[**edit_other_name_json**](DevelopmentMemberAPIV30Dev1Api.md#edit_other_name_json) | **PUT** /v3.0_dev1/{orcid}/other-names/{putCode} | Edit other name
[**edit_researcher_url_json**](DevelopmentMemberAPIV30Dev1Api.md#edit_researcher_url_json) | **PUT** /v3.0_dev1/{orcid}/researcher-urls/{putCode} | Edits researcher url for an ORCID ID
[**flag_as_archived_permission_notification**](DevelopmentMemberAPIV30Dev1Api.md#flag_as_archived_permission_notification) | **DELETE** /v3.0_dev1/{orcid}/notification-permission/{id} | Archive a notification
[**search_by_query_xml**](DevelopmentMemberAPIV30Dev1Api.md#search_by_query_xml) | **GET** /v3.0_dev1/search | Search records
[**update_education_json**](DevelopmentMemberAPIV30Dev1Api.md#update_education_json) | **PUT** /v3.0_dev1/{orcid}/education/{putCode} | Update an Education
[**update_employment_json**](DevelopmentMemberAPIV30Dev1Api.md#update_employment_json) | **PUT** /v3.0_dev1/{orcid}/employment/{putCode} | Update an Employment
[**update_funding_json**](DevelopmentMemberAPIV30Dev1Api.md#update_funding_json) | **PUT** /v3.0_dev1/{orcid}/funding/{putCode} | Update a Funding
[**update_group_id_record_json**](DevelopmentMemberAPIV30Dev1Api.md#update_group_id_record_json) | **PUT** /v3.0_dev1/group-id-record/{putCode} | Update a Group
[**update_peer_review_json**](DevelopmentMemberAPIV30Dev1Api.md#update_peer_review_json) | **PUT** /v3.0_dev1/{orcid}/peer-review/{putCode} | Update a Peer Review
[**update_work_json**](DevelopmentMemberAPIV30Dev1Api.md#update_work_json) | **PUT** /v3.0_dev1/{orcid}/work/{putCode} | Update a Work
[**view_activities**](DevelopmentMemberAPIV30Dev1Api.md#view_activities) | **GET** /v3.0_dev1/{orcid}/activities | Fetch all activities
[**view_address**](DevelopmentMemberAPIV30Dev1Api.md#view_address) | **GET** /v3.0_dev1/{orcid}/address/{putCode} | Fetch an address
[**view_addresses**](DevelopmentMemberAPIV30Dev1Api.md#view_addresses) | **GET** /v3.0_dev1/{orcid}/address | Fetch all addresses of a profile
[**view_biography**](DevelopmentMemberAPIV30Dev1Api.md#view_biography) | **GET** /v3.0_dev1/{orcid}/biography | Get biography details
[**view_client**](DevelopmentMemberAPIV30Dev1Api.md#view_client) | **GET** /v3.0_dev1/client/{client_id} | Fetch client details
[**view_education**](DevelopmentMemberAPIV30Dev1Api.md#view_education) | **GET** /v3.0_dev1/{orcid}/education/{putCode} | Fetch an Education
[**view_education_summary**](DevelopmentMemberAPIV30Dev1Api.md#view_education_summary) | **GET** /v3.0_dev1/{orcid}/education/summary/{putCode} | Fetch an Education summary
[**view_educations**](DevelopmentMemberAPIV30Dev1Api.md#view_educations) | **GET** /v3.0_dev1/{orcid}/educations | Fetch all educations
[**view_emails**](DevelopmentMemberAPIV30Dev1Api.md#view_emails) | **GET** /v3.0_dev1/{orcid}/email | Fetch all emails for an ORCID ID
[**view_employment**](DevelopmentMemberAPIV30Dev1Api.md#view_employment) | **GET** /v3.0_dev1/{orcid}/employment/{putCode} | Fetch an Employment
[**view_employment_summary**](DevelopmentMemberAPIV30Dev1Api.md#view_employment_summary) | **GET** /v3.0_dev1/{orcid}/employment/summary/{putCode} | Fetch an Employment Summary
[**view_employments**](DevelopmentMemberAPIV30Dev1Api.md#view_employments) | **GET** /v3.0_dev1/{orcid}/employments | Fetch all employments
[**view_external_identifier**](DevelopmentMemberAPIV30Dev1Api.md#view_external_identifier) | **GET** /v3.0_dev1/{orcid}/external-identifiers/{putCode} | Fetch external identifier
[**view_external_identifiers**](DevelopmentMemberAPIV30Dev1Api.md#view_external_identifiers) | **GET** /v3.0_dev1/{orcid}/external-identifiers | Fetch external identifiers
[**view_funding**](DevelopmentMemberAPIV30Dev1Api.md#view_funding) | **GET** /v3.0_dev1/{orcid}/funding/{putCode} | Fetch a Funding
[**view_funding_summary**](DevelopmentMemberAPIV30Dev1Api.md#view_funding_summary) | **GET** /v3.0_dev1/{orcid}/funding/summary/{putCode} | Fetch a Funding Summary
[**view_fundings**](DevelopmentMemberAPIV30Dev1Api.md#view_fundings) | **GET** /v3.0_dev1/{orcid}/fundings | Fetch all fundings
[**view_group_id_record**](DevelopmentMemberAPIV30Dev1Api.md#view_group_id_record) | **GET** /v3.0_dev1/group-id-record/{putCode} | Fetch a Group
[**view_group_id_records**](DevelopmentMemberAPIV30Dev1Api.md#view_group_id_records) | **GET** /v3.0_dev1/group-id-record | Fetch Groups
[**view_keyword**](DevelopmentMemberAPIV30Dev1Api.md#view_keyword) | **GET** /v3.0_dev1/{orcid}/keywords/{putCode} | Fetch keyword
[**view_keywords**](DevelopmentMemberAPIV30Dev1Api.md#view_keywords) | **GET** /v3.0_dev1/{orcid}/keywords | Fetch keywords
[**view_other_name**](DevelopmentMemberAPIV30Dev1Api.md#view_other_name) | **GET** /v3.0_dev1/{orcid}/other-names/{putCode} | Fetch Other name
[**view_other_names**](DevelopmentMemberAPIV30Dev1Api.md#view_other_names) | **GET** /v3.0_dev1/{orcid}/other-names | Fetch Other names
[**view_peer_review**](DevelopmentMemberAPIV30Dev1Api.md#view_peer_review) | **GET** /v3.0_dev1/{orcid}/peer-review/{putCode} | Fetch a Peer Review
[**view_peer_review_summary**](DevelopmentMemberAPIV30Dev1Api.md#view_peer_review_summary) | **GET** /v3.0_dev1/{orcid}/peer-review/summary/{putCode} | Fetch a Peer Review Summary
[**view_peer_reviews**](DevelopmentMemberAPIV30Dev1Api.md#view_peer_reviews) | **GET** /v3.0_dev1/{orcid}/peer-reviews | Fetch all peer reviews
[**view_permission_notification**](DevelopmentMemberAPIV30Dev1Api.md#view_permission_notification) | **GET** /v3.0_dev1/{orcid}/notification-permission/{id} | Fetch a notification by id
[**view_person**](DevelopmentMemberAPIV30Dev1Api.md#view_person) | **GET** /v3.0_dev1/{orcid}/person | Fetch person details
[**view_personal_details**](DevelopmentMemberAPIV30Dev1Api.md#view_personal_details) | **GET** /v3.0_dev1/{orcid}/personal-details | Fetch personal details for an ORCID ID
[**view_record**](DevelopmentMemberAPIV30Dev1Api.md#view_record) | **GET** /v3.0_dev1/{orcid}{ignore} | Fetch record details
[**view_researcher_url**](DevelopmentMemberAPIV30Dev1Api.md#view_researcher_url) | **GET** /v3.0_dev1/{orcid}/researcher-urls/{putCode} | Fetch one researcher url for an ORCID ID
[**view_researcher_urls**](DevelopmentMemberAPIV30Dev1Api.md#view_researcher_urls) | **GET** /v3.0_dev1/{orcid}/researcher-urls | Fetch all researcher urls for an ORCID ID
[**view_specified_works**](DevelopmentMemberAPIV30Dev1Api.md#view_specified_works) | **GET** /v3.0_dev1/{orcid}/works/{putCodes} | Fetch specified works
[**view_work**](DevelopmentMemberAPIV30Dev1Api.md#view_work) | **GET** /v3.0_dev1/{orcid}/work/{putCode} | Fetch a Work
[**view_work_summary**](DevelopmentMemberAPIV30Dev1Api.md#view_work_summary) | **GET** /v3.0_dev1/{orcid}/work/summary/{putCode} | Fetch a Work Summary
[**view_works**](DevelopmentMemberAPIV30Dev1Api.md#view_works) | **GET** /v3.0_dev1/{orcid}/works | Fetch all works


# **add_permission_notification_json**
> str add_permission_notification_json(orcid, body=body)

Add a notification



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.NotificationPermission() # NotificationPermission |  (optional)

try: 
    # Add a notification
    api_response = api_instance.add_permission_notification_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->add_permission_notification_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**NotificationPermission**](NotificationPermission.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_two_legs](../README.md#orcid_two_legs)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_address_json**
> create_address_json(orcid, body=body)

Add an address



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Address() # Address |  (optional)

try: 
    # Add an address
    api_instance.create_address_json(orcid, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_address_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Address**](Address.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_education_json**
> str create_education_json(orcid, body=body)

Create an Education



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Education() # Education |  (optional)

try: 
    # Create an Education
    api_response = api_instance.create_education_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_education_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Education**](Education.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_employment_json**
> str create_employment_json(orcid, body=body)

Create an Employment



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Employment() # Employment |  (optional)

try: 
    # Create an Employment
    api_response = api_instance.create_employment_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_employment_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Employment**](Employment.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_external_identifier_json**
> create_external_identifier_json(orcid, body=body)

Add external identifier



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.PersonExternalIdentifier() # PersonExternalIdentifier |  (optional)

try: 
    # Add external identifier
    api_instance.create_external_identifier_json(orcid, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_external_identifier_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**PersonExternalIdentifier**](PersonExternalIdentifier.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_funding_json**
> str create_funding_json(orcid, body=body)

Create a Funding



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Funding() # Funding |  (optional)

try: 
    # Create a Funding
    api_response = api_instance.create_funding_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_funding_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Funding**](Funding.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_group_id_record_json**
> create_group_id_record_json(body=body)

Create a Group



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
body = swagger_client.GroupIdRecord() # GroupIdRecord |  (optional)

try: 
    # Create a Group
    api_instance.create_group_id_record_json(body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_group_id_record_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**GroupIdRecord**](GroupIdRecord.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_keyword_json**
> create_keyword_json(orcid, body=body)

Add keyword



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Keyword() # Keyword |  (optional)

try: 
    # Add keyword
    api_instance.create_keyword_json(orcid, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_keyword_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Keyword**](Keyword.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_other_name_json**
> create_other_name_json(orcid, body=body)

Add other name



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.OtherName() # OtherName |  (optional)

try: 
    # Add other name
    api_instance.create_other_name_json(orcid, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_other_name_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**OtherName**](OtherName.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_peer_review_json**
> str create_peer_review_json(orcid, body=body)

Create a Peer Review



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.PeerReview() # PeerReview |  (optional)

try: 
    # Create a Peer Review
    api_response = api_instance.create_peer_review_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_peer_review_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**PeerReview**](PeerReview.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_researcher_url_json**
> create_researcher_url_json(orcid, body=body)

Add a new researcher url for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.ResearcherUrl() # ResearcherUrl |  (optional)

try: 
    # Add a new researcher url for an ORCID ID
    api_instance.create_researcher_url_json(orcid, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_researcher_url_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**ResearcherUrl**](ResearcherUrl.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_work_json**
> str create_work_json(orcid, body=body)

Create a Work



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.Work() # Work |  (optional)

try: 
    # Create a Work
    api_response = api_instance.create_work_json(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_work_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**Work**](Work.md)|  | [optional] 

### Return type

**str**

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **create_works**
> str create_works(orcid, body=body)

Create a listo of Work



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
body = swagger_client.WorkBulk() # WorkBulk |  (optional)

try: 
    # Create a listo of Work
    api_response = api_instance.create_works(orcid, body=body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->create_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **body** | [**WorkBulk**](WorkBulk.md)|  | [optional] 

### Return type

**str**

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
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete an address
    api_instance.delete_address(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_address: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_education**
> delete_education(orcid, put_code)

Delete an Education



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete an Education
    api_instance.delete_education(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_education: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_employment**
> delete_employment(orcid, put_code)

Delete an Employment



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete an Employment
    api_instance.delete_employment(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_employment: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_external_identifier**
> delete_external_identifier(orcid, put_code)

Delete external identifier



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete external identifier
    api_instance.delete_external_identifier(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_external_identifier: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_funding**
> delete_funding(orcid, put_code)

Delete a Funding



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete a Funding
    api_instance.delete_funding(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_funding: %s\n" % e)
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

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_group_id_record**
> delete_group_id_record(put_code)

Delete a Group



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
put_code = 'put_code_example' # str | 

try: 
    # Delete a Group
    api_instance.delete_group_id_record(put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_keyword**
> delete_keyword(orcid, put_code)

Delete keyword



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete keyword
    api_instance.delete_keyword(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_keyword: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_other_name**
> delete_other_name(orcid, put_code)

Delete other name



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete other name
    api_instance.delete_other_name(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_other_name: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_peer_review**
> delete_peer_review(orcid, put_code)

Delete a Peer Review



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete a Peer Review
    api_instance.delete_peer_review(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_peer_review: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_researcher_url**
> delete_researcher_url(orcid, put_code)

Delete one researcher url from an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete one researcher url from an ORCID ID
    api_instance.delete_researcher_url(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_researcher_url: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **delete_work**
> delete_work(orcid, put_code)

Delete a Work



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Delete a Work
    api_instance.delete_work(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->delete_work: %s\n" % e)
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

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_address**
> edit_address(orcid, put_code, body=body)

Edit an address



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Address() # Address |  (optional)

try: 
    # Edit an address
    api_instance.edit_address(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->edit_address: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Address**](Address.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_external_identifier_json**
> edit_external_identifier_json(orcid, put_code, body=body)

Edit external identifier



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.PersonExternalIdentifier() # PersonExternalIdentifier |  (optional)

try: 
    # Edit external identifier
    api_instance.edit_external_identifier_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->edit_external_identifier_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**PersonExternalIdentifier**](PersonExternalIdentifier.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_keyword_json**
> edit_keyword_json(orcid, put_code, body=body)

Edit keyword



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Keyword() # Keyword |  (optional)

try: 
    # Edit keyword
    api_instance.edit_keyword_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->edit_keyword_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Keyword**](Keyword.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_other_name_json**
> edit_other_name_json(orcid, put_code, body=body)

Edit other name



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.OtherName() # OtherName |  (optional)

try: 
    # Edit other name
    api_instance.edit_other_name_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->edit_other_name_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**OtherName**](OtherName.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **edit_researcher_url_json**
> edit_researcher_url_json(orcid, put_code, body=body)

Edits researcher url for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.ResearcherUrl() # ResearcherUrl |  (optional)

try: 
    # Edits researcher url for an ORCID ID
    api_instance.edit_researcher_url_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->edit_researcher_url_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**ResearcherUrl**](ResearcherUrl.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **flag_as_archived_permission_notification**
> Notification flag_as_archived_permission_notification(orcid, id)

Archive a notification



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
id = 789 # int | 

try: 
    # Archive a notification
    api_response = api_instance.flag_as_archived_permission_notification(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->flag_as_archived_permission_notification: %s\n" % e)
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

 - **Content-Type**: */*
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **search_by_query_xml**
> search_by_query_xml(q=q)

Search records



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
q = 'q_example' # str |  (optional)

try: 
    # Search records
    api_instance.search_by_query_xml(q=q)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->search_by_query_xml: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **q** | **str**|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_education_json**
> update_education_json(orcid, put_code, body=body)

Update an Education



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Education() # Education |  (optional)

try: 
    # Update an Education
    api_instance.update_education_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_education_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Education**](Education.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_employment_json**
> update_employment_json(orcid, put_code, body=body)

Update an Employment



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Employment() # Employment |  (optional)

try: 
    # Update an Employment
    api_instance.update_employment_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_employment_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Employment**](Employment.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_funding_json**
> update_funding_json(orcid, put_code, body=body)

Update a Funding



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Funding() # Funding |  (optional)

try: 
    # Update a Funding
    api_instance.update_funding_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_funding_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Funding**](Funding.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_group_id_record_json**
> update_group_id_record_json(put_code, body=body)

Update a Group



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
put_code = 'put_code_example' # str | 
body = swagger_client.GroupIdRecord() # GroupIdRecord |  (optional)

try: 
    # Update a Group
    api_instance.update_group_id_record_json(put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_group_id_record_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 
 **body** | [**GroupIdRecord**](GroupIdRecord.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_peer_review_json**
> update_peer_review_json(orcid, put_code, body=body)

Update a Peer Review



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.PeerReview() # PeerReview |  (optional)

try: 
    # Update a Peer Review
    api_instance.update_peer_review_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_peer_review_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**PeerReview**](PeerReview.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **update_work_json**
> update_work_json(orcid, put_code, body=body)

Update a Work



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 
body = swagger_client.Work() # Work |  (optional)

try: 
    # Update a Work
    api_instance.update_work_json(orcid, put_code, body=body)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->update_work_json: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 
 **body** | [**Work**](Work.md)|  | [optional] 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_activities**
> ActivitiesSummary view_activities(orcid)

Fetch all activities



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all activities
    api_response = api_instance.view_activities(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_activities: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**ActivitiesSummary**](ActivitiesSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_address**
> view_address(orcid, put_code)

Fetch an address



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch an address
    api_instance.view_address(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_address: %s\n" % e)
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

# **view_addresses**
> view_addresses(orcid)

Fetch all addresses of a profile



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all addresses of a profile
    api_instance.view_addresses(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_addresses: %s\n" % e)
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

# **view_biography**
> view_biography(orcid)

Get biography details



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Get biography details
    api_instance.view_biography(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_biography: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_client**
> view_client(client_id)

Fetch client details



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
client_id = 'client_id_example' # str | 

try: 
    # Fetch client details
    api_instance.view_client(client_id)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_client: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **client_id** | **str**|  | 

### Return type

void (empty response body)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_education**
> Education view_education(orcid, put_code)

Fetch an Education



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch an Education
    api_response = api_instance.view_education(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_education: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**Education**](Education.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_education_summary**
> EducationSummary view_education_summary(orcid, put_code)

Fetch an Education summary



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch an Education summary
    api_response = api_instance.view_education_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_education_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EducationSummary**](EducationSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_educations**
> Educations view_educations(orcid)

Fetch all educations



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all educations
    api_response = api_instance.view_educations(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_educations: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**Educations**](Educations.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_emails**
> view_emails(orcid)

Fetch all emails for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all emails for an ORCID ID
    api_instance.view_emails(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_emails: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employment**
> Employment view_employment(orcid, put_code)

Fetch an Employment



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch an Employment
    api_response = api_instance.view_employment(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_employment: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**Employment**](Employment.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employment_summary**
> EmploymentSummary view_employment_summary(orcid, put_code)

Fetch an Employment Summary



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch an Employment Summary
    api_response = api_instance.view_employment_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_employment_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**EmploymentSummary**](EmploymentSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_employments**
> Employments view_employments(orcid)

Fetch all employments



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all employments
    api_response = api_instance.view_employments(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_employments: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**Employments**](Employments.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_external_identifier**
> view_external_identifier(orcid, put_code)

Fetch external identifier



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch external identifier
    api_instance.view_external_identifier(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_external_identifier: %s\n" % e)
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

# **view_external_identifiers**
> view_external_identifiers(orcid)

Fetch external identifiers



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch external identifiers
    api_instance.view_external_identifiers(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_external_identifiers: %s\n" % e)
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

# **view_funding**
> Funding view_funding(orcid, put_code)

Fetch a Funding



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Funding
    api_response = api_instance.view_funding(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_funding: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**Funding**](Funding.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_funding_summary**
> FundingSummary view_funding_summary(orcid, put_code)

Fetch a Funding Summary



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Funding Summary
    api_response = api_instance.view_funding_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_funding_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**FundingSummary**](FundingSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_fundings**
> Fundings view_fundings(orcid)

Fetch all fundings



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all fundings
    api_response = api_instance.view_fundings(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_fundings: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**Fundings**](Fundings.md)

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
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Group
    api_response = api_instance.view_group_id_record(put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_group_id_record: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **put_code** | **str**|  | 

### Return type

[**GroupIdRecord**](GroupIdRecord.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_group_id_records**
> GroupIdRecords view_group_id_records(page_size=page_size, page=page, name=name)

Fetch Groups



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
page_size = '100' # str |  (optional) (default to 100)
page = '1' # str |  (optional) (default to 1)
name = 'name_example' # str |  (optional)

try: 
    # Fetch Groups
    api_response = api_instance.view_group_id_records(page_size=page_size, page=page, name=name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_group_id_records: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **page_size** | **str**|  | [optional] [default to 100]
 **page** | **str**|  | [optional] [default to 1]
 **name** | **str**|  | [optional] 

### Return type

[**GroupIdRecords**](GroupIdRecords.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_keyword**
> view_keyword(orcid, put_code)

Fetch keyword



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch keyword
    api_instance.view_keyword(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_keyword: %s\n" % e)
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

# **view_keywords**
> view_keywords(orcid)

Fetch keywords



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch keywords
    api_instance.view_keywords(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_keywords: %s\n" % e)
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

# **view_other_name**
> view_other_name(orcid, put_code)

Fetch Other name



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch Other name
    api_instance.view_other_name(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_other_name: %s\n" % e)
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

# **view_other_names**
> view_other_names(orcid)

Fetch Other names



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch Other names
    api_instance.view_other_names(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_other_names: %s\n" % e)
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

# **view_peer_review**
> PeerReview view_peer_review(orcid, put_code)

Fetch a Peer Review



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Peer Review
    api_response = api_instance.view_peer_review(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_peer_review: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**PeerReview**](PeerReview.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_review_summary**
> PeerReviewSummary view_peer_review_summary(orcid, put_code)

Fetch a Peer Review Summary



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Peer Review Summary
    api_response = api_instance.view_peer_review_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_peer_review_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**PeerReviewSummary**](PeerReviewSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_peer_reviews**
> PeerReviews view_peer_reviews(orcid)

Fetch all peer reviews



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all peer reviews
    api_response = api_instance.view_peer_reviews(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_peer_reviews: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**PeerReviews**](PeerReviews.md)

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
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_two_legs
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
id = 789 # int | 

try: 
    # Fetch a notification by id
    api_response = api_instance.view_permission_notification(orcid, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_permission_notification: %s\n" % e)
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
> view_person(orcid)

Fetch person details



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch person details
    api_instance.view_person(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_person: %s\n" % e)
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

# **view_personal_details**
> view_personal_details(orcid)

Fetch personal details for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch personal details for an ORCID ID
    api_instance.view_personal_details(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_personal_details: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_record**
> view_record(orcid)

Fetch record details



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch record details
    api_instance.view_record(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_record: %s\n" % e)
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

# **view_researcher_url**
> view_researcher_url(orcid, put_code)

Fetch one researcher url for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch one researcher url for an ORCID ID
    api_instance.view_researcher_url(orcid, put_code)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_researcher_url: %s\n" % e)
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

# **view_researcher_urls**
> view_researcher_urls(orcid)

Fetch all researcher urls for an ORCID ID



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all researcher urls for an ORCID ID
    api_instance.view_researcher_urls(orcid)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_researcher_urls: %s\n" % e)
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
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_specified_works**
> WorkBulk view_specified_works(orcid, put_codes)

Fetch specified works



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_codes = 'put_codes_example' # str | 

try: 
    # Fetch specified works
    api_response = api_instance.view_specified_works(orcid, put_codes)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_specified_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_codes** | **str**|  | 

### Return type

[**WorkBulk**](WorkBulk.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_work**
> Work view_work(orcid, put_code)

Fetch a Work



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Work
    api_response = api_instance.view_work(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_work: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**Work**](Work.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_work_summary**
> WorkSummary view_work_summary(orcid, put_code)

Fetch a Work Summary



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 
put_code = 'put_code_example' # str | 

try: 
    # Fetch a Work Summary
    api_response = api_instance.view_work_summary(orcid, put_code)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_work_summary: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 
 **put_code** | **str**|  | 

### Return type

[**WorkSummary**](WorkSummary.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **view_works**
> Works view_works(orcid)

Fetch all works



### Example 
```python
from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# Configure OAuth2 access token for authorization: orcid_auth
swagger_client.configuration.access_token = 'YOUR_ACCESS_TOKEN'

# create an instance of the API class
api_instance = swagger_client.DevelopmentMemberAPIV30Dev1Api()
orcid = 'orcid_example' # str | 

try: 
    # Fetch all works
    api_response = api_instance.view_works(orcid)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevelopmentMemberAPIV30Dev1Api->view_works: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **orcid** | **str**|  | 

### Return type

[**Works**](Works.md)

### Authorization

[orcid_auth](../README.md#orcid_auth)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/vnd.orcid+xml; qs=5, application/orcid+xml; qs=3, application/xml, application/vnd.orcid+json; qs=4, application/orcid+json; qs=2, application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

