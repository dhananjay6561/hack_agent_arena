
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
TOKEN:venmo:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZW5tbytkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY0NTF9.XqZZpnwDjeu86j8FhTaZRkQbT-KOEhanfp2alataZPo
TOKEN:splitwise:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcGxpdHdpc2UrZGF2Lm1hcnRAZ21haWwuY29tIiwiZXhwIjoxNjg0Njc3MDk0fQ.sUSddUniYfSxx3elCtEMKaCmq-edhnjlSZqIQ1kacms
TOKEN:spotify:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG90aWZ5K2Rhdi5tYXJ0QGdtYWlsLmNvbSIsImV4cCI6MTY4NDY3NzA4NH0.cSMj0ZHzloBrU7QG04L_DYjs-muvhTe6guWAIm0N4YM
TOKEN:gmail:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY1MTB9.zEpcGvLNblDu0RmeyuonCKjQHRCbuZN3nM3T3plybfA
TOKEN:amazon:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWF6b24rZGF2Lm1hcnRAZ21haWwuY29tIiwiZXhwIjoxNjg0Njc2OTU3fQ.P8at4rilpGB9cJSRhBjz9k42mHHoz1-trq_XcfNm7h4
TOKEN:simple_note:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaW1wbGVfbm90ZStkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY4Njl9.tL6swzWrIxNJ3C3Wn1FIjIwv72k-PvdOdFT1APp1xGs
TOKEN:todoist:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2RvaXN0K2Rhdi5tYXJ0QGdtYWlsLmNvbSIsImV4cCI6MTY4NDY3NzA0MH0.5tIzZFwhAmLaNEV7HXYZKABb-Ya7o7_DBsszTl62dyc
TOKEN:file_system:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaWxlX3N5c3RlbStkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzcxOTF9.jW6IuZjXP101akPaq-EQTlpWAm_WoVdx4vWVWxPKnaY
TOKEN:phone:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSs3MjI4Nzk2OTkzIiwiZXhwIjoxNjg0Njc2Mzc4fQ.FDwxlLpETXmC6v1p64SEAXt_FyGrYicl66NNxJT5RxI
```


### Environment Interaction 2
----------------------------------------------------------------------------
```python
venmo_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZW5tbytkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY0NTF9.XqZZpnwDjeu86j8FhTaZRkQbT-KOEhanfp2alataZPo'
splitwise_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcGxpdHdpc2UrZGF2Lm1hcnRAZ21haWwuY29tIiwiZXhwIjoxNjg0Njc3MDk0fQ.sUSddUniYfSxx3elCtEMKaCmq-edhnjlSZqIQ1kacms'
spotify_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG90aWZ5K2Rhdi5tYXJ0QGdtYWlsLmNvbSIsImV4cCI6MTY4NDY3NzA4NH0.cSMj0ZHzloBrU7QG04L_DYjs-muvhTe6guWAIm0N4YM'
gmail_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY1MTB9.zEpcGvLNblDu0RmeyuonCKjQHRCbuZN3nM3T3plybfA'
amazon_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWF6b24rZGF2Lm1hcnRAZ21haWwuY29tIiwiZXhwIjoxNjg0Njc2OTU3fQ.P8at4rilpGB9cJSRhBjz9k42mHHoz1-trq_XcfNm7h4'
simple_note_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaW1wbGVfbm90ZStkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzY4Njl9.tL6swzWrIxNJ3C3Wn1FIjIwv72k-PvdOdFT1APp1xGs'
todoist_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2RvaXN0K2Rhdi5tYXJ0QGdtYWlsLmNvbSIsImV4cCI6MTY4NDY3NzA0MH0.5tIzZFwhAmLaNEV7HXYZKABb-Ya7o7_DBsszTl62dyc'
file_system_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaWxlX3N5c3RlbStkYXYubWFydEBnbWFpbC5jb20iLCJleHAiOjE2ODQ2NzcxOTF9.jW6IuZjXP101akPaq-EQTlpWAm_WoVdx4vWVWxPKnaY'
phone_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSs3MjI4Nzk2OTkzIiwiZXhwIjoxNjg0Njc2Mzc4fQ.FDwxlLpETXmC6v1p64SEAXt_FyGrYicl66NNxJT5RxI'
```

```
Execution successful.
```


### Environment Interaction 3
----------------------------------------------------------------------------
```python
# Get the notes from SimpleNote
notes = apis.simple_note.search_notes(access_token=simple_note_token)

# Filter notes to find the meeting schedule note
meeting_schedule_note = None
for note in notes:
    if 'meeting schedule' in note['content'].lower():
        meeting_schedule_note = note
        break

# If meeting schedule note is found, parse its content to extract meeting information
if meeting_schedule_note:
    meetings = []
    lines = meeting_schedule_note['content'].split('\n')
    for line in lines:
        if 'meeting' in line.lower():
            parts = line.split(',')
            meeting_name = parts[0].split(':')[1].strip()
            meeting_time = parts[1].strip()
            participants = parts[2].strip().split(';')
            meetings.append({
                'name': meeting_name,
                'time': meeting_time,
                'participants': participants
            })

    # Get the user's email address from Gmail
    user_email = apis.gmail.show_account(access_token=gmail_token)['email']

    # Schedule reminder emails for each meeting
    for meeting in meetings:
        # Get the participants' email addresses from Gmail
        participant_emails = []
        for participant in meeting['participants']:
            if participant != user_email:
                contact = apis.gmail.search_users(access_token=gmail_token, query=participant)
                if contact:
                    participant_emails.append(contact[0]['email'])

        # Schedule a reminder email 20 minutes before the meeting
        if participant_emails:
            meeting_time_parts = meeting['time'].split(' ')
            meeting_date = meeting_time_parts[0]
            meeting_hour, meeting_minute = map(int, meeting_time_parts[1].split(':'))
            reminder_time = f"{meeting_date} {meeting_hour-0:02d}:{meeting_minute-20:02d}:00"
            subject = f"Meeting '{meeting['name']}' Starting Soon"
            body = ""
            apis.gmail.send_email(access_token=gmail_token, to=participant_emails, subject=subject, body=body, send_at=reminder_time)

# Complete the task
apis.supervisor.complete_task(answer=None)
```

```
Execution failed. Traceback:
  File "<python-input>", line 7, in <module>
    if 'meeting schedule' in note['content'].lower():
                             ~~~~^^^^^^^^^^^
KeyError: 'content'
```


### Environment Interaction 4
----------------------------------------------------------------------------
```python
# Check the API documentation for the search_notes endpoint
print(apis.api_docs.show_api_doc(app_name='simple_note', api_name='search_notes'))
print(apis.api_docs.show_api_doc(app_name='simple_note', api_name='show_note'))

# Get the notes from SimpleNote
notes = apis.simple_note.search_notes(access_token=simple_note_token)

# Filter notes to find the meeting schedule note
meeting_schedule_note = None
for note in notes:
    note_id = note['id']
    note_content = apis.simple_note.show_note(access_token=simple_note_token, note_id=note_id)
    if 'meeting schedule' in note_content['content'].lower():
        meeting_schedule_note = note_content
        break

# If meeting schedule note is found, parse its content to extract meeting information
if meeting_schedule_note:
    meetings = []
    lines = meeting_schedule_note['content'].split('\n')
    for line in lines:
        if 'meeting' in line.lower():
            parts = line.split(',')
            meeting_name = parts[0].split(':')[1].strip()
            meeting_time = parts[1].strip()
            participants = parts[2].strip().split(';')
            meetings.append({
                'name': meeting_name,
                'time': meeting_time,
                'participants': participants
            })

    # Get the user's email address from Gmail
    user_email = apis.gmail.show_account(access_token=gmail_token)['email']

    # Schedule reminder emails for each meeting
    for meeting in meetings:
        # Get the participants' email addresses from Gmail
        participant_emails = []
        for participant in meeting['participants']:
            if participant!= user_email:
                contact = apis.gmail.search_users(access_token=gmail_token, query=participant)
                if contact:
                    participant_emails.append(contact[0]['email'])

        # Schedule a reminder email 20 minutes before the meeting
        if participant_emails:
            meeting_time_parts = meeting['time'].split(' ')
            meeting_date = meeting_time_parts[0]
            meeting_hour, meeting_minute = map(int, meeting_time_parts[1].split(':'))
            reminder_time = f"{meeting_date} {meeting_hour:02d}:{meeting_minute-20:02d}:00"
            subject = f"Meeting '{meeting['name']}' Starting Soon"
            body = ""
            apis.gmail.send_email(access_token=gmail_token, to=participant_emails, subject=subject, body=body, send_at=reminder_time)

# Complete the task
apis.supervisor.complete_task(answer=None)
```

```
Execution failed. Traceback:
  File "<python-input>", line 11, in <module>
    note_id = note['id']
              ~~~~^^^^^^
KeyError: 'id'
```


### Environment Interaction 5
----------------------------------------------------------------------------
```python
# Check the API documentation for the search_notes endpoint
print(apis.api_docs.show_api_doc(app_name='simple_note', api_name='search_notes'))
print(apis.api_docs.show_api_doc(app_name='simple_note', api_name='show_note'))

# Get the notes from SimpleNote
notes = apis.simple_note.search_notes(access_token=simple_note_token)

# Filter notes to find the meeting schedule note
meeting_schedule_note = None
for note in notes:
    print(apis.api_docs.show_api_doc(app_name='simple_note', api_name='show_note'))
    note_id = note.get('note_id') or note.get('id')
    if note_id:
        note_content = apis.simple_note.show_note(access_token=simple_note_token, note_id=note_id)
        if 'meeting schedule' in note_content.get('content', '').lower():
            meeting_schedule_note = note_content
            break

# If meeting schedule note is found, parse its content to extract meeting information
if meeting_schedule_note:
    meetings = []
    lines = meeting_schedule_note.get('content', '').split('\n')
    for line in lines:
        if 'meeting' in line.lower():
            parts = line.split(',')
            meeting_name = parts[0].split(':')[1].strip() if len(parts) > 0 and ':' in parts[0] else ''
            meeting_time = parts[1].strip() if len(parts) > 1 else ''
            participants = parts[2].strip().split(';') if len(parts) > 2 else []
            meetings.append({
                'name': meeting_name,
                'time': meeting_time,
                'participants': participants
            })

    # Get the user's email address from Gmail
    user_email = apis.gmail.show_account(access_token=gmail_token)['email']

    # Schedule reminder emails for each meeting
    for meeting in meetings:
        # Get the participants' email addresses from Gmail
        participant_emails = []
        for participant in meeting['participants']:
            if participant!= user_email:
                contact = apis.gmail.search_users(access_token=gmail_token, query=participant)
                if contact:
                    participant_emails.append(contact[0].get('email'))

        # Schedule a reminder email 20 minutes before the meeting
        if participant_emails:
            meeting_time_parts = meeting['time'].split(' ')
            meeting_date = meeting_time_parts[0]
            meeting_hour, meeting_minute = map(int, meeting_time_parts[1].split(':')) if len(meeting_time_parts) > 1 and ':' in meeting_time_parts[1] else (0, 0)
            reminder_time = f"{meeting_date} {meeting_hour:02d}:{meeting_minute-20:02d}:00" if meeting_minute >= 20 else f"{meeting_date} {meeting_hour-1:02d}:{60+meeting_minute-20:02d}:00"
            subject = f"Meeting '{meeting['name']}' Starting Soon"
            body = ""
            apis.gmail.send_email(access_token=gmail_token, to=participant_emails, subject=subject, body=body, send_at=reminder_time)

# Complete the task
apis.supervisor.complete_task(answer=None)
```

```
{
 "app_name": "simple_note",
 "api_name": "search_notes",
 "path": "/notes",
 "method": "GET",
 "description": "Search your notes. This will not show contents of the notes. Pinned notes will be shown first by default, except when dont_reorder_pinned is true.",
 "parameters": [
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  },
  {
   "name": "query",
   "type": "string",
   "required": false,
   "description": "Search query for the notes.",
   "default": "",
   "constraints": []
  },
  {
   "name": "tags",
   "type": "list[string]",
   "required": false,
   "description": "Tags to filter the notes by. Notes not having any of these tags will be filtered out.",
   "default": null,
   "constraints": []
  },
  {
   "name": "pinned",
   "type": "boolean",
   "required": false,
   "description": "Filter notes by pinned status.",
   "default": null,
   "constraints": []
  },
  {
   "name": "dont_reorder_pinned",
   "type": "boolean",
   "required": false,
   "description": "If true, pinned notes will not be reordered to be shown at the top.",
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
   "description": "The attribute to sort the notes by prefixed with +/- to reflect ascending/descending. Valid attributes: created_at and updated_at. If both query and sort_by are given and non-empty, results will be first ranked by query relevance, then paginated, and will then be sorted by the given attribute within each page. If both query and sort_by are not given, null, or empty, sort_by will default to -updated_at.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": [
   {
    "note_id": 1,
    "title": "string",
    "tags": [
     "string"
    ],
    "created_at": "2019-01-01T00:00:00",
    "updated_at": "2019-01-01T00:00:00",
    "pinned": true
   }
  ],
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
{
 "app_name": "simple_note",
 "api_name": "show_note",
 "path": "/notes/{note_id}",
 "method": "GET",
 "description": "Show detailed information of a note, including its content.",
 "parameters": [
  {
   "name": "note_id",
   "type": "integer",
   "required": true,
   "description": "ID of the note to be shown.",
   "default": null,
   "constraints": []
  },
  {
   "name": "access_token",
   "type": "string",
   "required": true,
   "description": "Access token obtained from simple_note app login.",
   "default": null,
   "constraints": []
  }
 ],
 "response_schemas": {
  "success": {
   "note_id": 1,
   "title": "string",
   "content": "string",
   "tags": [
    "string"
   ],
   "created_at": "2019-01-01T00:00:00",
   "updated_at": "2019-01-01T00:00:00",
   "pinned": true
  },
  "failure": {
   "message": "string"
  }
 }
}
```

