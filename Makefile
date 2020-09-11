PYTHON         = python3
PIP            = pip3
EXAMPLES_DIR   = examples
SIMULAQRON_DIR = simulaqron
RESET_FILE     = ${SIMULAQRON_DIR}/toolbox/reset.py

clean: _delete_pyc _delete_pid _clear_build _reset

_delete_pyc:
	@find . -name '*.pyc' -delete

_delete_pid:
	@find ${SIMULAQRON_DIR} -name '*.pid' -delete

lint:
	@${PYTHON} -m flake8 ${SIMULAQRON_DIR} ${EXAMPLES_DIR}

test-deps:
	@${PYTHON} -m pip install -r test_requirements.txt

requirements python-deps:
	@cat requirements.txt | xargs -n 1 -L 1 $(PIP) install

_reset:
	@${PYTHON} ${RESET_FILE}

_tests:
	@${PYTHON} ${SIMULAQRON_DIR}/tests_run.py --quick

tests: _tests _reset

_tests_all:
	@${PYTHON} ${SIMULAQRON_DIR}/tests_run.py --full

tests_all: _tests_all _reset

install: test-deps
	@$(PYTHON) -m pip install -e . ${PIP_FLAGS}

_verified:
	@echo "SimulaQron is verified!"

verify: clean python-deps lint tests _verified

_remove_build:
	@rm -f -r build

_remove_dist:
	@rm -f -r dist

_remove_egg_info:
	@rm -f -r simulaqron.egg-info

_clear_build: _remove_build _remove_dist _remove_egg_info

_build:
	@${PYTHON} setup.py sdist bdist_wheel

build: _clear_build _build

.PHONY: clean lint python-deps tests full_tests verify build
