PYTHON        = python
PIP           = pip
RUN_TESTS     = tests/runTests.sh


clean:
	@find . -name '*.pyc' -delete

python-deps:
	@$(PIP) install -r requirements.txt

tests:
	@sh $(RUN_TESTS) --quick

full_tests:
	@sh $(RUN_TESTS) --full

verify: clean python-deps tests

.PHONY: clean python-deps tests full_tests verify
