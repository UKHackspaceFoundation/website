run: init
	./ENV/bin/python ./manage.py runserver

test:
	./ENV/bin/flake8 ./main

init: ENV/requirements.built
	./ENV/bin/python ./manage.py migrate

ENV/requirements.built: ENV requirements.txt
	./ENV/bin/pip install -r ./requirements.txt && cp ./requirements.txt ./ENV/requirements.built

ENV:
	virtualenv -p python3 ./ENV
