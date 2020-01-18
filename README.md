# QtPyHammer
A Python alternative to Valve's Hammer Editor (4.X in particular)

# Creating the dev environment
Open a terminal with admin privileges and navigate to the QtPyHammer folder

`cd C:/GitHub/QtPyHammer-master/`

Create a new python virtual environment

`python -m venv venv`

Activate your new venv, on Windows:

`call venv/scripts/activate`

On Mac / Linux:

`source venv/bin/activate`

Install the dependencies with pip

`python -m pip install -r requirements.txt`

You can now run QtPyHammer with the following command: (needs venv to be active)

`fbs run`

Other fbs operations, such as freezing QtPyHammer to a standalone release, or building an Installer may require additional packages

See this guide for more information: [https://www.learnpyqt.com/courses/packaging-and-distribution/packaging-pyqt5-apps-fbs/]

Be aware there is a security vulnerability in the version of PyInstaller used by fbs, but it only affects "onefile" builds, which fbs does not create
