# SimulaQron - simple quantum network simulator (4.0.0)

The purpose of this simulator of quantum network nodes is to allow you to develop new applications for
a future quantum internet, while we do not yet have real quantum network nodes available for testing. 

Since version 4.0, SimulaQron is compatible with [NetQASM](https://github.com/QuTech-Delft/netqasm).
See its documentation for how to use SimulaQron as a backend for running NetQASM applications.

## Installation

### Linux

Before proceeding, make sure you install Python 3.12. Please note that Python 3.13 or newer *is not supported*.
To install Python 3.12 in Debian-based distributions, you can first add the "deadsnakes" repository:

```shell
sudo add-apt-repository -y "ppa:deadsnakes/ppa"
```

Then you can install Python 3.12 and the Python development package:

```shell
sudo apt-get install python3.12-full python3.12-dev
```

Additionally, you will need the `build-essential` package, to install tools used when building some SimulaQron dependencies::

```shell
sudo apt-get install build-essential cmake vim linux-headers-generic
```

After this, you can install this repository by using the Makefile:

```shell
make install
```

Additionally, you can install SimulaQron with extra dependencies:
```shell
make install-optional
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

In macOS, the only supported way to install SimulaQron is by using a Virtual Machine. Considering this
please install a Virtual Machine Hypervisor such as [Oracle VirtualBox](https://www.virtualbox.org/wiki/Downloads),
and install a compatible operating system:

* Intel-based Macs: This is the case for Mac computers with Intel processor.s You can directly install the ["amd64"
  version of Ubuntu 24.04](https://ubuntu.com/download/desktop/thank-you?version=24.04.4&architecture=amd64&lts=true).
* ARM-based Macs: This is the case for "Apple Silicon" processors (M1 or newer, including the A18 Macbook Neo). For
  this type of Macs, you can install the ["arm64" version of Ubuntu 24.04](https://cdimage.ubuntu.com/releases/24.04/release/ubuntu-24.04.4-desktop-arm64.iso)

After installing the Operating System on the virtual machine, please continue the installation of SimulaQron in
the virtual machine using the Linux instructions as mentioned above.


Documentation
-------------

Documentation and examples are explained in the HTML documentation 
https://softwarequtech.github.io/SimulaQron/html/index.html

For upcoming and previous changes see the file [CHANGELOG.md](CHANGELOG.md)

More info at
http://www.simulaqron.org
