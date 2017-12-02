PROJECTNAME = workflow_engine
DISTDIR = dist
BUILDDIR = build
export RELEASE=.dev
RELEASEDIR = $(PROJECTNAME)-$(VERSION)$(RELEASE)
EGGINFODIR = $(PROJECTNAME).egg-info
DOCDIR = doc
COVDIR = htmlcov

DOC_URL=http://alleninstitute.github.io/BlueSkyWorkflowEngine

build:
	mkdir -p $(DISTDIR)/$(PROJECTNAME) 
	cp -r workflow_engine setup.py README.md $(DISTDIR)/$(PROJECTNAME)/
	cd $(DISTDIR); tar czvf $(PROJECTNAME).tgz --exclude .git $(PROJECTNAME)
	

distutils_build: clean
	python setup.py build

sdist: distutils_build
	python setup.py sdist

pypi_deploy:
	python setup.py sdist upload --repository local

pytest_lax:
	python -m pytest -s --boxed --cov=workflow_engine --cov-report html --junitxml=test-reports/test.xml

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

EXAMPLES=doc/_static/examples

doc: FORCE
	sphinx-apidoc -d 4 -H "Blue Sky Workflow Engine" -A "Allen Institute for Brain Science" -V $(VERSION) -R $(VERSION)$(RELEASE) --full -o doc workflow_client
	sphinx-apidoc -d 4 -H "Blue Sky Workflow Engine" -A "Allen Institute for Brain Science" -V $(VERSION) -R $(VERSION)$(RELEASE) --full -o doc $(PROJECTNAME)
	cp doc_template/*.rst doc_template/conf.py doc
	# cp -R doc_template/examples $(EXAMPLES)
	sed -i --expression "s/|version|/${VERSION}/g" doc/conf.py
	cp -R doc_template/aibs_sphinx/static/* doc/_static
	cp -R doc_template/aibs_sphinx/templates/* doc/_templates
ifdef STATIC
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" doc/_templates/layout.html
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" doc/_templates/portalHeader.html
	sed -i --expression "s/\/_static\/external_assets/${STATIC}\/external_assets/g" doc/_templates/portalFooter.html
endif
	cd doc && make html || true

FORCE:

clean:
	rm -rf $(DISTDIR)
	rm -rf $(BUILDDIR)
	rm -rf $(RELEASEDIR)
	rm -rf $(EGGINFODIR)
	rm -rf $(DOCDIR)
