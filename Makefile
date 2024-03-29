PROJECTNAME = workflow_engine
DISTDIR = dist
BUILDDIR = build
RELEASEDIR = $(PROJECTNAME)-$(VERSION)$(RELEASE)
EGGINFODIR = $(PROJECTNAME).egg-info
DOCDIR = doc
COVDIR = htmlcov

DOC_URL=http://alleninstitute.github.io/BlueSkyWorkflowEngine

build:
	mkdir -p $(DISTDIR)/$(PROJECTNAME) 
	cp -r workflow_engine setup.py README.md $(DISTDIR)/$(PROJECTNAME)/
	cd $(DISTDIR); tar czvf $(PROJECTNAME).tgz --exclude .git $(PROJECTNAME)
	

distutils_build:
	python setup.py build

sdist: distutils_build
	python setup.py sdist

pypi_deploy:
	python setup.py sdist upload --repository local

pytest_lax:
	python setup.py test

pytest: pytest_lax

test: pytest

pytest_pep8:
	find -L . -name "test_*.py" -exec py.test --boxed --pep8 --cov-config coveragerc --cov=workflow_engine --cov-report html --junitxml=test-reports/test.xml {} \+

pytest_lite:
	find -L . -name "test_*.py" -exec py.test --boxed --assert=reinterp --junitxml=test-reports/test.xml {} \+

pylint:
	pylint --disable=C workflow_engine > htmlcov/pylint.txt || exit 0
	grep import-error htmlcov/pylint.txt > htmlcov/pylint_imports.txt

flake8:
	flake8 --ignore=E201,E202,E226 --max-line-length=200 --filename 'workflow_engine/**/*.py' workflow_engine | grep -v "local variable '_' is assigned to but never used" > htmlcov/flake8.txt
	grep -i "import" htmlcov/flake8.txt > htmlcov/imports.txt || exit 0

EXAMPLES=$(DOCDIR)/_static/examples

fsm_figures:
	python -m manage graph_transitions -o doc_template/aibs_sphinx/static/task_states.png workflow_engine.Task
	python -m manage graph_transitions -o doc_template/aibs_sphinx/static/job_states.png workflow_engine.Job

doc: FORCE
	sphinx-apidoc -d 4 --force -H "Blue Sky Workflow Engine" -A "Allen Institute for Brain Science" -V $(VERSION) -R $(VERSION)$(RELEASE) --full -o $(DOCDIR) --module-first workflow_client
	sphinx-apidoc -d 4 --force -H "Blue Sky Workflow Engine" -A "Allen Institute for Brain Science" -V $(VERSION) -R $(VERSION)$(RELEASE) --full -o $(DOCDIR) --module-first $(PROJECTNAME)
	cp doc_template/*.rst doc_template/conf.py $(DOCDIR)
	# cp -R $(DOCDIR)/examples $(EXAMPLES)
	sed -i --expression "s/|version|/${VERSION}/g" $(DOCDIR)/conf.py
	cp -R doc_template/aibs_sphinx/static/* $(DOCDIR)/_static
	cp -R doc_template/aibs_sphinx/templates/* $(DOCDIR)/_templates
ifdef STATIC
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" $(DOCDIR)/_templates/layout.html
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" $(DOCDIR)/_templates/portalHeader.html
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" $(DOCDIR)/_templates/portalFooter.html
endif
	cd $(DOCDIR) && make html || true

FORCE:

clean:
	rm -rf $(DISTDIR)
	rm -rf $(BUILDDIR)
	rm -rf $(RELEASEDIR)
	rm -rf $(EGGINFODIR)
	rm -rf $(DOCDIR)
