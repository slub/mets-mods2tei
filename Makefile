# Python interpreter. Default: '$(PYTHON)'
PYTHON = python

# BEGIN-EVAL makefile-parser --make-help Makefile

help:
	@echo ""
	@echo "  Targets"
	@echo ""
	@echo "    test      Run all unit tests"
	@echo "    coverage  Run coverage tests"
	@echo ""
	@echo "  Variables"
	@echo ""
	@echo "    PYTHON  Python interpreter. Default: '$(PYTHON)'"

# END-EVAL

#
# Tests
#

.PHONY: test coverage

# Run all unit tests
test:
	$(PYTHON) -m pytest --continue-on-collection-errors $(TESTDIR)

# Run coverage tests
coverage:
	coverage erase
	make test PYTHON="coverage run"
	coverage report
	coverage html
