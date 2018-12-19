PYTHON        = python
PIP           = pip
RUN_TESTS     = tests/runTests.sh
CQC_DIR		  = cqc
EXAMPLES_DIR  = examples
GENERAL_DIR   = general
LOCAL_DIR     = local
RUN_DIR       = run
TESTS_DIR     = tests
TOOLBOX_DIR   = toolbox
VIRTNODE_DIR  = virtNode

clean:
	@find . -name '*.pyc' -delete

format:
	black -l 120 .

lint:
	@${PYTHON} -m flake8 ${CQC_DIR} ${EXAMPLES_DIR} ${GENERAL_DIR} ${LOCAL_DIR} ${RUN_DIR} ${TESTS_DIR} ${TOOLBOX_DIR} ${VIRTNODE_DIR}

python-deps:
	@cat requirements.txt | xargs -n 1 -L 1 $(PIP) install

tests:
	@sh $(RUN_TESTS) --quick --projectq

tests_qutip:
	@sh $(RUN_TESTS) --quick --qutip

tests_projectq:
	@sh $(RUN_TESTS) --quick --projectq

tests_stabilizer:
	@sh $(RUN_TESTS) --quick --stabilizer

full_tests:
	@sh $(RUN_TESTS) --full --projectq

full_tests_qutip:
	@sh $(RUN_TESTS) --full --qutip

full_tests_projectq:
	@sh $(RUN_TESTS) --full --projectq

full_tests_stabilizer:
	@sh $(RUN_TESTS) --full --stabilizer

tests_allBackends: tests_qutip tests_projectq tests_stabilizer

full_tests_allBackends: full_tests_qutip full_tests_projectq full_tests_stabilizer

verify: clean lint python-deps tests

.PHONY: clean format lint python-deps tests full_tests verify
