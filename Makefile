init:
	pip install -r requirements.txt

isort:
	isort --check-only src

format: isort
	black src

isort-fix:
	isort src
