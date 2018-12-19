# Timetracker

Get your time tracking data via Harvest API. 

## Getting started

### Prerequisites

* Docker 18 or later

### Bootstrap

```bash
# Get the code, cd to timetracker, setup timetracker in Docker
git clone git@github.com:emazzotta/timetracker.git && \
    cd timetracker && \
    make bootstrap
```

### Configuration/Authorization

* Get your personal token [here](https://id.getharvest.com/oauth2/access_tokens/new)
* Adapt the .env file with your personal token 

|.env variable name|Use|Default|
|---|---|---|
|HARVEST_API_BEARER|The harvest API Token|None|
|HARVEST_API_ID|The harvest API account ID|None|
|WORK_WEEK_HOURS|Hours in a regular full-time week|42|
|WORK_DAY_HOURS|Hours of a regular full-time day|8.4|
|WORK_QUOTA_DATES|Semicolon separated list of "date":"work quota"-combinations. E.g. the example reads starting from 2018-09-01 you worked 100% and from 2018-11-01 you worked 80%| 2018-09-01:1; 2018-11-01:0.8 |

### Run

```bash
make run
```

## Example Output

### Overtime

```text
Quota: 42.0h / week
Average: 43.14h / week
Overtime: 10.22h (1.22 days)
```

### Undertime

```text
Quota: 42.0h / week
Average: 36.02h / week
Undertime: 53.78h (6.4 days)
```

## Author

[Emanuele Mazzotta](mailto:hello@mazzotta.me)
