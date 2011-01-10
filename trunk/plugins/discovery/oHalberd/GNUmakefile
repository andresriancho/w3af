# ============================================================================
# This makefile is intended for developers. End users should rely on setup.py.
# ============================================================================

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


srcdir := .
scriptsdir := $(srcdir)/scripts
modulesdir := $(srcdir)/Halberd
docdir := $(srcdir)/doc
apidocdir := $(srcdir)/doc/api
mandir := $(srcdir)/man
testdir := $(srcdir)/tests


PYTHON := /usr/bin/python
PYTHON_COUNT := /usr/local/bin/python_count
PYLINT := /usr/bin/pylint
EPYDOC := /usr/bin/epydoc
CTAGS := ctags
DARCS := /usr/bin/darcs
SHTOOLIZE := /usr/local/bin/shtoolize
SHTOOL := $(srcdir)/shtool
RM := /bin/rm -f
MKDIR := /bin/mkdir
SETUP := $(PYTHON) $(srcdir)/setup.py
HELP2MAN := ~/bin/hacked-help2man


versionfile := $(modulesdir)/version.py

SCRIPTS := $(scriptsdir)/halberd
MODULES := $(filter-out $(modulesdir)/version.py, \
		   $(wildcard $(modulesdir)/*.py)) \
		   $(wildcard $(modulesdir)/clues/*.py)

SOURCES := $(SCRIPTS) $(MODULES)
TEST_SOURCES := $(wildcard $(testdir)/*.py)
ALL_SOURCES := $(SOURCES) $(TEST_SOURCES)

ALL_DIRS := $(sort $(dir $(ALL_SOURCES)))


remove = $(RM) $(addsuffix $(strip $(1)), $(2))


all:
	@echo "============================================================================"
	@echo "This makefile is intended for developers. End users should rely on setup.py."
	@echo "============================================================================"

clean:
	$(RM) tags
	$(RM) -r $(srcdir)/build
	$(call remove, *.pyc, $(ALL_DIRS))
	$(call remove, *.pyo, $(ALL_DIRS))
	$(MAKE) -C doc clean

clobber: clean
	$(RM) *.bak
	$(call remove, *~, $(ALL_DIRS) $(docdir)/)
	$(MAKE) -C doc clobber

build: $(SOURCES)
	$(SETUP) build

dist: distclean lint setversion doc ChangeLog
	$(SETUP) sdist

check: $(ALL_SOURCES)
	$(SETUP) test
	PYTHONPATH=$(modulesdir):$(modulesdir)/clues:$$PYTHONPATH \
	$(PYTHON) $(modulesdir)/clues/analysis.py

install: build doc
	$(SETUP) install --prefix $$HOME

distclean: clobber
	$(RM) $(srcdir)/MANIFEST
	$(RM) $(srcdir)/ChangeLog
	$(RM) $(docdir)/*.html
	$(RM) $(mandir)/man1/halberd.1
	$(RM) -r $(apidocdir)
	$(RM) -r $(srcdir)/dist

doc: $(apidocdir)/index.html $(mandir)/man1/halberd.1
	$(MAKE) -C $(docdir)

$(apidocdir)/index.html: $(MODULES)
	$(EPYDOC) -o $(apidocdir) $^

$(mandir)/man1/halberd.1:
	$(HELP2MAN) --include $(srcdir)/help2man.cfg --no-info $(scriptsdir)/halberd --output $@

tags: $(ALL_SOURCES)
	$(CTAGS) $^

setversion: shtool
	@version=`$(SHTOOL) version -l python $(versionfile)`; \
	$(SHTOOL) version -l python -n halberd -s $$version $(versionfile)

incversion: shtool
	$(SHTOOL) version -l python -n halberd -i l $(versionfile)

shtool:
	$(SHTOOLIZE) -o $@ version

lint:
	$(PYLINT) --required-attributes= --additional-builtins=map,filter --method-rgx='.*' --function-rgx='.*' $(ALL_SOURCES)

ChangeLog: $(ALL_SOURCES)
	$(DARCS) changes --human-readable > ChangeLog

count: $(ALL_SOURCES)
	@$(PYTHON_COUNT) $^


.PHONY: clean clobber distclean dist setversion incversion check count install lint ChangeLog 


# vim: noexpandtab
