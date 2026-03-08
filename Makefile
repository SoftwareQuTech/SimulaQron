PYTHON         = python3
PIP            = pip3
EXAMPLES_DIR   = examples
SIMULAQRON_DIR = simulaqron
TEST_DIR       = tests

# IMPORTANT: For running in makefile, we need to use only 1 thread in OMP library
export OMP_NUM_THREADS=1

clean: _delete_pyc _delete_pid _clear_build _reset

_delete_pyc:
	@find . -name '*.pyc' -delete

_delete_pid:
	@find ${SIMULAQRON_DIR} -name '*.pid' -delete

lint:
	@${PYTHON} -m flake8 ${SIMULAQRON_DIR} ${EXAMPLES_DIR} ${TEST_DIR}

test-deps:
	@${PYTHON} -m pip install .\[test\]

requirements python-deps:
	@${PYTHON} -m pip install .

install-optional: install
	@${PYTHON} -m pip install .\[opt\]

tests:
	@${PYTHON} -m pytest -v ${TEST_DIR}/quick

tests_slow:
	@${PYTHON} -m pytest -v ${TEST_DIR}/slow

tests_all:
	@${PYTHON} -m pytest -v --capture=tee-sys ${TEST_DIR}

examples:
	@echo "--- new-sdk examples ---"
	@cd examples/new-sdk/corrRNG && timeout 90 bash run.sh
	@cd examples/new-sdk/extendGHZ && timeout 90 bash run.sh
	@cd examples/new-sdk/teleport && timeout 90 bash run.sh
	@cd examples/new-sdk/classical-client-server && timeout 90 bash run.sh
	@cd examples/new-sdk/template-quantum-local && timeout 90 bash run.sh
	@cd examples/new-sdk/midCircuitLogic && timeout 90 bash run.sh
	@echo "--- nativeMode examples ---"
	@cd examples/nativeMode/corrRNG && timeout 90 bash run.sh
	@cd examples/nativeMode/extendGHZ && timeout 90 bash run.sh
	@cd examples/nativeMode/teleport && timeout 90 bash run.sh
	@cd examples/nativeMode/graphState && timeout 90 bash run.sh
	@echo "All examples passed."

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

.PHONY: clean lint python-deps tests tests_slow tests_all examples full_tests verify build
