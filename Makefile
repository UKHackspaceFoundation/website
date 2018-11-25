DOCKER_RUN=docker-compose exec web pipenv run

test: lint
	$(DOCKER_RUN) ./manage.py test

lint:
	pipenv run flake8 ./main

ci: lint
	pipenv run ./manage.py test

shell:
	$(DOCKER_RUN) ./manage.py shell

deploy:
	echo "$(DOCKER_PASSWORD)" | docker login -u "$(DOCKER_USERNAME)" --password-stdin
	docker build . -f ./Dockerfile.prod -t ukhackspacefoundation/website:latest
	docker push ukhackspacefoundation/website:latest
