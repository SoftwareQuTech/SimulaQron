How to build the docs
=====================

First, install some dependencies needed to build the docs:

```bash
make install-deps
```

Then, you can build the docs by:

```bash
make build
```

In system with a desktop GUI (i.e. non-headless systems), you can open the built docs with the command:

```bash
make open
```
which makes use of the command `open`. If you're on Linux and `open` does not work you can add `alias open='xdg-open` to you rc-file.

To both build the html files and open them, do:
```bash
make see
```
