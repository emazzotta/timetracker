#!/usr/bin/python

import json

import os
import sys
from os.path import join

import requests as requests
from datetime import datetime, timedelta


def get_tracked_time():
    harvest_api_account_id = os.environ.get('HARVEST_API_ID')
    harvest_api_token = os.environ.get("HARVEST_API_BEARER")

    if not harvest_api_account_id or not harvest_api_token:
        print('You need to provide valid harvest credentials in the .env file!', file=sys.stderr)
        exit(1)

    if os.environ.get('ENV', 'prod') == 'prod':
        headers = {
            'Harvest-Account-ID': harvest_api_account_id,
            'Authorization': f'Bearer {harvest_api_token}',
            'User-Agent': 'TimeChecker'
        }

        page = 1
        data = request_time_entries(page=page, headers=headers)
        entries = data.get('time_entries', [])
        while int(data.get('total_pages')) > page:
            page += 1
            data = request_time_entries(page=page, headers=headers)
            entries = entries + data.get('time_entries', [])

        # open(join('..', 'data', 'time_entries.json'), 'w+').write(json.dumps(entries))
        return entries
    return json.loads(open(join('..', 'data', 'time_entries.json'), 'r+').read())


def parse_work_quota_dates(work_quota_dates):
    if not work_quota_dates:
        print('You must add the date you started to work and you work quota to .env!', file=sys.stderr)
        print('Example: WORK_QUOTA_DATES="2018-09-01:70%;2019-02-01:80%"', file=sys.stderr)
        exit(1)

    try:
        parsed_work_quota_dates = {
            parse_iso_date(date_quota.split(':')[0].strip()): float(date_quota.split(':')[1].strip())
            for date_quota
            in work_quota_dates.strip().strip(';').split(';')
        }
        return parsed_work_quota_dates
    except TypeError:
        print(f'Invalid work quota format: "{work_quota_dates}"')
        exit(1)


def is_business_day(day):
    return day.isoweekday() not in [6, 7]


def calculate(time_entries, work_quota_dates):
    i = 0
    working_day_hours = float(os.environ.get('WORK_DAY_HOURS', 8.4))
    quota_change_dates = sorted(work_quota_dates.keys())
    current_quota_start_date = quota_change_dates[i]
    current_quota = work_quota_dates[current_quota_start_date]

    check_work_quota_exists(current_quota_start_date, time_entries[0])

    hours_should_work = 0

    current_work_day = current_quota_start_date
    working_days_total = 0

    while current_work_day <= datetime.today():

        # Check if work quota is up-to-date
        while i < len(quota_change_dates) - 1 and current_work_day >= quota_change_dates[i + 1]:
            i += 1
            current_quota_start_date = quota_change_dates[i]
            current_quota = work_quota_dates[current_quota_start_date]

        if is_business_day(current_work_day):
            working_days_total += 1
            hours_should_work += working_day_hours * current_quota

        current_work_day += timedelta(days=1)

    time_entries_until_today = [
        time_entry
        for time_entry
        in time_entries
        if parse_iso_date(time_entry['spent_date']) <= datetime.today()
    ]

    hours_should_work = round(hours_should_work, 2)
    hours_did_work = sum([entry['hours'] for entry in time_entries_until_today])
    delta_hours = round(hours_should_work - hours_did_work, 2)
    compensation_in_days = round(delta_hours / working_day_hours, 2)

    print(f'⏱  Your current contract: {working_day_hours * 5 * current_quota}h / week ({current_quota * 100}%)')
    print(f'💰 You sold {int(round(hours_did_work, 0))}h of your time working 🤔')
    compensation_type = '🛑 Undertime' if delta_hours > 0 else '✅ Overtime'
    print(f'{compensation_type}: {abs(delta_hours)}h ({abs(compensation_in_days)} working days)')


def check_work_quota_exists(quota_date, first_work_day_entry):
    first_work_day = parse_iso_date(first_work_day_entry['spent_date'])
    if first_work_day < quota_date:
        print(f'You worked on the {to_human_date(first_work_day)}', file=sys.stderr)
        print(f'But your earliest provided work quota date is: {to_human_date(quota_date)}', file=sys.stderr)
        exit(1)


def parse_iso_date(date):
    return datetime.strptime(date, '%Y-%m-%d')


def to_human_date(date):
    return datetime.strftime(date, '%d.%m.%Y')


def request_time_entries(page=1, headers=None):
    if headers is None:
        headers = {}

    return json.loads(
        requests.get(
            url='https://api.harvestapp.com/api/v2/time_entries',
            params={'page': page},
            headers=headers
        ).content
    )


if __name__ == '__main__':
    calculate(
        get_tracked_time(),
        parse_work_quota_dates(os.environ.get('WORK_QUOTA_DATES', None))
    )
