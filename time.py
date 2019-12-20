from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import sys
import csv

import dateparser

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def main():
    creds = get_creds()

    my_events = get_events(creds, 'primary')

    try:
        arg = sys.argv[1]
    except:
        arg = 0

    if arg == 'ot':
        print_ot(my_events)
        return

    else:
        print('---------------------')

        total = datetime.timedelta(0)

        my_time, ot = get_my_time(creds, arg)
        freelance = get_freelancer_time(creds, arg)

        print(f'{arg.upper()} {get_job_number(arg)}:')
        print('me', delta_hours(my_time), f'({delta_hours(ot)} OT)')
        total += my_time

        for freelancer, time in freelance.items():
            total += time
            print(freelancer, delta_hours(time))

        print(f'TOTAL: {delta_hours(total)}')

        print('---------------------')
        return

def get_my_time(creds, project):
    events = get_events(creds, 'primary')
    total = datetime.timedelta(0)
    ot = datetime.timedelta(0)
    for event in events:
        title = str(event['summary'])
        if not project == title:
            continue

        total += duration(event)

        color_id = event.get('colorId')
        if color_id == '1':
            ot += duration(event)

    return total, ot


def get_freelancer_time(creds, project):
    freelancer_time = {}
    cal_id = get_freelancer_cal_id()
    if not cal_id:
        return None

    events = get_events(creds, cal_id)

    for event in events:
        name = str(event['summary']).lower().strip()
        event_project = str(event.get('description')).lower().strip()
        if event_project == project:
            add_time_to_key(freelancer_time, name, duration(event))

    return freelancer_time

def get_events(credentials, calendar_id):
    service = build('calendar', 'v3', credentials=credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    events_result = service.events().list(
        calendarId=calendar_id,
        singleEvents=True,
        orderBy='startTime',
        timeMax=now).execute()

    events = events_result.get('items', [])
    return events

def get_freelancer_cal_id():
    try:
        with open('freelancer_cal_id.txt', 'r') as infile:
            return infile.read().strip()

    except:
        return None

def add_time_to_key(dictionary, key, time_delta):
    if not key in dictionary.keys():
        dictionary[key] = time_delta
    else:
        dictionary[key] += time_delta

def print_ot(events):
    print('FLETCHER OT')
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

        dur = duration(event)
        total_ot += dur

        end = dateparser.parse(str(event['end'].get('dateTime')))
        title = event.get('summary')
        job_number = get_job_number(title)
        print(
            start.strftime("%a %m-%d"),
            f'[{title} {job_number}]',
            dur
            )

    print(f'Total: {sec_to_hour(total_ot.total_seconds())}')

def get_job_number(project_title):
    job_number = '000000'
    with open('job_numbers.csv', 'r') as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if project_title == row[0]:
                job_number = row[1]

    return job_number

def duration(event):
    start = dateparser.parse(str(event['start'].get('dateTime')))
    end = dateparser.parse(str(event['end'].get('dateTime')))
    if not start or not end:
        return datetime.timedelta(0)
    return end - start

def delta_hours(time_delta):
    return sec_to_hour(time_delta.total_seconds())

def sec_to_hour(sec):
    return sec / (60 * 60)

def get_creds():
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
    return creds


if __name__ == '__main__':
    main()
