This is the website for www.hackspace.org.uk.

This is a Python 3 project, so make sure you have a python 3
interpreter.

To run (it will use a sqlite database in dev):

    $ pip3 install -r ./requirements.txt
    $ python3 ./manage.py migrate
    $ python3 ./manage.py runserver

Then you should be able to connect to http://localhost:8000.
