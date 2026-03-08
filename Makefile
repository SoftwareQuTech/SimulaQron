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

_example_cleanup:
	@simulaqron stop 2>/dev/null || true
	@sleep 2

examples:
	@echo "--- new-sdk examples ---"
	@cd examples/new-sdk/corrRNG && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@cd examples/new-sdk/extendGHZ && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@cd examples/new-sdk/teleport && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@cd examples/new-sdk/classical-client-server && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@cd examples/new-sdk/template-quantum-local && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@cd examples/new-sdk/midCircuitLogic && timeout 90 bash run.sh
	@$(MAKE) _example_cleanup
	@echo "All new sdk examples passed."

install: test-deps
	@$(PYTHON) -m pip install -e . ${PIP_FLAGS}

_verified:
	@echo "SimulaQron is verified!"

ci: lint tests tests_slow examples
	@echo "All CI checks passed."

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

.PHONY: clean lint python-deps tests tests_slow tests_all examples _example_cleanup ci full_tests verify build
