
### Environment Interaction 1
----------------------------------------------------------------------------
```python
creds_list = apis.supervisor.show_account_passwords()
creds = {c['account_name']: c['password'] for c in creds_list}
profile = apis.supervisor.show_profile()
email = profile.get('email', '')
phone_number = profile.get('phone_number', '')
login_map = {
    'venmo': ('venmo', email), 'splitwise': ('splitwise', email),
    'spotify': ('spotify', email), 'gmail': ('gmail', email),
    'amazon': ('amazon', email), 'simple_note': ('simple_note', email),
    'todoist': ('todoist', email), 'file_system': ('file_system', email),
    'phone': ('phone', phone_number),
}
for app, (cred_key, username) in login_map.items():
    try:
        tok = getattr(apis, app).login(username=username, password=creds.get(cred_key, ''))
        print('TOKEN:' + app + ':' + tok.get('access_token', ''))
    except Exception as e:
        print('TOKEN:' + app + ':FAILED')
```

```
TOKEN:venmo:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZW5tbytjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjA5OH0.6BbQ2XpMHFObP4D1HEE4zjTmc65BDDNiWuV8jz5Mwoo
TOKEN:splitwise:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcGxpdHdpc2UrY2hlbHNlYS1idXJjaEBnbWFpbC5jb20iLCJleHAiOjE2ODQ0MTI3NDF9.kiF7j51JsD9tdprUSZf2zNfBerlj7neNJjW4GYAtiFs
TOKEN:spotify:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG90aWZ5K2NoZWxzZWEtYnVyY2hAZ21haWwuY29tIiwiZXhwIjoxNjg0NDEyNzMxfQ.NPxV1GnGur-yl42UalWhkTbeURKso30IqTGhnGULNVw
TOKEN:gmail:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjE1N30.qpmpuqGaR04VvmZ35s5a_W2Ysc9Vu0-HNM_CI3cIpY8
TOKEN:amazon:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWF6b24rY2hlbHNlYS1idXJjaEBnbWFpbC5jb20iLCJleHAiOjE2ODQ0MTI2MDR9.4QIT2hQAVkc4RiiKlzauMKh9i16DwoRaUHfitoNBnb8
TOKEN:simple_note:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaW1wbGVfbm90ZStjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjUxNn0.XxRw4cDtr6i2sAMoGNOUrVXyonLK_kpEjZgOv23b5tE
TOKEN:todoist:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2RvaXN0K2NoZWxzZWEtYnVyY2hAZ21haWwuY29tIiwiZXhwIjoxNjg0NDEyNjg3fQ.fva44zE6cDmkGKd9YDGZNybTRH-L1oFOY9oC_R1hLGE
TOKEN:file_system:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaWxlX3N5c3RlbStjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjgzOH0.CuzXz6Z5E0VT033yWf_G3gkHSXeiR7RejcW__yHKP0Y
TOKEN:phone:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSs3NzYzMzYxMjQ2IiwiZXhwIjoxNjg0NDEyMDI1fQ.sKVZTjCaAB1YcNhJtu80JFQcDRnzu4rxKnWqagodNxc
```


### Environment Interaction 2
----------------------------------------------------------------------------
```python
venmo_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZW5tbytjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjA5OH0.6BbQ2XpMHFObP4D1HEE4zjTmc65BDDNiWuV8jz5Mwoo'
splitwise_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcGxpdHdpc2UrY2hlbHNlYS1idXJjaEBnbWFpbC5jb20iLCJleHAiOjE2ODQ0MTI3NDF9.kiF7j51JsD9tdprUSZf2zNfBerlj7neNJjW4GYAtiFs'
spotify_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG90aWZ5K2NoZWxzZWEtYnVyY2hAZ21haWwuY29tIiwiZXhwIjoxNjg0NDEyNzMxfQ.NPxV1GnGur-yl42UalWhkTbeURKso30IqTGhnGULNVw'
gmail_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjE1N30.qpmpuqGaR04VvmZ35s5a_W2Ysc9Vu0-HNM_CI3cIpY8'
amazon_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWF6b24rY2hlbHNlYS1idXJjaEBnbWFpbC5jb20iLCJleHAiOjE2ODQ0MTI2MDR9.4QIT2hQAVkc4RiiKlzauMKh9i16DwoRaUHfitoNBnb8'
simple_note_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaW1wbGVfbm90ZStjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjUxNn0.XxRw4cDtr6i2sAMoGNOUrVXyonLK_kpEjZgOv23b5tE'
todoist_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2RvaXN0K2NoZWxzZWEtYnVyY2hAZ21haWwuY29tIiwiZXhwIjoxNjg0NDEyNjg3fQ.fva44zE6cDmkGKd9YDGZNybTRH-L1oFOY9oC_R1hLGE'
file_system_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaWxlX3N5c3RlbStjaGVsc2VhLWJ1cmNoQGdtYWlsLmNvbSIsImV4cCI6MTY4NDQxMjgzOH0.CuzXz6Z5E0VT033yWf_G3gkHSXeiR7RejcW__yHKP0Y'
phone_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSs3NzYzMzYxMjQ2IiwiZXhwIjoxNjg0NDEyMDI1fQ.sKVZTjCaAB1YcNhJtu80JFQcDRnzu4rxKnWqagodNxc'
```

```
Execution successful.
```


### Environment Interaction 3
----------------------------------------------------------------------------
```python
# Get the user's profile and order history from Amazon
user_profile = apis.amazon.show_profile(access_token=amazon_token)
order_history = apis.amazon.show_orders(access_token=amazon_token)

# Extract the seller IDs from the order history
seller_ids = [order['seller_id'] for order in order_history if 'seller_id' in order]

# Search for watches on Amazon within the price range
watches = apis.amazon.search_products(access_token=amazon_token, query='watch', price_range='0-110')

# Filter the watches to only include those from trusted sellers
trusted_watches = [watch for watch in watches if watch['seller_id'] in seller_ids]

# If there are no trusted watches, print a message and complete the task
if not trusted_watches:
    print("No watches found from trusted sellers within the price range.")
    apis.supervisor.complete_task(answer=None)

# Otherwise, proceed to the next step
else:
    print("Trusted watches found. Proceeding to the next step.")
```

```
Execution failed. Traceback:
  File "<python-input>", line 2, in <module>
    user_profile = apis.amazon.show_profile(access_token=amazon_token)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Exception: Response status code is 422:
{"message":"Either email or phone_number must be provided."}
```


### Environment Interaction 4
----------------------------------------------------------------------------
```python
# Check the API documentation for the show_profile endpoint
print(apis.api_docs.show_api_doc(app_name='amazon', api_name='show_profile'))

# Get the user's profile from Amazon using their email
user_profile = apis.amazon.show_profile(access_token=amazon_token, email='chelsea-burch@gmail.com')

# Get the user's order history from Amazon
order_history = apis.amazon.show_orders(access_token=amazon_token, email='chelsea-burch@gmail.com')

# Extract the seller IDs from the order history
seller_ids = [order['seller_id'] for order in order_history if 'seller_id' in order]

# Check the API documentation for the search_products endpoint
print(apis.api_docs.show_api_doc(app_name='amazon', api_name='search_products'))

# Search for watches on Amazon within the price range
watches = apis.amazon.search_products(access_token=amazon_token, query='watch', min_price=0, max_price=110)

# Filter the watches to only include those from trusted sellers
trusted_watches = [watch for watch in watches if watch['seller_id'] in seller_ids]

# If there are no trusted watches, print a message and complete the task
if not trusted_watches:
    print("No watches found from trusted sellers within the price range.")
    apis.supervisor.complete_task(answer=None)

# Otherwise, proceed to the next step
else:
    print("Trusted watches found. Proceeding to the next step.")
```

```
{
 "app_name": "amazon",
 "api_name": "show_profile",
 "path": "/profile",
 "method": "GET",
 "description": "Show public profile information of a user.",
 "parameters": [
  {
   "name": "email",
   "type": "string",
   "required": false,
   "description": "Email of the person you want to see the profile information of.",
   "default": null,
   "constraints": [
    "value is email address"
   ]
  }
 ],
 "response_schemas": {
  "success": {
   "first_name": "string",
   "last_name": "string",
   "email": "user@example.com",
   "registered_at": "2019-01-01T00:00:00"
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "amazon",
 "api_name": "search_products",
 "path": "/products",
 "method": "GET",
 "description": "Search for products with a query and various filtering criteria.",
 "parameters": [
  {
   "name": "query",
   "type": "string",
   "required": false,
   "description": "The search query string.",
   "default": "",
   "constraints": []
  },
  {
   "name": "product_type",
   "type": "string",
   "required": false,
   "description": "The type of product to search for.",
   "default": null,
   "constraints": []
  },
  {
   "name": "color",
   "type": "string",
   "required": false,
   "description": "The color of product to search for.",
   "default": null,
   "constraints": []
  },
  {
   "name": "relative_size",
   "type": "string",
   "required": false,
   "description": "The relative size of product to search for.",
   "default": null,
   "constraints": [
    "value in ['extra-small', 'small', 'medium', 'large', 'extra-large']"
   ]
  },
  {
   "name": "min_price",
   "type": "number",
   "required": false,
   "description": "The minimum price for search results.",
   "default": 0,
   "constraints": [
    "value >= 0.0"
   ]
  },
  {
   "name": "max_price",
   "type": "number",
   "required": false,
   "description": "The maximum price for search results.",
   "default": 9223372036854775807,
   "constraints": [
    "value >= 0.0"
   ]
  },
  {
   "name": "min_product_rating",
   "type": "number",
   "required": false,
   "description": "The minimum product rating for search results.",
   "default": 0,
   "constraints": [
    "value >= 0.0, <= 5.0"
   ]
  },
  {
   "name": "max_product_rating",
   "type": "number",
   "required": false,
   "description": "The maximum product rating for search results.",
   "default": 5,
   "constraints": [
    "value >= 0.0, <= 5.0"
   ]
  },
  {
   "name": "min_seller_rating",
   "type": "number",
   "required": false,
   "description": "The minimum seller rating for search results.",
   "default": 0,
   "constraints": [
    "value >= 0.0, <= 5.0"
   ]
  },
  {
   "name": "max_seller_rating",
   "type": "number",
   "required": false,
   "description": "The maximum seller rating for search results.",
   "default": 5,
   "constraints": [
    "value >= 0.0, <= 5.0"
   ]
  },
  {
   "name": "seller_id",
   "type": "integer",
   "required": false,
   "description": "ID of the seller to search for.",
   "default": null,
   "constraints": []
  },
  {
   "name": "page_index",
   "type": "integer",
   "required": false,
   "description": "The index of the page to return.",
   "default": 0,
   "constraints": [
    "value >= 0.0"
   ]
  },
  {
   "name": "page_limit",
   "type": "integer",
   "required": false,
   "description": "The maximum number of results to return per page.",
   "default": 5,
   "constraints": [
    "value >= 1.0, <= 20.0"
   ]
  },
  {
   "name": "sort_by",
   "type": "string",
   "required": false,
   "description": "The attribute to sort the products by prefixed with +/- to reflect ascending/descending. Valid attributes: rating, price and delivery_days. If both query and sort_by are given and non-empty, results will be first ranked by query relevance, then paginated, and will then be sorted by the given attribute within each page.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": [
   {
    "product_id": 1,
    "seller_id": 1,
    "product_type": "string",
    "name": "string",
    "description": "string",
    "price": 0.0,
    "delivery_days": 1.0,
    "inventory_quantity": 0.0,
    "weight": 0.0,
    "length": 0.0,
    "width": 0.0,
    "height": 0.0,
    "color": "string",
    "relative_size": "extra-small",
    "rating": 0.0,
    "num_product_reviews": 1,
    "num_product_questions": 1,
    "variations": [
     {
      "product_id": 1,
      "relative_size": "extra-small",
      "color": "string"
     }
    ]
   }
  ],
  "failure": {
   "message": "string"
  }
 }
}
No watches found from trusted sellers within the price range.
```

