# See README for copyright and licensing details.

check:
	./run-tests

TAGS:
	ctags -e -R pyunit3k/

tags:
	ctags -R pyunit3k/

clean:
	rm -f TAGS tags pyunit3k/*.pyc pyunit3k/tests/*.pyc


.PHONY: tags TAGS check clean
