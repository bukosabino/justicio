init:
	pip install -r requirements.txt

isort:
	isort --check-only src evaluation

format: isort
	black --line-length=120 src evaluation

isort-fix:
	isort src evaluation
