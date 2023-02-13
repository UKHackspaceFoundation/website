DOCKER_RUN=docker-compose exec web poetry run

test: lint
	$(DOCKER_RUN) ./manage.py test

lint:
	poetry run flake8 ./main

ci: lint
	poetry run ./manage.py test

shell:
	$(DOCKER_RUN) ./manage.py shell

deploy:
	docker build . -f ./Dockerfile.prod -t ukhackspacefoundation/website:latest
	docker push ukhackspacefoundation/website:latest
