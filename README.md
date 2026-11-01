# QtPyHammer
A Python 3.X alternative to Valve's 4.X Hammer Editor

## Installation

To launch from the terminal, on Linux:

```bash
$ git clone https://github.com/QtPyHammer-devs/QtPyHammer
$ cd QtPyHammer
$ python -m venv .env
$ source .env/bin/activate
(.env) $ python -m pip install -U pip
(.env) $ python -m pip install -e .
(.env) $ python hammer.py  # launch QtPyHammer
(.env) $ deactivate
$ # it is now safe to shutdown your computer
```

> [!NOTE]
> Basically a glorified `.vmf` viewer at present.
> If you want to edit `.vmf`s on Linux, check out [WifeRadiant](https://github.com/erysdren/WifeRadiant)

> [!WARNING]
> Encounters horrific memory leaks when loading more than 156KB of `.vmf` at a time.
> Basically, `test2.vmf` is the upper limit of what the editor can handle at present.
