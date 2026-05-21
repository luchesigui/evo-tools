.PHONY: start install clean venv

# Define the path to your virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip3

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install -r requirements.txt

start: venv
	$(PYTHON) divide-alunos-e-agregadores.py

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache