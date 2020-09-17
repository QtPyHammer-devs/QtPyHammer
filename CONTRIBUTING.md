# How to Contribute to QtPyHammer
Welcome aboard! And thanks for considering helping us out with this crazy project!

Be sure to join our [Discord Server](https://discord.gg/sW4Gzke) if you haven't already.  
And please, don't forget to read the [Code of Conduct](CODE_OF_CONDUCT.md)

> Come on in! The ~~spaghetti~~ code's warm!

NOTE: [GitHub Community Standards](https://opensource.guide/)  
NOTE: [Building Community](https://opensource.guide/building-community/)

#### Table of Contents
[Code of Conduct](#code-of-conduct)

[Do I Need Experience?](#do-i-need-experience?)

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
 * [IDE Linters](#ide-linters)
 * [Documentation](#documentation)
 * [Testing](#testing)
 * [Further Reading](#further-reading)

[Frequently Asked Questions](#frequently-asked-questions)
 * [Are we an Organisation?](#are-we-an-organisation?)
 * [Are we Really Democratic?](#are-we-really-democratic?)



## Code of Conduct
Please read the full [Code of Conduct](CODE_OF_CONDUCT.md)  
We will hold you to it's standards, even if you haven't read it  
The rules apply to the discord too. Read it! (please)  



## Do I Need Experience?
Not at all.  
Casual contributions are what we're all about.  
That's why QtPyHammer is made with Python.  
We're making an editor that puts users first.  

Our aim is to have an editor than anyone can use, and code anyone can edit.  
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
QtPyHammer gets it's name from being written (mostly) in Python
If you don't have it installed, get [python 3.8](https://www.python.org/downloads/release/python-385/)

### Joining the Crew
Programmers make the code, so they get to decide what they make  
Anyone can become a programmer! But, you will have to learn  

Veteran programmers have a responsibility to help anyone that wishes to learn
Experience has value, we respect our ~~elders~~ veteran programmers

ping bikkie on discord, they'll help you get set up


### Setting up a Virtual Environment
We recommend using a python virtual environment.
They make life easier for all programmers working on QtPyHammer by ensuring everyone is working with the same code.
When everyone working on the code is using the same versions of each dependency, tracking down bugs becomes waaay easier than it would be otherwise
Be sure to check the #announcements channel in the discord for any changes to `requirements.txt`
If you have changed `requirements.txt`, make sure an announcement gets sent out!

So, setting up that virtual environment:
First, open a terminal at the top level (usually QtPyHammer-master)
Then, run this: `$ python -m venv venv`
(Linux users may need to install python-venv first)

Activate your new virtual environment:  
| Operating System | Command |
| Windows | `$ call venv/scripts/activate` |  
| Mac OS | `$ source venv/bin/activate` |
| Linux | `$ source venv/bin/activate` |  

Finally, install all dependencies with pip  
`$ python -m pip install -r requirements.txt`  

You can now run QtPyHammer from the terminal
`$ python hammer.py`


### Working with GitHub
Check out [Atlassian's Guide](https://www.atlassian.com/git/tutorials/what-is-version-control)
Make sure to pull the latest version before you commit!  
Communicate with other [contributors](https://github.com/snake-biscuits/QtPyHammer/graphs/contributors) to avoid code conflicts!  

If you're planning on making big changes:  
Make a branch to avoid conflicts with the master branch
Name your branch something short that explains what changes you're making
Talk to other programmers to see who can help you with your workload  
(Nagging a programmer to write documentation is OK, but only in small doses)
TODO: this is hard for beginners, @asd can you think of anything I've missed here?


### Coding Prototypes
TODO: @asd, what works for you? describe your approach & experience here.



## Style Guide
We use [PEP8](https://www.python.org/dev/peps/pep-0008/) around here  
It's not very fun but it keeps the code neat & tidy  
And who doesn't like tidy code? (bikkie, the answer is bikkie)  
Some warnings are OK to leave in when prototyping  
TODO: list warnings you can ignore


### Linter
If you're using an IDE we recommend getting a linter plugin.  
Every time a commit is pushed to `master`, GitHub checks all python scripts meet PEP8 standards.  
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
| Visual Studio Code  | TODO: find a vscode PEP8 linter                         |

If you don't use an IDE that's OK.  IDEs have their benefits but some of us prefer notepad.  
Notepad++ if you're fancy.

If you don't / can't get a linter to review your code, you can still use flake8.  
```
$ flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
$ flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```
GitHub also automatically runs these commands every time we push to GitHub.  
You may have another programmer ping you with a polite request to look at these warnings.  
It's OK to ask someone else to help clean up your formatting, but we prefer you do it yourself.  


### Documentation
Please use comments in your code to help explain how it all works.
Be sure to use docstrings too. Consider writing a wiki page or two
Your future self will thank you, trust me

### Testing
Write tests! Run tests! Found a bug you can't fix? Ask for help!

### Further Reading
[The Zen of Python](https://www.python.org/dev/peps/pep-0020/#the-zen-of-python)  
[Jack Diederich - Stop Writing Classes](https://www.youtube.com/watch?v=o9pEzgHorH0)  
[Raymond Hettinger - Transforming Code into Beautiful, Idiomatic Python](https://www.youtube.com/watch?v=OSGv2VnC0go)  
[Raymond Hettinger - Beyond PEP 8: Best practices for beautiful, intelligible code](https://www.youtube.com/watch?v=wf-BqAjZb8M)



## Frequently Asked Questions
### Are we an organisation?
While we aim be democratic in our work, we aren't explicitly an organisation.  
Our democracy has layers  

### Are we Really democratic?  
Kind of.  
There are many ways to contribute, and each role holds a certain level of power:

| Role                | Power                   |  
|---------------------|-------------------------|  
| Veteran Programmers | Teach newer programmers |
| Programmers         | Write the code          |
| Paper protoypers    | Shapes ideas into plans |   
| Feature requesters  | Sends in new ideas      |
| Testers             | Gives feedback          |
| Users               | Also gives feedback     |

Programmers, prototypers & requesters make stuff, that means they get to decide what they make.
Anyone is free to make what they want,
but sometimes there are jobs that must be done.

While we make decisions democratically, we don't hold explicitly hold anyone to finishing what they start.
While pressure can be good, remember that contributors are not paid.
We contribute out of our free time.
