# How to Contribute to QtPyHammer
Welcome aboard! And thanks for considering helping us out with this crazy project!

Be sure to join our [Discord Server](https://discord.gg/sW4Gzke) if you haven't already.  
And please, don't forget to read the [Code of Conduct](CODE_OF_CONDUCT.md)

> Come on in! The ~~spaghetti~~ code's warm!

#### Table of Contents
[Code of Conduct](#code-of-conduct)

[Do I Need Experience?](#do-i-need-experience)

[How Can I Contribute?](#how-can-i-contribute)
 * [Feature Requests](#feature-requests)
 * [Paper Prototypes](#paper-prototypes)
 * [Wiki Entries](#wiki-entries)
 * [Art](#art)
 * [Sharing Tips](#sharing-tips)
 * [Reporting Bugs](#reporting-bugs)
 * [Other](#other)

[Contributing Code](#contributing-code)
 * [Joining the Crew](#joining-the-crew)
 * [Setting up a Virtual Environment](#setting-up-a-virtual-environment)  
 * [Working with GitHub](#working-with-github)
 * [Coding Prototypes](#coding-prototypes)

[Style Guide](#style-guide)
 * [PEP 8](#pep-8httpswwwpythonorgdevpepspep-0008)
 * [Type Hints](#type-hints)
 * [Naming Conventions](#naming-conventions)
 * [Documentation](#documentation)
 * [Testing](#testing)
 * [Further Reading](#further-reading)

[Frequently Asked Questions](#frequently-asked-questions)
 * [What is QtPyHammer?](#what-is-qtpyhammer)
 * [Who are the QtPyHammer Team?](#who-are-the-qtpyhammer-team)
 * [Who's in Charge of the Project?](#who's-in-charge-of-the-project)



## Code of Conduct
Please read the full [Code of Conduct](CODE_OF_CONDUCT.md)  
We will hold you to it's standards, even if you haven't read it  
The rules apply to the discord too. Read it! (please)  



## Do I Need Experience?
Not at all.  
Casual contributions are what we're all about.  
That's why QtPyHammer is made with Python.  
We're making an editor that puts users first.  

Our aim is to have an editor anyone can use, and code anyone can edit.  
We aim to have anyone that wants a feature added or bug fixed to have the tools to do so.  

There's no pressure to keep contributing either, no contribution is too small.  
If you know what you want to work on, ping a veteran programmer and they'll help you get started  
If you want to contribute, but aren't sure what to do, check out `#feature-requests` for inspiration



## How can I contribute?
### Feature Requests
We keep a [list of requested features](https://github.com/snake-biscuits/QtPyHammer/wiki/Features-requested-by-users), be sure to read it to see if your idea is already on the list!
most of these feature requests were left in the [Discord's](https://discord.gg/sW4Gzke) `#feature-requests` channel.
We take ideas through Discord so everyone can discuss them, not just the programmers!

Just typing: "I wish hammer could do X" is a totally valid way to help direct and shape the project
If your idea is particularly exciting, you may find yourself making...


### Paper Prototypes
When a discussion sparks up, you may find yourself planning features right in the #feature-requests channel!
These discussions really help flesh out ideas.
Plus, they give programmers a clearer understanding of how to *make your dreams come true*  


### Wiki Entries
If you want to help others understand how QtPyHammer works under the hood, consider helping write a wiki entry.
You can work with the programmer that wrote a particular part of code to write up documentation


### Art
We need:  
 * A splash screen  
   ~~Please draw our mascot swimming in code spaghetti with little meatball floaties~~  
 * Icons for buttons

We would like:  
 * GLSL Shaders (programming can be art too!)  
 * UI Mock-ups  

And most importantly:
 * Our [Discord](https://discord.gg/sW4Gzke) needs more emotes!


### Sharing Tips
We want to give users tips on the splash screen.  
Do you know of a hammer feature that's hard to find?  
Tell us all what is and where to find it in: [tip_of_the_day.txt](tip_of_the_day.txt)


### Reporting Bugs
TODO: Bug report issue template


### Other
Can you think of another way to contribute? Add it to this list!  
That's a contribution too!



## Contributing Code
QtPyHammer gets it's name from being written (mostly) in Python.  
If you don't have it installed, get [python 3.8](https://www.python.org/downloads/release/python-385/)

### Joining the Crew
Programmers make the code, so they get to decide what they make  
Anyone can become a programmer! But you will have to learn  

We appreciate everyone with knowledge who uses it to help those that wish to learn.  
Experience has value, and we respect our ~~elders~~ veteran programmers.  
If you're starting out and need help learning, get the attention of a programmer.  
And please understand that while we appreciate teachers, it's not compulsory.  

We consider clear documentation to be form of teaching, since it helps newcomers understand the code.
That said, nagging a programmer to write documentation is only OK in small doses.
Please don't harass anyone.

If you're not sure who to ask: `@bikkie` on discord, they'll help you get set up  
TODO: have a list of people who are comfortable to help newcomers in Discord


### Setting up a Virtual Environment
We recommend using a python virtual environment.
They make life easier for all programmers working on QtPyHammer by ensuring everyone is working with the same code.
When everyone working on the code is using the same versions of each dependency, tracking down bugs becomes waaay easier than it would be otherwise
Be sure to check the `#announcements` channel in the discord for any changes to `requirements.txt`
If you have changed `requirements.txt`, make sure an announcement gets sent out!

So, setting up that virtual environment:  
First, open a terminal at the top level (usually QtPyHammer-master)  
Then, run this: `$ python -m venv venv`  
(Linux users may need to install python-venv first)

Activate your new virtual environment:  

| Operating System | Command                        |  
|------------------|--------------------------------|  
| Windows          | `$ call venv/scripts/activate` |  
| Mac OS           | `$ source venv/bin/activate`   |  
| Linux            | `$ source venv/bin/activate`   |  

Finally, install all dependencies with pip  
`$ python -m pip install -r requirements.txt`  

You can now run QtPyHammer from the terminal
`$ python hammer.py`


### Working with GitHub
TODO: GitHub is hard for beginners, @asd can you think of anything I've missed? - Added the last line. seems about fine now
 * Check out [Atlassian's Guide](https://www.atlassian.com/git/tutorials/what-is-version-control)
 * Make sure to pull the latest version before you commit!  
 * Communicate with other [contributors](https://github.com/snake-biscuits/QtPyHammer/graphs/contributors) to avoid code conflicts!  
 * If you are working on a prototype script of your own, it's ok to push to the main branch.

If you're planning on making big changes:  
 1. Talk to other programmers to see who can help you with your workload  
 2. Make a branch to avoid conflicts with the master branch
 3. Name your branch something short that explains what changes you're making



### Coding Prototypes
When adding code for the first time, understanding how the program fits together can be confusing  
That's why we have the `prototypes\` folder!  
It's a space where you can experiment without getting tangled up in the rest of QPH

TODO: @asd, what works for you? please describe your approach / experience here.
I use VS Code for prototyping and it's definitely easier to just install all the modules you need in the `prototype\venv` folder and opening vs code in `prototype\`
This removes the need to put in weird directory modifier for all the imports



## Style Guide
We use [PEP 8](https://www.python.org/dev/peps/pep-0008/) around here  
It's not very fun but it keeps the code neat & tidy  
And who doesn't like tidy code? (bikkie, the answer is bikkie)  
You can ask someone else to help you meet the requirements of the style guide, **but we prefer you do it yourself.**  


### [PEP 8](https://www.python.org/dev/peps/pep-0008/)
If you're using an IDE we recommend getting a PEP 8 linter plugin.  
Every time a commit is pushed to `master`, GitHub checks all python scripts meet PEP 8 standards.  
Having a linter plugin in your IDE helps you catch warnings before you push.   
You will probably need to install `flake8` to use these plugins.  
Add it to your virtual environment like so:
```
$ call venv/scripts/activate
$ pip install flake8
```
Most of us use these linter plugins

| IDE                 | Plugin                                                  |  
|---------------------|---------------------------------------------------------|  
| Atom                | [linter-flake8](https://atom.io/packages/linter-flake8) |
| Visual Studio Code  | [ms-python.python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) |  

If you don't use an IDE that's OK.  IDEs have their benefits but some of us prefer notepad.  
Notepad++ if you're fancy.

If you don't / can't get a linter to review your code, you can still use flake8.  
```
$ flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
$ flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```
GitHub also automatically runs these commands every time we push to GitHub.  
Some warnings you will get are OK to leave in when prototyping. You can ignore:  

| Code | Reason                                                                   |
|------|--------------------------------------------------------------------------|
| C901 | "Complex is better than complicated" - The Zen of Python                 |
| E266 | `### Important Comments` look pretty so they can stay                    |
| E501 | Long lines are OK, so long as the line is easy to understand             |
| F403 | C-based packages are named to avoid namespace collision anyway           |
| F405 | C-based packages are named to avoid namespace collision anyway           |

If you get a code you don't understand,
check [flake8rules.com](https://www.flake8rules.com/)
to get more details.  


### Type Hints
Type hints are a feature officially added to Python in version 3.7  
With type hints code can become much more readable and easier to use  
Check out these links for pointers:
 * [PEP 484](https://www.python.org/dev/peps/pep-0484/): which details a standard which we follow
 * [PEP 563](https://www.python.org/dev/peps/pep-0563/): explains why we should import `annotations` from `__future__`
 * [mypy](https://mypy-lang.org/): the type checker on which PEP 484 is based
 * [typing](https://docs.python.org/3/library/typing.html): official python module for making broad type hints

### Naming Conventions
A linter will not give warning for naming conventions, so we define our own.  
PEP 8 recommends using descriptive, lowercase variable & function names, spaced with underscores.  
For class names, CamelCase is preferred, since it tells you at a glance that an object is a class
```python
from __future__ import annotations
from typing import List


def flipped_selection(axis: str) -> List[PointEntity]:
    flip_along = {"x": flip_x, "y": flip_y, "z": flip_z}
    # ^ {"axis": function}
    flip_function = flip_along[axis]
    global selection: List[PointEntity]
    return list(map(flip_function, selection))


class PointEntity:
    classname: str
    def __init__(self, classname: str):
        self.classname = classname


draw_distance = 4096  # Hammer Units
some_point_entity = PointEntity("info_teamspawn")
```
Note that we don't hint the return type when functions return nothing.

### Documentation
Please use comments in your code to help explain how it all works.
Be sure to use docstrings too. Consider writing a wiki page or two
Your future self will thank you, trust me

### Testing
Write tests! Run tests! Found a bug you can't fix? Ask for help!  
Tests are particularly handy for checking what you may have broken before pushing a commit  


### Further Reading
[The Zen of Python](https://www.python.org/dev/peps/pep-0020/#the-zen-of-python)  
[Jack Diederich - Stop Writing Classes](https://www.youtube.com/watch?v=o9pEzgHorH0)  
[Raymond Hettinger - Transforming Code into Beautiful, Idiomatic Python](https://www.youtube.com/watch?v=OSGv2VnC0go)  
[Raymond Hettinger - Beyond PEP 8: Best practices for beautiful, intelligible code](https://www.youtube.com/watch?v=wf-BqAjZb8M)



## Frequently Asked Questions
### What is QtPyHammer?
QtPyHammer is an alternative to Valve's Hammer World Editor,
written from scratch, in Python.  

### Who are the QtPyHammer Team?
The QtPyHammer Team is mostly made up of [TF2Maps](https://tf2maps.net/) members.  
Some of us are programmers, most of us are Hammer users.  
We're here to make a Hammer for the users, a Hammer that anyone can repair when it breaks.  

We decide what we make democratically, asking users what they want.
Though some decisions, like large code refactors, are decided by Veteran Programmers.


### Who's in Charge of the Project?  
QtPyHammer is managed democratically, kind of.  

In practice, the team functions as a sort of casual Oligarchy.  
There are many roles within the team, and each holds a certain level of power:

| Role                | Power                                     |
|---------------------|-------------------------------------------|
| Veteran Programmers | Control the overall structure of the code |
| Programmers         | Make prototypes & write the code          |
| Paper protoypers    | Workshop ideas & design user interfaces   |
| Feature requesters  | Send in, workshop & refine ideas          |
| Testers             | Give feedback & help identify bugs        |
| Users               | Give feedback & request features          |

Programmers & prototypers make stuff, that means they get to decide what they make.  
Anyone is free to make what they want, but sometimes there are jobs that must be done.

While we make decisions democratically, we don't hold explicitly hold anyone to finishing what they start.
Pressure can be good, but remember that contributors are not paid.
We contribute out of our free time.

Veterans are well experienced in their skillsets and have spent a long time with the project.  
As a general rule, veterans get more of a say, since we expect they know what they're talking about.
