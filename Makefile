# See README for copyright and licensing details.

check:
	./run-tests

TAGS:
	ctags -e -R testtools/

tags:
	ctags -R testtools/

clean:
	rm -f TAGS tags testtools/*.pyc testtools/tests/*.pyc

release:
	./setup.py sdist upload --sign

.PHONY: tags TAGS check clean
