# Timetracker build file.
#
# All commands necessary to go from development to release candidate should be here.

ROOT_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))

# -----------------------------------------------------------------------------
# BUILD
# -----------------------------------------------------------------------------
.PHONY: all
all: build

.PHONY: build
build:
	@docker build --file Dockerfile -t emazzotta/timetracker .

.PHONY: run
run:
	@docker run --rm --env-file=.env emazzotta/timetracker

# -----------------------------------------------------------------------------
# DEVELOPMENT
# -----------------------------------------------------------------------------
.PHONY: bootstrap
bootstrap: build copy_env

.PHONY: copy_env
copy_env:
	@cp .env.example .env

.PHONY: restart
restart: stop start

.PHONY: start
start:
	@docker-compose up -d 

.PHONY: stop
stop:
	@docker-compose kill 

.PHONY: force_build
force_build:
	@docker-compose build --force-rm --no-cache --pull

.PHONY: clean
clean:
	@rm -rf .cache
	@rm -rf target
	@rm -f .coverage
	@find . -iname __pycache__ | xargs rm -rf
	@find . -iname "*.pyc" | xargs rm -f
