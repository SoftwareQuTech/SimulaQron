How to build the docs
=====================

First build the docs by:

```bash
make build
```

This will first install any required dependencies and build the html files. (the next time you can simply do `make html`).

To open the built docs, do:

```bash
make open
```
which makes use of the command `open`. If you're on Linux and `open` does not work you can add `alias open='xdg-open` to you rc-file.

To both build the html files and open them, do:
```bash
make see
```
