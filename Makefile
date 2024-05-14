PYTHON_MODULE=geonetpy

PYTHON_BIN=python3

TESTS_DIR=test
TESTS_UNIT_DIR=$(TESTS_DIR)/unit

PYTEST_MODULE=unittest
PYTEST_PARAMS=discover -b -v -s $(TESTS_UNIT_DIR)

PYLINT_BIN ?= pylint

FLAKE8_BIN ?= flake8

.PHONY: run_pylint
run_pylint:
	$(PYLINT_BIN) $(PYTHON_MODULE)

.PHONY: run_flake8
run_flake8:
	$(FLAKE8_BIN) $(PYTHON_MODULE)

.PHONY: lint
lint: run_pylint run_flake8
	@ echo "*** Linters done ***"

.PHONY: test
test:
	$(PYTHON_BIN) -m $(PYTEST_MODULE) $(PYTEST_PARAMS)
