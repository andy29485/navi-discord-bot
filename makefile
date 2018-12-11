PYTHON36 := $(shell python3.7 --version 2> /dev/null)

ifdef PYTHON37
	PYTHON=python3.7
else
	PYTHON3 := $(shell python3 --version 2> /dev/null)
	ifdef PYTHON3
		PYTHON=python3
	else
		PYTHON=python
	endif
endif

test:
	$(PYTHON) -t -m py_compile ./start.py
	$(PYTHON) -t -m py_compile cogs/*py
	$(PYTHON) -t -m py_compile includes/*py
	$(PYTHON) -t -m py_compile includes/utils/*py
	$(PYTHON) -W ignore -m unittest discover -s tests/

clean:
	rm -rf __pycache__/
