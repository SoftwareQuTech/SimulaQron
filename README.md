# SimulaQron - simple quantum network simulator (4.1.1)

The purpose of this simulator of quantum network nodes is to allow you to develop new applications for
a future quantum internet, while we do not yet have real quantum network nodes available for testing. 

Since version 4.0, SimulaQron is compatible with [NetQASM](https://github.com/QuTech-Delft/netqasm).
See its documentation for how to use SimulaQron as a backend for running NetQASM applications.

## Installation

### Linux

#### Software dependencies

Before proceeding, make sure you install Python 3.12. Please note that Python 3.13 or newer *is not supported*.
To install Python 3.12 in Debian-based distributions, you can first add the "deadsnakes" repository:

```shell
sudo add-apt-repository -y "ppa:deadsnakes/ppa"
```

Then you can install Python 3.12 and the Python development package:

```shell
sudo apt-get install python3.12-full python3.12-dev
```
Additionally, you will need the `build-essential` package, to install tools used when building some SimulaQron dependencies:

```shell
sudo apt-get install build-essential cmake vim linux-headers-generic
```
After this point, you should have all the required dependencies.


#### Create Python virtual environment (venv)

Before proceeding with the installation


##### Installing from PyPI

Installing from PyPI is simple; once you activated your virtual environment, simply run:

```shell
pip install simulaqron
```

Which should install SimulaQron in its base backends. Additionally, to allow support for `projectq`, you might want
to install the optional dependencies:

```shell
pip install "simulaqron[opt]"
```


#### Installing from this repository

It is also possible to install SimulaQron directly from this repository. First, make sure you have checked out
this repository, then navigate to the root folder of SimulaQron's repository. Once there, you can install SimulaQron 
by using the Makefile:

```shell
make install
```
Additionally, you can install SimulaQron with extra dependencies:
```shell
make install-optional
```

Finally, if you would like to contribute to the development of SimulaQron, please install the development dependencies:
```shell
make install-development
```

### Windows

In Windows, SimulaQron can be installed in two similar ways:

* Using WSL: *Windows for Linux Subsystems* (WSL) is a way to execute the linux kernel (and linux apps)
  in a Windows environment. To install WSL, you can follow the [official microsoft documentation](https://learn.microsoft.com/en-us/windows/wsl/install).
  After this you can install SimulaQron in WSL using the Linux instructions from above.
* Using a Linux Virtual Machine: It is also possible to create a Linux environment using a Virtual Machine
  Hypervisor such as [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads). After installing this,
  create a new Virtual Machine and install a compatible linux version (such as [Ubuntu 24.04](https://ubuntu.com/download/desktop/thank-you?version=24.04.4&architecture=amd64&lts=true)).
  After the installation is finished, follow the instructions to install SimulaQron on a Linux machine as
  presented above.


### macOS

#### Native installation

SimulaQron has also been tested working on macOS Tahoe (26.5) on an M3 Pro CPU.

Before proceeding with the SimulaQron install, you need to install python 3.12, which is available from the
[Homebrew package manager](https://brew.sh/). Once that homebrew has been installed, you can install Python
3.12 using the following command:

```shell
brew install python@3.12
```

Additionally, to install the optional dependencies, you will need to install *XCode COmmand Line Tools*. To do
so, run the following command in a terminal:

```shell
xcode-select --install
```

And follow the instructions on the screen. After this, you can follow the instructions to install SimulaQron
either [from PyPI](#installing-from-pypi) or directly [from this repository](#installing-from-this-repository).


#### Using the provided virtual machines

It is also possible to install SimulaQron on macOS using a Virtual Machine. Considering this  please install a
Virtual Machine Hypervisor such as [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads), and install a compatible operating system:

* Intel-based Macs: This is the case for Mac computers with Intel processor.s You can directly install the ["amd64"
  version of Ubuntu 24.04](https://ubuntu.com/download/desktop/thank-you?version=24.04.4&architecture=amd64&lts=true).
* ARM-based Macs: This is the case for "Apple Silicon" processors (M1 or newer, including the A18 Macbook Neo). For
  this type of Macs, you can install the ["arm64" version of Ubuntu 24.04](https://cdimage.ubuntu.com/releases/24.04/release/ubuntu-24.04.4-desktop-arm64.iso)

After installing the Operating System on the virtual machine, please continue the installation of SimulaQron in
the virtual machine using the Linux instructions as mentioned above.


## Tests

There are 2 sets of tests: quick and slow ones. To ease the execution, the `Makefile` provides two targets:
* `tests`: This target only run the quick tests.
* `tests_all`: This target runs quick and slow tests.

To run a test target, simply invoke it with make:
```shell
make tests
```

or:
```shell
make tests_all
```


## Documentation


Documentation and examples are explained in the HTML documentation 
https://softwarequtech.github.io/SimulaQron/index.html

For upcoming and previous changes see the file [CHANGELOG.md](CHANGELOG.md)

More info at
http://www.simulaqron.org
