#!/usr/bin/python
import calendar
import json
import os
import sys
import datetime
from os.path import join

import requests as requests


salary_day_of_month = int(os.environ.get('SALARY_DAY_OF_MONTH'))
harvest_api_account_id = os.environ.get('HARVEST_API_ID')
harvest_api_token = os.environ.get("HARVEST_API_BEARER")


def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day, )


def get_days_until_salary():
    return (get_next_salary_date() - datetime.date.today()).days


def get_next_salary_date():
    current_date = datetime.date.today()

    if current_date.day < salary_day_of_month:
        salary_date = current_date + datetime.timedelta(days=(salary_day_of_month - current_date.day))
    else:
        salary_date = add_months(current_date, 1) - datetime.timedelta(days=(current_date.day - salary_day_of_month))

    salary_date_weekday = salary_date.isoweekday()

    # If salary date is on Saturday, salary is due on Friday
    # If salary date is on Sunday, salary is due on Monday
    if salary_date_weekday == 6:
        return salary_date - datetime.timedelta(days=1)
    elif salary_date_weekday == 7:
        return salary_date + datetime.timedelta(days=1)
    else:
        return salary_date


def get_tracked_time():
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

        # write current data into json file
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
    work_quota_index = 0
    working_day_hours = float(os.environ.get('WORK_DAY_HOURS', 8.4))
    quota_change_dates = sorted(work_quota_dates.keys())
    current_quota_start_date = quota_change_dates[work_quota_index]
    current_quota = work_quota_dates[current_quota_start_date]

    check_work_quota_exists(current_quota_start_date, time_entries[-1])

    seconds_should_work = 0

    current_work_day = current_quota_start_date
    working_days_total = 0

    while current_work_day <= datetime.datetime.today():

        # Check if work quota is up-to-date
        while work_quota_index < len(quota_change_dates) - 1 and current_work_day >= quota_change_dates[work_quota_index + 1]:
            work_quota_index += 1
            current_quota_start_date = quota_change_dates[work_quota_index]
            current_quota = work_quota_dates[current_quota_start_date]

        if is_business_day(current_work_day):
            working_days_total += 1
            seconds_should_work += working_day_hours * 3600 * current_quota

        current_work_day += datetime.timedelta(days=1)

    time_entries_until_today = [
        time_entry
        for time_entry
        in time_entries
        if parse_iso_date(time_entry['spent_date']) <= datetime.datetime.today()
    ]

    seconds_did_work = sum([entry['hours'] for entry in time_entries_until_today]) * 3600
    delta_seconds = seconds_should_work - seconds_did_work
    delta_hours = round(delta_seconds / 3600, 2)
    compensation_in_days = round(delta_hours / working_day_hours, 2)
    days_until_salary = get_days_until_salary()

    print(f'⏱  Your current contract: {working_day_hours * 5 * current_quota}h / week ({current_quota * 100}%)')
    print(f'💰 You sold {int(round(seconds_did_work / 3600, 0))}h of your time working at your current job 🤔')
    compensation_type = '🛑 Undertime' if delta_hours > 0 else '✅ Overtime'
    print(f'{compensation_type}: {abs(delta_hours)}h ({abs(compensation_in_days)} working days)')
    print(f'💸 {days_until_salary} day{"s" if days_until_salary != 1 else ""} until next salary {get_next_salary_date().strftime("%d.%m.%Y")}')


def check_work_quota_exists(earliest_quota_date, first_work_day_entry):
    first_work_day = parse_iso_date(first_work_day_entry['spent_date'])
    if first_work_day < earliest_quota_date:
        print(f'You worked on the {to_human_date(first_work_day)}', file=sys.stderr)
        print(f'But your earliest provided work quota date is: {to_human_date(earliest_quota_date)}', file=sys.stderr)
        exit(1)


def parse_iso_date(date):
    return datetime.datetime.strptime(date, '%Y-%m-%d')


def to_human_date(date):
    return datetime.datetime.strftime(date, '%d.%m.%Y')


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
