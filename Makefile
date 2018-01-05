all: init test

init:
	python setup.py develop
	pip install detox coverage mkdocs

test:
	coverage erase
	detox
	coverage html
