test_case = '' # Run all tests by default; otherwise run user specified test
.PHONY: dev fmt install lint migrations test fmt-ci lint-ci build install-dev load-test

build: ;

dev:
	API_AUTH_TOKEN=123 uvicorn main:app --reload --host 0.0.0.0 --port 8000

fmt:
	black . $(ARGS)

install:
	pip3 install --user -r requirements.txt

install-dev:
	pip3 install --user -r requirements_dev.txt
	
lint:
	flake8 .

lint-ci:
	flake8 .

load-test:
	locust

migrations:
	cd db_migrations &&\
	alembic upgrade head

test:
	API_AUTH_TOKEN=e184bd87-feac-4582-8ec8-dc63557faa68 OPENAPI_URL="" AWS_LOCALSTACK="" AV_DEFINITION_PATH=/tmp/clamav CI=True coverage run -m pytest -k $(test_case) -s -vv tests &&\
	coverage report -m

fmt-ci:
	black --check .