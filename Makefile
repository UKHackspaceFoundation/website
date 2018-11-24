DOCKER_RUN=docker-compose exec web pipenv run

test: lint
	$(DOCKER_RUN) ./manage.py test

lint:
	pipenv run flake8 ./main

ci: lint
	pipenv run ./manage.py test

shell:
	$(DOCKER_RUN) ./manage.py shell
