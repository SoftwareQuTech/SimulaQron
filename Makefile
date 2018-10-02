PYTHON        = python
PIP           = pip
RUN_TESTS     = tests/runTests.sh


clean:
	@find . -name '*.pyc' -delete

python-deps:
	@$(PIP) install -r requirements.txt

tests:
	@sh $(RUN_TESTS)

verify: clean python-deps tests

.PHONY: clean python-deps tests verify
