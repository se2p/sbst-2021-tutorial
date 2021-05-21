# Simulation-based Testing with BeamNG.tech
A tutorial by Dr. Alessio Gambi, Pascale Maul, and Marc Mueller

## Setting up the project dependencies
To interact with BeamNG.tech from Python, you need to install the official Python API: `BeamNGpy`

For this tutorial we, used the version `1.19.1`. 

We run this tutorial using Powershell and Jupiter Notebooks.

### Step 0: Install Python 
To install Python on Windows, please refer to the official guides.
For this tutorial, we used Python version 3.7.9.

### Step 1: Create a Python Virtual Environment

Open a Powershell terminal, and `cd` to the folder where you have checked out "this" repo. In my case this is the folder `Y:/`.

You can check the version of Python you are using with the following command:

```
PS Y:\> py.exe -V
```

If the python version is the expected one, continue with the tutorial, otherwise move to Step 0 and install the right version of Python. 

> **Note**: If you have multiple Python executable installed in your system, use the full path to `py.exe`

> **Note**: If Windows complains that you cannot execute scripts from the command line, please read [Here](https://docs.vmware.com/en/vRealize-Automation/7.6/com.vmware.vra.iaas.hp.doc/GUID-9670AFC5-76B8-4321-822A-BCE05800DB5B.html#:~:text=Select%20Start%20%3E%20All%20Programs%20%3E%20Windows,settings%20for%20the%20execution%20policy.).

Finally, create a new virtual environment called `.venv` and *activate it* using the following command. In this tutorial, we use `venv`. There are other utilities that may can be used as well (e.g., `Conda`, `AnaConda`) but we did not tested them. You can read more on `venv` [here](https://docs.python.org/3/library/venv.html).

``` 
PS Y:\> py.exe -m venv .venv
PS Y:\> .\.venv\Scripts\activate
```

Update `pip` and other utilities. For this tutorial, we use `pip` version `21.1.1`, `setuptools` version `56.2.0` and `wheel` version `0.36.2`.

```
(.venv) PS Y:\> py.exe -m pip install --upgrade pip
(.venv) PS Y:\>

```

Finally, install `BeamNGpy`, version `1.19.1`:

```
(.venv) PS Y:\> pip install beamngpy==1.19.1
Collecting beamngpy==1.19.1

... Some verbose output ...

Installing collected packages: six, python-dateutil, pyparsing, Pillow, numpy, MarkupSafe, kiwisolver, cycler, colorama, scipy, PyOpenGL, msgpack, matplotlib, Jinja2, click, beamngpy
```
Check that all the required dependencies are indeed installed in the virtual environment:

```
(.venv) PS Y:\> pip freeze
```

### Alternative Installation Methods

We are aware of a problem on PyPi to prevent to installing older versions of `BeamNGpy`. If you need to install an older version, you can install it from source or from a local package.

#### Install BeamNGpy from source
Check out the code from GitHub (use the right tag!)

```
cd Y:
PS Y:\> git clone git@github.com:BeamNG/BeamNGpy.git
PS Y:\> cd .\BeamNGpy\
PS Y:\BeamNGpy>
```

Activate the `venv` where you want to install the library (e.g., `Y:\.venv`), and install it using `pip`:

```
pip install .
```

#### Install BeamNGpy from local package
Download the package from [https://pypi.org/project/beamngpy/](https://pypi.org/project/beamngpy/) somewhere (e.g., `Y:\`). Be sure you downloaded the right version, the version number is embedded in the file name.

For example, to install `1.19.1` you need to download file `beamngpy-1.19.1-py2.py3-none-any.whl` from [https://pypi.org/project/beamngpy/1.19.1/#files](https://pypi.org/project/beamngpy/1.19.1/#files)

Activate the virtual environment and install the package using `pip`:

```
cd Y:
PS Y:\> 
(.venv) PS Y:\> pip install ./beamngpy-1.19.1-py2.py3-none-any.whl
```