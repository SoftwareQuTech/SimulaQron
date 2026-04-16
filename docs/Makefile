# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =
BUILDDIR      = build

# Internal variables.
PAPEROPT_a4     = -D latex_elements.papersize=a4
PAPEROPT_letter = -D latex_elements.papersize=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html        to make standalone HTML files"
	@echo "  dirhtml     to make HTML files named index.html in directories"
	@echo "  singlehtml  to make a single large HTML file"
	@echo "  pickle      to make pickle files"
	@echo "  json        to make JSON files"
	@echo "  htmlhelp    to make HTML files and an HTML help project"
	@echo "  qthelp      to make HTML files and a qthelp project"
	@echo "  applehelp   to make an Apple Help Book"
	@echo "  devhelp     to make HTML files and a Devhelp project"
	@echo "  epub        to make an epub"
	@echo "  epub3       to make an epub3"
	@echo "  latex       to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf    to make LaTeX files and run them through pdflatex"
	@echo "  latexpdfja  to make LaTeX files and run them through platex/dvipdfmx"
	@echo "  lualatexpdf to make LaTeX files and run them through lualatex"
	@echo "  xelatexpdf  to make LaTeX files and run them through xelatex"
	@echo "  text        to make text files"
	@echo "  man         to make manual pages"
	@echo "  texinfo     to make Texinfo files"
	@echo "  info        to make Texinfo files and run them through makeinfo"
	@echo "  gettext     to make PO message catalogs"
	@echo "  changes     to make an overview of all changed/added/deprecated items"
	@echo "  xml         to make Docutils-native XML files"
	@echo "  pseudoxml   to make pseudoxml-XML files for display purposes"
	@echo "  linkcheck   to check all external links for integrity"
	@echo "  doctest     to run all doctests embedded in the documentation (if enabled)"
	@echo "  coverage    to run coverage check of the documentation (if enabled)"
	@echo "  dummy       to check syntax errors of document sources"

clean:
	rm -rf $(BUILDDIR)/*

html:
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

docs:
	@make clean
	@rm -r html
	@make html
	@mkdir html
	@cp -r _build/html/* html

dirhtml:
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/dirhtml
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/dirhtml."

singlehtml:
	$(SPHINXBUILD) -b singlehtml $(ALLSPHINXOPTS) $(BUILDDIR)/singlehtml
	@echo
	@echo "Build finished. The HTML page is in $(BUILDDIR)/singlehtml."

pickle:
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) $(BUILDDIR)/pickle
	@echo
	@echo "Build finished; now you can process the pickle files."

json:
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) $(BUILDDIR)/json
	@echo
	@echo "Build finished; now you can process the JSON files."

htmlhelp:
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) $(BUILDDIR)/htmlhelp
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in $(BUILDDIR)/htmlhelp."

qthelp:
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) $(BUILDDIR)/qthelp
	@echo
	@echo "Build finished; now you can run "qcollectiongenerator" with the" \
	      ".qhcp project file in $(BUILDDIR)/qthelp, like this:"
	@echo "# qcollectiongenerator $(BUILDDIR)/qthelp/SimulaQron.qhcp"
	@echo "To view the help file:"
	@echo "# assistant -collectionFile $(BUILDDIR)/qthelp/SimulaQron.qhc"

applehelp:
	$(SPHINXBUILD) -b applehelp $(ALLSPHINXOPTS) $(BUILDDIR)/applehelp
	@echo
	@echo "Build finished. The help book is in $(BUILDDIR)/applehelp."
	@echo "N.B. You won't be able to view it unless you put it in" \
	      "~/Library/Documentation/Help or install it in your application" \
	      "bundle."

devhelp:
	$(SPHINXBUILD) -b devhelp $(ALLSPHINXOPTS) $(BUILDDIR)/devhelp
	@echo
	@echo "Build finished."
	@echo "To view the help file:"
	@echo "# mkdir -p $$HOME/.local/share/devhelp/SimulaQron"
	@echo "# ln -s $(BUILDDIR)/devhelp $$HOME/.local/share/devhelp/SimulaQron"
	@echo "# devhelp"

epub:
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) $(BUILDDIR)/epub
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

epub3:
	$(SPHINXBUILD) -b epub3 $(ALLSPHINXOPTS) $(BUILDDIR)/epub3
	@echo
	@echo "Build finished. The epub3 file is in $(BUILDDIR)/epub3."

latex:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo
	@echo "Build finished; the LaTeX files are in $(BUILDDIR)/latex."
	@echo "Run \`make' in that directory to run these through (pdf)latex" \
	      "(use \`make latexpdf' here to do that automatically)."

latexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

latexpdfja:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through platex and dvipdfmx..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf-ja
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

lualatexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through lualatex..."
	$(MAKE) PDFLATEX=lualatex -C $(BUILDDIR)/latex all-pdf
	@echo "lualatex finished; the PDF files are in $(BUILDDIR)/latex."

xelatexpdf:
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	@echo "Running LaTeX files through xelatex..."
	$(MAKE) PDFLATEX=xelatex -C $(BUILDDIR)/latex all-pdf
	@echo "xelatex finished; the PDF files are in $(BUILDDIR)/latex."

text:
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) $(BUILDDIR)/text
	@echo
	@echo "Build finished. The text files are in $(BUILDDIR)/text."

man:
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) $(BUILDDIR)/man
	@echo
	@echo "Build finished. The manual pages are in $(BUILDDIR)/man."

texinfo:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo
	@echo "Build finished. The Texinfo files are in $(BUILDDIR)/texinfo."
	@echo "Run \`make' in that directory to run these through makeinfo" \
	      "(use \`make info' here to do that automatically)."

info:
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	@echo "Running Texinfo files through makeinfo..."
	make -C $(BUILDDIR)/texinfo info
	@echo "makeinfo finished; the Info files are in $(BUILDDIR)/texinfo."

gettext:
	$(SPHINXBUILD) -b gettext $(I18NSPHINXOPTS) $(BUILDDIR)/locale
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/locale."

changes:
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) $(BUILDDIR)/changes
	@echo
	@echo "The overview file is in $(BUILDDIR)/changes."

linkcheck:
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

doctest:
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) $(BUILDDIR)/doctest
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in $(BUILDDIR)/doctest/output.txt."

coverage:
	$(SPHINXBUILD) -b coverage $(ALLSPHINXOPTS) $(BUILDDIR)/coverage
	@echo "Testing of coverage in the sources finished, look at the " \
	      "results in $(BUILDDIR)/coverage/python.txt."

xml:
	$(SPHINXBUILD) -b xml $(ALLSPHINXOPTS) $(BUILDDIR)/xml
	@echo
	@echo "Build finished. The XML files are in $(BUILDDIR)/xml."

pseudoxml:
	$(SPHINXBUILD) -b pseudoxml $(ALLSPHINXOPTS) $(BUILDDIR)/pseudoxml
	@echo
	@echo "Build finished. The pseudo-XML files are in $(BUILDDIR)/pseudoxml."

dummy:
	$(SPHINXBUILD) -b dummy $(ALLSPHINXOPTS) $(BUILDDIR)/dummy
	@echo
	@echo "Build finished. Dummy builder generates no files."

projectq-dep:
	# WARNING - To build the docs, we *need* projectq, since sphinx imports all modules fof simulaqron
	# This, as a side effect, imports projectq modules, so the doc build *fails* if projectq is not installed.
	# Python setuptools 81 removed "dry_run" option when compiling C++ code
	# this breaks the build of projectq
	# As a hack, we install the bare minimum tools to build projectq, then
	# we build and install it (ignoring any build requirement in the projectq
	# package spec), and finally we install the rest of the optional requirements
	@pip install "setuptools<81" pybind11
	@pip install "git+https://github.com/ProjectQ-Framework/ProjectQ.git@v0.8.0" --no-build-isolation

python-deps:
	@cat requirements.txt | xargs -n 1 -L 1 pip3 install

_add_jekyll:
	touch build/.nojekyll

build: html _add_jekyll

install-deps: projectq-dep python-deps

check-xdg:
	@{ \
    set -e ;\
	MIME_APP="$$(xdg-mime query default $$(xdg-mime query filetype ${BUILDDIR}/html/index.html) )"; \
	if [ "" = "$$MIME_APP" ]; then \
    	echo "No web browser detected, or this is a headless environment."; \
    	echo "If you already have a web browser installed, please run"; \
    	echo "xdg-mime default <browser-app-name>.desktop text/html"; \
    	echo 'Where <browser-app-name> could be "google-chrome", "firefox", etc.'; \
    	exit 1; \
	fi; \
	}

open: check-xdg
	open ${BUILDDIR}/html/index.html

see: html open

.PHONY: help clean html docs dirhtml singlehtml pickle json htmlhelp qthelp applehelp devhelp epub epub3 latex
.PHONY: latexpdf latexpdfja lualatexpdf xelatexpdf text man texinfo info gettext changes linkcheck doctest coverage
.PHONY: xml dummy pseudoxml python-deps build open see check-xdg
