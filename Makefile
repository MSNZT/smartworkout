.PHONY: db-up db-down start

db-up:
	docker compose up -d

db-down:
	docker compose down

start: db-up
	python3 ./main.py
