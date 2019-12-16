from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import sys

import dateparser

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    print('Talking to Google Calendar...')
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    '''events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()'''
    
    events_result = service.events().list(calendarId='primary', singleEvents=True,
                                        orderBy='startTime', timeMax=now).execute()
    events = events_result.get('items', [])

    if not events:
        print('No events.')

    try:
        arg = sys.argv[1]
    except:
        arg = 0

    if arg == 'ot':
        print_ot(events)
        return

    else:
        print_project_duration(arg, events)
        return

def print_project_duration(project_name, events):
    projects = {}
    for event in events:
        title = str(event['summary'])
        if project_name and not project_name == title:
            continue

        if not title in projects.keys():
            projects[title] = duration(event)
        else:
            projects[title] += duration(event)
            
    for project, dur in projects.items():
        print(project, dur.total_seconds() / (60 * 60), 'hours')

def print_ot(events):
    print('OT')
    now = datetime.datetime.now()
    total_ot = datetime.timedelta(0)
    for event in events:
        color_id = event.get('colorId')
        if not color_id == '1':
            continue

        start = dateparser.parse(str(event['start'].get('dateTime')))
        start_naive = start.replace(tzinfo = None)
        if (now - start_naive).days > 7:
            continue

        total_ot += duration(event)
        
        end = dateparser.parse(str(event['end'].get('dateTime')))
        title = event.get('summary')
        print(
            start.strftime("%Y-%m-%d"),
            title,
            start.strftime("%H:%M"),
            end.strftime("%H:%M")
            )

    print(f'Total: {sec_to_hour(total_ot.total_seconds())}')

def duration(event):
    start = dateparser.parse(str(event['start'].get('dateTime')))
    end = dateparser.parse(str(event['end'].get('dateTime')))
    if not start or not end:
        return datetime.timedelta(0)
    return end - start

def sec_to_hour(sec):
    return sec / (60 * 60)
    

if __name__ == '__main__':
    main()
