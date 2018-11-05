# Timetracker

Get your time tracking data via Harvest API. 

## Getting started

### Authorization

* Get your personal token [here](https://id.getharvest.com/oauth2/access_tokens/new)
* Add you token to the .env file
```bash
touch .env
echo "HARVEST_API_BEARER=<TOKEN>" >> .env
echo "HARVEST_API_ID=<ACCOUNT_ID>" >> .env
```
### Configuration

```bash
# Set your work week hours quota
# Default is 42 hours
echo "WORK_HOURS_PER_WEEK_QUOTA=42" >> .env

# Set your work day hours quota
# Default is 8.4 hours
echo "WORK_HOURS_PER_DAY_QUOTA=8.4" >> .env
```

### Run

```bash
docker-compose up -d
```

## Example Output

```text
# If you have overtime
Quota: 42.0h / week
Average: 43.14h / week
Overtime: 10.22h
Compensation: 1.22 days

# If you have undertime
Quota: 42.0h / week
Average: 36.02h / week
Undertime: 53.78h
Compensation: 6.4 days
```

## Author

[Emanuele Mazzotta](mailto:hello@mazzotta.me)
