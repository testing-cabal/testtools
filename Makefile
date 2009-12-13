# See README for copyright and licensing details.

PYTHON=python
SOURCES=$(shell find testtools -name "*.py")

check:
	PYTHONPATH=$(PWD) $(PYTHON) -m testtools.run testtools.tests.test_suite

TAGS: ${SOURCES}
	ctags -e -R testtools/

tags: ${SOURCES}
	ctags -R testtools/

clean:
	rm -f TAGS tags
	find testtools -name "*.pyc" -exec rm '{}' \;

release:
	./setup.py sdist upload --sign

.PHONY: check clean
