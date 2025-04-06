# Makefile

.PHONY: venv install test run

venv:
	python3 -m venv venv

venvActivate:
	source venv/bin/activate

all: 
	pip3 install -r requirements.txt
	python3 main.py

install:
	pip3 install -r requirements.txt

test:
	PYTHONWARNINGS=ignore python3 -m unittest discover -s ./tests -v

testImage:
	PYTHONWARNINGS=ignore python3 -m unittest ./tests/testImage.py -v

testImagePath:
	PYTHONWARNINGS=ignore python -m unittest discover -s ./tests -p "testImage.py" -k "test_calculate_path_success"

testImageUpload:
	PYTHONWARNINGS=ignore python -m unittest discover -s ./tests -p "testImage.py" -k "test_upload_real_image_success"

testEBImageUpload:
	PYTHONWARNINGS=ignore python -m unittest discover -s ./tests -p "testImage.py" -k "test_upload_eb_real_image_success"

testImageGet:
	PYTHONWARNINGS=ignore python -m unittest discover -s ./tests -p "testImage.py" -k "test_get_image_with_anchors_2"

testBuilding:
	PYTHONWARNINGS=ignore python3 -m unittest ./tests/testBuilding.py -v

testGunicorn:
	gunicorn main:app

run:
	python3 main.py