import json

import os
import sys
from os.path import join

import requests as requests
from datetime import datetime


def get_tracked_time():
    if os.environ.get('ENV', 'dev') == 'prod':
        data = requests.get(url='https://api.harvestapp.com/api/v2/time_entries', headers={
            'Harvest-Account-ID': os.environ.get('HARVEST_API_ID'),
            'Authorization': f'Bearer {os.environ.get("HARVEST_API_BEARER")}',
            'User-Agent': 'TimeChecker'
        })
        return json.loads(data.content).get('time_entries', [])
    return json.loads(open(join('..', 'data', 'time_entries.json'), 'r+').read())


def parse_work_quota_dates(work_quota_dates):
    if not work_quota_dates:
        print('You must add the date you started to work and you work quota to .env!', file=sys.stderr)
        print('Example: WORK_QUOTA_DATES="2018-09-01;70%,2019-02-01;80%"', file=sys.stderr)
        exit(1)

    parsed_work_quota_dates = {
        parse_iso_date(date_quota.split(';')[0]): float(date_quota.split(';')[1])
        for date_quota in work_quota_dates.split(',')
    }

    return parsed_work_quota_dates


def calculate(time_entries, work_quota_dates):
    i = 0
    work_hours_per_week_quota = float(os.environ.get('WORK_HOURS_PER_WEEK_QUOTA', 42))
    quota_change_dates = sorted(work_quota_dates.keys())
    current_quota_start_date = quota_change_dates[i]
    current_quota = work_quota_dates[current_quota_start_date]

    first_work_day = parse_iso_date(time_entries[0]['spent_date'])
    if first_work_day < current_quota_start_date:
        print(f'You worked on the {to_human_date(first_work_day)} but your earliest provided '
              f'work quota date is: {to_human_date(current_quota_start_date)}', file=sys.stderr)
        exit(1)

    weekly_hours_total = {}
    weekly_hours_delta = {}

    for entry in time_entries:
        work_date = parse_iso_date(entry['spent_date'])

        while i < len(quota_change_dates)-1 and work_date >= quota_change_dates[i+1]:
            i += 1
            current_quota_start_date = quota_change_dates[i]
            current_quota = work_quota_dates[current_quota_start_date]
            print(f'Work day: {to_human_date(work_date)}')
            print(f'Changed quota to {work_quota_dates[current_quota_start_date]}.')
            print()

        calendar_week = work_date.isocalendar()[1]
        week_id = f'Calendarweek[{calendar_week}].Year[{work_date.year}]'
        weekly_hours_total.update({week_id: weekly_hours_total.get(week_id, 0) + entry['hours']})
        weekly_hours_delta[week_id] = work_hours_per_week_quota * current_quota - weekly_hours_total.get(week_id)

    total_hours_worked = sum(weekly_hours_total.values())
    total_hours_average = round(total_hours_worked / len(weekly_hours_total), 2)

    delta_hours = sum(weekly_hours_delta.values())

    compensation_in_days = round(delta_hours / float(os.environ.get('WORK_HOURS_PER_DAY_QUOTA', 8.4)), 2)
    print(f'Current quota: {work_hours_per_week_quota * current_quota}h / week')
    print(f'Average: {total_hours_average}h / week')
    compensation_type = 'Undertime' if delta_hours > 0 else 'Overtime'
    print(f'{compensation_type}: {abs(delta_hours)}h')
    print(f'Compensation: {abs(compensation_in_days)} days')


def parse_iso_date(date):
    return datetime.strptime(date, '%Y-%m-%d')


def to_human_date(date):
    return datetime.strftime(date, '%d.%m.%Y')


if __name__ == '__main__':
    time_entries = sorted(get_tracked_time(), key=lambda e: e['id'])
    calculate(time_entries, parse_work_quota_dates(os.environ.get('WORK_QUOTA_DATES', None)))


