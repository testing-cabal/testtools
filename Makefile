# Copyright (c) 2008-2013 testtools developers. See LICENSE for details.

PYTHON=python3
SOURCES=$(shell find testtools -name "*.py")

check:
	PYTHONPATH=$(PWD) $(PYTHON) -m testtools.run tests.test_suite

TAGS: ${SOURCES}
	ctags -e -R testtools/

tags: ${SOURCES}
	ctags -R testtools/

clean: clean-sphinx
	rm -f TAGS tags
	find testtools -name "*.pyc" -exec rm '{}' \;

prerelease:
	# An existing MANIFEST breaks distutils sometimes. Avoid that.
	-rm MANIFEST

release:
	hatchling build
	twine upload dist/testtools-$(shell hatchling version)-*
	gpg -a --detach-sign dist/testtools-$(shell hatchling version).tar.gz

snapshot: prerelease
	hatchling build

### Documentation ###

apidocs:
	# pydoctor emits deprecation warnings under Ubuntu 10.10 LTS
	PYTHONWARNINGS='ignore::DeprecationWarning' \
		pydoctor --make-html --add-package testtools \
		--docformat=restructuredtext --project-name=testtools \
		--project-url=https://github.com/testing-cabal/testtools

doc/news.rst:
	ln -s ../NEWS doc/news.rst

docs: doc/news.rst docs-sphinx
	rm doc/news.rst

docs-sphinx: html-sphinx

# Clean out generated documentation
clean-sphinx:
	cd doc && make clean

# Build the html docs using Sphinx.
html-sphinx:
	cd doc && PYTHONPATH=.. make html

.PHONY: apidocs docs-sphinx clean-sphinx html-sphinx docs
.PHONY: check clean prerelease release
