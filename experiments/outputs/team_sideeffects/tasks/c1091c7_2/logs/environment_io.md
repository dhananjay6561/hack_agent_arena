
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
TOKEN:venmo:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2ZW5tbytjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3MDQ0fQ.d14WQW-Fh4R1S3k-Kjy2IrC_MM7S9RTNNQuplo7RoUY
TOKEN:splitwise:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcGxpdHdpc2UrY2UtbWFsZG9uYWRvQGdtYWlsLmNvbSIsImV4cCI6MTY4NDc0NzY4N30.N4PWoessPhCiruNCPC0V4d-SWWi7FaMTEAqZZlsJnyU
TOKEN:spotify:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzcG90aWZ5K2NlLW1hbGRvbmFkb0BnbWFpbC5jb20iLCJleHAiOjE2ODQ3NDc2Nzd9.3gFP41rTJ8V9qeL9ibGbAYIpwmCfK7ZpJ0xyPWxeW5k
TOKEN:gmail:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3MTAzfQ.wveZFlNqiUz2OwoLcHiJSML4Vnt8fWcwjRAXqy-otIE
TOKEN:amazon:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbWF6b24rY2UtbWFsZG9uYWRvQGdtYWlsLmNvbSIsImV4cCI6MTY4NDc0NzU1MH0.gukembN0vKo0ySerTYY2z8mK8N4jhtduD7fdCLjI6Q4
TOKEN:simple_note:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzaW1wbGVfbm90ZStjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3NDYyfQ.Ltgo6AZXd9nx9Rmo1YwM_Dsb8LGeyAef0svBhwrdYhM
TOKEN:todoist:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0b2RvaXN0K2NlLW1hbGRvbmFkb0BnbWFpbC5jb20iLCJleHAiOjE2ODQ3NDc2MzN9._4-iLwxSE0cPDKPUMZIdGAdQ0DTFTPouH76pZl1UxkM
TOKEN:file_system:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmaWxlX3N5c3RlbStjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3Nzg0fQ.xuvm9Uvq361Ax7WLDa73RrBHCEDRVvWBsrAj6LP3roE
TOKEN:phone:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSszOTQ3MzI0MjM1IiwiZXhwIjoxNjg0NzQ2OTcxfQ.kW5nish-B7YIe6I4IIQpVfxAu3zEioZm9dwfiAFjmKg
```


### Environment Interaction 2
----------------------------------------------------------------------------
```python
gmail_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3MTAzfQ.wveZFlNqiUz2OwoLcHiJSML4Vnt8fWcwjRAXqy-otIE'
phone_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSszOTQ3MzI0MjM1IiwiZXhwIjoxNjg0NzQ2OTcxfQ.kW5nish-B7YIe6I4IIQpVfxAu3zEioZm9dwfiAFjmKg'

# Get the list of emails from coworkers
emails = apis.gmail.show_inbox_threads(access_token=gmail_token, query='subject:(meeting cancellation)')

# Get the list of alarms on the phone
alarms = apis.phone.show_alarms(access_token=phone_token)

# Print the results
print(emails)
print(alarms)
```

```
[
 {
  "email_thread_id": 47833,
  "email_ids": [
   20875,
   20876
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": true,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-22T09:29:14",
  "updated_at": "2023-05-22T09:29:14",
  "subject": "Reunion Cancelation",
  "participants": [
   {
    "name": "Alex White",
    "email": "alexwhite@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 47823,
  "email_ids": [
   20868
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": false,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-21T18:23:44",
  "updated_at": "2023-05-21T18:23:44",
  "subject": "Cancel Meeting?",
  "participants": [
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   },
   {
    "name": "Catherine Smith",
    "email": "ca-smit@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 10244,
  "email_ids": [
   3158
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": false,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-15T15:01:38",
  "updated_at": "2023-05-15T15:01:38",
  "subject": "Book Club Reminder",
  "participants": [
   {
    "name": "Chris Mccoy",
    "email": "chris.mcco@gmail.com"
   },
   {
    "name": "Martin Blackburn",
    "email": "mar_blac@gmail.com"
   },
   {
    "name": "Kevin Blackburn",
    "email": "kevin.blac@gmail.com"
   },
   {
    "name": "Joseph Weber",
    "email": "joseph.webe@gmail.com"
   },
   {
    "name": "Lindsey Simpson",
    "email": "lindseysimpson@gmail.com"
   },
   {
    "name": "Cory Wilson",
    "email": "corwils@gmail.com"
   },
   {
    "name": "Melissa Bailey",
    "email": "mel.bailey@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   },
   {
    "name": "Carl Brown",
    "email": "carbrown@gmail.com"
   },
   {
    "name": "Andrew Brown",
    "email": "andrew_brow@gmail.com"
   },
   {
    "name": "Cody Smith",
    "email": "cod.smith@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 12816,
  "email_ids": [
   3987,
   3988
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": true,
  "read": true,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2022-06-15T17:05:11",
  "updated_at": "2022-06-15T17:05:11",
  "subject": "Travel Memories",
  "participants": [
   {
    "name": "Kathryn Maldonado",
    "email": "kathrynmaldonado@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 12818,
  "email_ids": [
   3989,
   3990
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": true,
  "read": true,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2022-08-24T08:21:37",
  "updated_at": "2022-08-24T08:21:37",
  "subject": "Childhood Photos",
  "participants": [
   {
    "name": "Kathryn Maldonado",
    "email": "kathrynmaldonado@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 }
]
[
 {
  "alarm_id": 603,
  "time": "08:30",
  "repeat_days": [
   "monday",
   "tuesday",
   "wednesday",
   "thursday",
   "friday"
  ],
  "label": "Wake Up",
  "enabled": true,
  "snooze_minutes": 10,
  "vibration": true,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 747,
  "time": "09:00",
  "repeat_days": [
   "tuesday"
  ],
  "label": "One-on-One with Christopher",
  "enabled": true,
  "snooze_minutes": 15,
  "vibration": true,
  "created_at": "2023-05-08T09:32:45",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 604,
  "time": "09:30",
  "repeat_days": [
   "saturday",
   "sunday"
  ],
  "label": "Wake Up",
  "enabled": true,
  "snooze_minutes": 10,
  "vibration": true,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 749,
  "time": "09:30",
  "repeat_days": [
   "tuesday"
  ],
  "label": "One-on-One with Thomas",
  "enabled": true,
  "snooze_minutes": 15,
  "vibration": true,
  "created_at": "2023-05-09T08:20:32",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 606,
  "time": "10:30",
  "repeat_days": [
   "monday"
  ],
  "label": "Weekly Work Standup Meeting",
  "enabled": true,
  "snooze_minutes": 0,
  "vibration": true,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 }
]
```


### Environment Interaction 3
----------------------------------------------------------------------------
```python
gmail_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3MTAzfQ.wveZFlNqiUz2OwoLcHiJSML4Vnt8fWcwjRAXqy-otIE'
phone_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSszOTQ3MzI0MjM1IiwiZXhwIjoxNjg0NzQ2OTcxfQ.kW5nish-B7YIe6I4IIQpVfxAu3zEioZm9dwfiAFjmKg'

# Filter the email threads to only include those with a subject containing 'cancel' or 'cancellation'
canceled_meetings = [thread for thread in emails if 'cancel' in thread['subject'].lower() or 'cancellation' in thread['subject'].lower()]

# Get the labels of the alarms that correspond to the canceled meetings
canceled_alarm_labels = []
for meeting in canceled_meetings:
    for participant in meeting['participants']:
        if participant['email'] == 'ce-maldonado@gmail.com':
            alarm_label = f"One-on-One with {meeting['participants'][0]['name']}"
            canceled_alarm_labels.append(alarm_label)

# Disable the corresponding alarms
for alarm in alarms:
    if alarm['label'] in canceled_alarm_labels:
        apis.phone.disable_alarm(access_token=phone_token, alarm_id=alarm['alarm_id'])

# Print the results
print(canceled_meetings)
print(canceled_alarm_labels)
```

```
[
 {
  "email_thread_id": 47833,
  "email_ids": [
   20875,
   20876
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": true,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-22T09:29:14",
  "updated_at": "2023-05-22T09:29:14",
  "subject": "Reunion Cancelation",
  "participants": [
   {
    "name": "Alex White",
    "email": "alexwhite@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 47823,
  "email_ids": [
   20868
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": false,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-21T18:23:44",
  "updated_at": "2023-05-21T18:23:44",
  "subject": "Cancel Meeting?",
  "participants": [
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   },
   {
    "name": "Catherine Smith",
    "email": "ca-smit@gmail.com"
   }
  ]
 }
]
["One-on-One with Alex White", "One-on-One with Cesar Maldonado"]
```


### Environment Interaction 4
----------------------------------------------------------------------------
```python
gmail_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnbWFpbCtjZS1tYWxkb25hZG9AZ21haWwuY29tIiwiZXhwIjoxNjg0NzQ3MTAzfQ.wveZFlNqiUz2OwoLcHiJSML4Vnt8fWcwjRAXqy-otIE'
phone_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwaG9uZSszOTQ3MzI0MjM1IiwiZXhwIjoxNjg0NzQ2OTcxfQ.kW5nish-B7YIe6I4IIQpVfxAu3zEioZm9dwfiAFjmKg'

# Filter the email threads to only include those with a subject containing 'cancel' or 'cancellation'
canceled_meetings = [
 {
  "email_thread_id": 47833,
  "email_ids": [
   20875,
   20876
  ],
  "draft_ids": [],
  "incoming": True,
  "outgoing": True,
  "read": False,
  "label": None,
  "starred": False,
  "archived": False,
  "spam": False,
  "created_at": "2023-05-22T09:29:14",
  "updated_at": "2023-05-22T09:29:14",
  "subject": "Reunion Cancelation",
  "participants": [
   {
    "name": "Alex White",
    "email": "alexwhite@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 47823,
  "email_ids": [
   20868
  ],
  "draft_ids": [],
  "incoming": True,
  "outgoing": False,
  "read": False,
  "label": None,
  "starred": False,
  "archived": False,
  "spam": False,
  "created_at": "2023-05-21T18:23:44",
  "updated_at": "2023-05-21T18:23:44",
  "subject": "Cancel Meeting?",
  "participants": [
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   },
   {
    "name": "Catherine Smith",
    "email": "ca-smit@gmail.com"
   }
  ]
 }
]

alarms = [
 {
  "alarm_id": 603,
  "time": "08:30",
  "repeat_days": [
   "monday",
   "tuesday",
   "wednesday",
   "thursday",
   "friday"
  ],
  "label": "Wake Up",
  "enabled": True,
  "snooze_minutes": 10,
  "vibration": True,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 747,
  "time": "09:00",
  "repeat_days": [
   "tuesday"
  ],
  "label": "One-on-One with Christopher",
  "enabled": True,
  "snooze_minutes": 15,
  "vibration": True,
  "created_at": "2023-05-08T09:32:45",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 604,
  "time": "09:30",
  "repeat_days": [
   "saturday",
   "sunday"
  ],
  "label": "Wake Up",
  "enabled": True,
  "snooze_minutes": 10,
  "vibration": True,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 749,
  "time": "09:30",
  "repeat_days": [
   "tuesday"
  ],
  "label": "One-on-One with Thomas",
  "enabled": True,
  "snooze_minutes": 15,
  "vibration": True,
  "created_at": "2023-05-09T08:20:32",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 },
 {
  "alarm_id": 606,
  "time": "10:30",
  "repeat_days": [
   "monday"
  ],
  "label": "Weekly Work Standup Meeting",
  "enabled": True,
  "snooze_minutes": 0,
  "vibration": True,
  "created_at": "2023-05-18T12:00:00",
  "user": {
   "name": "Cesar Maldonado",
   "phone_number": "3947324235"
  }
 }
]

# Get the labels of the alarms that correspond to the canceled meetings
canceled_alarm_labels = []
for meeting in canceled_meetings:
    for participant in meeting['participants']:
        if participant['email'] != 'ce-maldonado@gmail.com':
            alarm_label = f"One-on-One with {participant['name']}"
            canceled_alarm_labels.append(alarm_label)

# Disable the corresponding alarms
for alarm in alarms:
    if alarm['label'] in canceled_alarm_labels:
        apis.phone.disable_alarm(access_token=phone_token, alarm_id=alarm['alarm_id'])

# Print the results
print(canceled_meetings)
print(canceled_alarm_labels)

# Complete the task
apis.supervisor.complete_task(answer="One-on-One with Alex White, One-on-One with Catherine Smith")
```

```
[
 {
  "email_thread_id": 47833,
  "email_ids": [
   20875,
   20876
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": true,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-22T09:29:14",
  "updated_at": "2023-05-22T09:29:14",
  "subject": "Reunion Cancelation",
  "participants": [
   {
    "name": "Alex White",
    "email": "alexwhite@gmail.com"
   },
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   }
  ]
 },
 {
  "email_thread_id": 47823,
  "email_ids": [
   20868
  ],
  "draft_ids": [],
  "incoming": true,
  "outgoing": false,
  "read": false,
  "label": null,
  "starred": false,
  "archived": false,
  "spam": false,
  "created_at": "2023-05-21T18:23:44",
  "updated_at": "2023-05-21T18:23:44",
  "subject": "Cancel Meeting?",
  "participants": [
   {
    "name": "Cesar Maldonado",
    "email": "ce-maldonado@gmail.com"
   },
   {
    "name": "Catherine Smith",
    "email": "ca-smit@gmail.com"
   }
  ]
 }
]
["One-on-One with Alex White", "One-on-One with Catherine Smith"]
```

