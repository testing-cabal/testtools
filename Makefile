# Copyright (c) 2008-2013 testtools developers. See LICENSE for details.

PYTHON=python
SOURCES=$(shell find testtools -name "*.py")

SRC_REPO=github.com/testing-cabal/testtools
SRC_EGGNAME=testtools
SRC_PYPINAME=${SRC_EGGNAME}
PIP_SRC_URL='git+ssh://git@${SRC_REPO}\#egg=${SRC_EGGNAME}'

default: check

check:
	PYTHONPATH=$(PWD) $(PYTHON) -m testtools.run testtools.tests.test_suite

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
	./setup.py sdist bdist_wheel upload --sign
	$(PYTHON) scripts/_lp_release.py

snapshot: prerelease
	./setup.py sdist bdist_wheel

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
	cd doc && make html

# Overwrite gh-pages branch with the contents of doc/_build/html,
# add a .nojekyll file, and git push to origin:gh-pages
gh-pages:
	ghp-import -n -p ./doc/_build/html

### Installation ###

# Install from pypi
install-from-pypi:
	# pip install testtools
	pip install ${SRC_PYPINAME}

install-from-warehouse:
	pip install -i https://warehouse.python.org/project/ ${SRC_PYPINAME}

# Install from github
install-from-github:
	pip install -v --find-links=https://${SRC_REPO}/releases ${SRC_PYPINAME}

# Install from src
install-from-src:
	pip install -e ${PIP_SRC_URL}

# Install requirements with pip
install-pip-requirements:
	pip install -r ./requirements.txt

# Install dev/doc requirements with pip
install-dev: install-pip-requirements
	pip install -r ./requirements-dev.txt
	pip install -e .


.PHONY: default check clean prerelease release
.PHONY: apidocs docs-sphinx clean-sphinx html-sphinx docs
.PHONY: gh-pages
.PHONY: install-from-pypi install-from-warehouse install-from-github \
		install-from-src
.PHONY: install-pip-requirements install-dev
