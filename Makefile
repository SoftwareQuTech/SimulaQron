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
	@rm ${CLI}/*.pid

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

# tests_qutip:
# 	@sh $(RUN_TESTS) --quick --qutip

# tests_projectq:
# 	@sh $(RUN_TESTS) --quick --projectq

# tests_stabilizer:
# 	@sh $(RUN_TESTS) --quick --stabilizer

# full_tests:
# 	@sh $(RUN_TESTS) --full --stabilizer

# full_tests_qutip:
# 	@sh $(RUN_TESTS) --full --qutip

# full_tests_projectq:
# 	@sh $(RUN_TESTS) --full --projectq

# full_tests_stabilizer:
# 	@sh $(RUN_TESTS) --full --stabilizer

# tests_allBackends: tests_qutip tests_projectq tests_stabilizer

# full_tests_allBackends: full_tests_qutip full_tests_projectq full_tests_stabilizer

verify: clean python-deps lint tests

.PHONY: clean format lint python-deps tests full_tests verify
