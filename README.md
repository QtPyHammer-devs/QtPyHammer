[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=QtPyHammer-devs_QtPyHammer&metric=ncloc)](https://sonarcloud.io/dashboard?id=QtPyHammer-devs_QtPyHammer)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=QtPyHammer-devs_QtPyHammer&metric=code_smells)](https://sonarcloud.io/dashboard?id=QtPyHammer-devs_QtPyHammer)
[![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=QtPyHammer-devs_QtPyHammer&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=QtPyHammer-devs_QtPyHammer)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=QtPyHammer-devs_QtPyHammer&metric=sqale_rating)](https://sonarcloud.io/dashboard?id=QtPyHammer-devs_QtPyHammer)

# QtPyHammer
A Python alternative to Valve's Hammer Editor (4.X in particular)

# Creating the dev environment
It's recommended to use a python virtual environment to preserve the version of dependencies, here's how you do that:

First, open a terminal in the QtPyHammer folder   
Then, create a new python(3.8+) virtual environment  
(Linux users may need to install python-venv first)  
`$ python -m venv venv`   
Activate your new virtual environment   
Windows: `$ call venv/scripts/activate`  
Mac / Linux: `$ source venv/bin/activate`  
Finally, install all dependencies with pip
`$ python -m pip install -r requirements.txt`

You can now run QtPyHammer from the terminal  
`$ python hammer.py`  
