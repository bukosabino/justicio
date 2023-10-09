init:
	pip install -r requirements.txt

isort:
	isort --check-only src evaluation

format: isort
	black src evaluation

isort-fix:
	isort src evaluation
