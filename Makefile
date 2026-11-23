.PHONY: install lint test up load watch e2e down

install:
	cd worker && pip install -r requirements-dev.txt

lint:
	cd worker && ruff check . && ruff format --check .

test:
	cd worker && pytest

up:
	bash scripts/kind-up.sh

load:
	bash scripts/load-test.sh

watch:
	bash scripts/watch-scaling.sh

e2e:
	bash scripts/e2e-test.sh

down:
	kind delete cluster --name keda-demo
