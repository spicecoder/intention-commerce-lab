.PHONY: demo test-python test-orders test-inventory test real-up real-down e2e-real

demo:
	python3 -m intention_commerce.cli --mode prototype --client scripted --scenario success

test-python:
	python3 -m unittest discover -s tests/python -v

test-orders:
	cd apps/orders-node && npm test

test-inventory:
	cd apps/inventory-spring && ./mvnw test

test: test-python test-orders test-inventory

real-up:
	docker compose up --build -d

real-down:
	docker compose down

e2e-real:
	python3 tests/e2e_real.py
