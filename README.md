This is the website for www.hackspace.org.uk.

This is a Python 3 project, so make sure you have a python 3
interpreter installed.

To configure: Copy the hsf/local_settings.py.example to
hsf/local_settings.py and edit as necessary. Don't forget to check if
the example has updated on pulling new changes.

You will need a GoCardless sandbox account to test payments: Visit
https://manage-sandbox.gocardless.com/signup to create one. Create an
access token and set it in the local_settings.py

To run (it will use a sqlite database in dev), simply type:

    make

Then you should be able to connect to http://localhost:8000.

To check your code for style (and hopefully tests in future), run `make
test`.
