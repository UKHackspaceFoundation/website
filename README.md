This is the website for www.hackspace.org.uk.

This is a Python 3 project, so make sure you have a python 3
interpreter installed.

To configure: Copy the hsf/local_settings.py.example to
hsf/local_settings.py and edit as necessary.

To run (it will use a sqlite database in dev), simply type:

    make

Then you should be able to connect to http://localhost:8000.

To check your code for style (and hopefully tests in future), run `make
test`.
