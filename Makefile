PYTHON        = python3
PIP           = pip3
QUICK_TESTS   = tests/auto/quick
ALL_TESTS     = tests/auto
CQC_DIR		  = cqc
EXAMPLES_DIR  = examples
GENERAL_DIR   = general
LOCAL_DIR     = local
RUN_DIR       = run
TESTS_DIR     = tests
TOOLBOX_DIR   = toolbox
VIRTNODE_DIR  = virtNode
CLI           = cli

delete_pyc:
	@find . -name '*.pyc' -delete

delete_pid:
	@find ${CLI} -name '*.pid' -delete

clean: delete_pyc delete_pid

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

.PHONY: clean format lint python-deps tests full_tests verify
