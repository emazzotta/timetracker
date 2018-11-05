import json

import os
import requests as requests
from datetime import datetime

print(f"Getting data with harvest ID '{os.environ.get('HARVEST_API_ID')}'...")

headers = {
    'Harvest-Account-ID': os.environ.get('HARVEST_API_ID'),
    'Authorization': f'Bearer {os.environ.get("HARVEST_API_BEARER")}',
    'User-Agent': 'TimeChecker'
}

data = requests.get(url='https://api.harvestapp.com/api/v2/time_entries', headers=headers)
time_entries = json.loads(data.content).get('time_entries', [])

work_hours_per_week_quota = 42 * 0.7
weekly_hours_total = {}

for entry in time_entries:
    work_date = datetime.strptime(entry['spent_date'], '%Y-%m-%d')
    calendar_week = work_date.isocalendar()[1]
    key = f'Calendarweek[{calendar_week}].Year[{work_date.year}]'
    weekly_hours_total.update({key: weekly_hours_total.get(key, 0) + entry['hours']})

total_hours_worked = sum(weekly_hours_total.values())
total_hours_should_have_worked = len(weekly_hours_total) * work_hours_per_week_quota
delta_hours = round(total_hours_should_have_worked - total_hours_worked, 2)

compensation_in_days = round(delta_hours/8.4, 2)

if delta_hours > 0:
    print(f'Hours undertime: {delta_hours}')
    print(f'Compensation in days: {compensation_in_days}')
else:
    print(f'Hours overtime: {abs(delta_hours)}')
