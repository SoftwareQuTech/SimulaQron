PYTHON        = python3
PIP           = pip3
QUICK_TESTS   = tests/auto/quick
ALL_TESTS     = tests/auto
EXAMPLES_DIR  = examples
GENERAL_DIR   = general
LOCAL_DIR     = local
RUN_DIR       = run
TESTS_DIR     = tests
TOOLBOX_DIR   = toolbox
VIRTNODE_DIR  = virtNode
CLI           = cli

_delete_pyc:
	@find . -name '*.pyc' -delete

_delete_pid:
	@find ${CLI} -name '*.pid' -delete

format:
	black -l 120 .

lint:
	@${PYTHON} -m flake8 ${CQC_DIR} ${EXAMPLES_DIR} ${GENERAL_DIR} ${LOCAL_DIR} ${RUN_DIR} ${TESTS_DIR} ${TOOLBOX_DIR} ${VIRTNODE_DIR}

python-deps:
	@cat requirements.txt | xargs -n 1 -L 1 $(PIP) install

tests:
	@${PYTHON} -m unittest discover -s ${QUICK_TESTS}

tests_all:
	@${PYTHON} -m unittest discover -s ${ALl_TESTS}

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

clean: _delete_pyc _delete_pid _clear_build

_build:
	@${PYTHON} setup.py sdist bdist_wheel

build: _clear_build _build

.PHONY: clean format lint python-deps tests full_tests verify build
