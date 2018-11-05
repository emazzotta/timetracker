import json

import os
import requests as requests
from datetime import datetime

headers = {
    'Harvest-Account-ID': os.environ.get('HARVEST_API_ID'),
    'Authorization': f'Bearer {os.environ.get("HARVEST_API_BEARER")}',
    'User-Agent': 'TimeChecker'
}

data = requests.get(url='https://api.harvestapp.com/api/v2/time_entries', headers=headers)
time_entries = json.loads(data.content).get('time_entries', [])

work_hours_per_week_quota = float(os.environ.get('WORK_HOURS_PER_WEEK_QUOTA'))
weekly_hours_total = {}

for entry in time_entries:
    work_date = datetime.strptime(entry['spent_date'], '%Y-%m-%d')
    calendar_week = work_date.isocalendar()[1]
    week_id = f'Calendarweek[{calendar_week}].Year[{work_date.year}]'
    weekly_hours_total.update({week_id: weekly_hours_total.get(week_id, 0) + entry['hours']})

total_hours_worked = sum(weekly_hours_total.values())
total_hours_average = round(total_hours_worked / len(weekly_hours_total), 2)
total_hours_should_have_worked = len(weekly_hours_total) * work_hours_per_week_quota
delta_hours = round(total_hours_should_have_worked - total_hours_worked, 2)

compensation_in_days = round(delta_hours / 8.4, 2)

print(f'Quota: {work_hours_per_week_quota}h / week')
print(f'Average: {total_hours_average}h / week')
if delta_hours > 0:
    print(f'Undertime: {delta_hours}h')
    print(f'Compensation: {compensation_in_days} days')
else:
    print(f'Overtime: {abs(delta_hours)}h')
