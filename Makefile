# Makefile

.PHONY: venv install test run

venv:
	python3 -m venv venv
	source venv/bin/activate

install:
	pip3 install -r requirements.txt

test:
	PYTHONWARNINGS=ignore python3 -m unittest discover -s ./tests -v

testImage:
	PYTHONWARNINGS=ignore python3 -m unittest ./tests/testImage.py -v
run:
	python3 main.py