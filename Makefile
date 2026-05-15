PYTHON         = python3
PIP            = pip3
EXAMPLES_DIR   = examples
SIMULAQRON_DIR = simulaqron
TEST_DIR       = tests

# We use the Gitlab repo to look for already-compiled versions os projectq and qutip
GITLAB_REPO=$(shell curl --write-out '%{http_code}' --silent --output /dev/null https://gitlab.tudelft.nl/api/v4/projects/28442/packages/pypi/simple)

# IMPORTANT: For running in makefile, we need to use only 1 thread in OMP library
export OMP_NUM_THREADS=1

clean: _delete_pyc _delete_pid _clear_build _reset

_delete_pyc:
	@find . -name '*.pyc' -delete

_delete_pid:
	@find ${SIMULAQRON_DIR} -name '*.pid' -delete

_install_projectq_qutip:
	@if [ "${GITLAB_REPO}" = "200" ]; then \
    	${PYTHON} -m pip install projectq qutip --index-url https://gitlab.tudelft.nl/api/v4/projects/28442/packages/pypi/simple; \
    else \
		${PYTHON} -m pip install "setuptools<81" pybind11; \
		${PYTHON} -m pip install "git+https://github.com/ProjectQ-Framework/ProjectQ.git@v0.8.0" --no-build-isolation; \
		${PYTHON} -m pip install "qutip<5.0.0" --no-build-isolation \
    fi

lint-deps:
	@${PYTHON} -m pip install .\[lint\]

lint:
	@${PYTHON} -m flake8 ${SIMULAQRON_DIR} ${EXAMPLES_DIR} ${TEST_DIR}

test-deps: _install_projectq_qutip
	@${PYTHON} -m pip install .\[test\]

requirements python-deps:
	@${PYTHON} -m pip install .

dev-deps:
	@${PYTHON} -m pip install .\[dev\]

install-development: dev-deps

install-optional: _install_projectq_qutip
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
	@cd examples/new-sdk/corrRNG && bash terminate.sh && sleep 3
	@cd examples/new-sdk/extendGHZ && timeout 90 bash run.sh
	@cd examples/new-sdk/extendGHZ && bash terminate.sh && sleep 3
	@cd examples/new-sdk/teleport && timeout 90 bash run.sh
	@cd examples/new-sdk/teleport && bash terminate.sh && sleep 3
	@cd examples/new-sdk/midCircuitLogic && timeout 90 bash run.sh
	@cd examples/new-sdk/midCircuitLogic && bash terminate.sh && sleep 3
	@cd examples/native-mode/teleport && bash terminate.sh && sleep 3
	@echo "Chosen examples passed."

install:
	@$(PYTHON) -m pip install . ${PIP_FLAGS}

install-dev: install-optional
	@${PYTHON} -m pip install -e .\[test,dev\]

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
	@${PYTHON} -m build --sdist --wheel --outdir dist/ .

build: _clear_build _build

.PHONY: clean lint python-deps tests tests_slow tests_all examples ci full_tests verify build
