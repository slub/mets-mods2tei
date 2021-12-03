# Python interpreter. Default: '$(PYTHON)'
PYTHON ?= python
PIP ?= pip

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    install   Install this package"
	@echo "    deps      Install dependencies only"
	@echo "    deps-test Install dependencies for testing only"
	@echo "    test      Run all unit tests"
	@echo "    coverage  Run coverage tests"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    PYTHON  Python interpreter. Default: '$(PYTHON)'"
	@echo "    PIP     Python packager. Default: '$(PIP)'"

# END-EVAL

#
# Tests
#

.PHONY: install test coverage deps deps-test

install:
	$(PIP) install .

deps:
	$(PIP) install -r requirements.txt

deps-test:
	$(PIP) install -r requirements-test.txt

# Run all unit tests
test:
	$(PYTHON) -m pytest --continue-on-collection-errors $(TESTDIR)

# Run coverage tests
coverage:
	coverage erase
	make test PYTHON="coverage run"
	coverage report
	coverage html
