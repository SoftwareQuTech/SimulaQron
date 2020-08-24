[![Build Status](https://travis-ci.com/SoftwareQuTech/SimulaQron.svg?branch=Develop)](https://travis-ci.com/SoftwareQuTech/SimulaQron)

SimulaQron - simple quantum network simulator (3.0.15)
=====================================================

The purpose of this simulator of quantum network nodes is to allow you to develop new applications for
a future quantum internet, while of course right now we do not yet have real quantum network nodes available for testing. 

Importantly, SimulaQron is an application level simulator, with the sole purpose on exploring abstraction layers and how to program a quantum network. If you are interested in a simulator that can assess, for example, the performance of quantum repeaters or their placement, QuTech is developing a separate lower level simulator that can also model timing delays. This lower level simulator has a very different purpose and performs a discrete event simulation in order to determine the effect of the timing of classical communication on repeater protocols. A first version of the low level simulator will only be available in 2018.

Installation:
```
pip3 install simulaqron
```

Documentation and examples are explained in the html documentation 
https://softwarequtech.github.io/SimulaQron/html/index.html

For upcoming and previous changes see the file [CHANGELOG.md]()

More info including a competition at
http://www.simulaqron.org
