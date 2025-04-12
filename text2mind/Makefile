.PHONY: install test run web clean

install:
	pip install -r requirements.txt
	pip install -e .

test:
	python -m unittest discover tests

run:
	python src/main.py convert examples/example.txt output.png

web:
	python run_web_app.py

clean:
	rm -f *.png
	rm -f *.xmind
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 