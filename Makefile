.PHONY: clean wheel install tests check_version dist check_dist upload_test upload bump release docker docker_upload

PYCACHE := $(shell find . -name '__pycache__')
EGGS := $(wildcard *.egg-info)
CURRENT_VERSION := $(shell awk '/current_version/ {print $$3}' setup.cfg)

clean:
	@echo "=> Cleaning"
	@rm -fr build dist $(EGGS) $(PYCACHE)

prepare: clean
	git add .
	git status
	git commit -m "cleanup before release"

# Version commands

bump:
ifdef part
ifdef version
	bumpversion --new-version $(version) $(part) && grep current setup.cfg
else
	bumpversion --allow-dirty $(part) && grep current setup.cfg
endif
else
	@echo "Provide part=major|minor|patch|release|build and optionally version=x.y.z..."
	exit 1
endif

# Dist commands

dist:
	@rm dist/*
	@python setup.py sdist bdist_wheel
	@echo "jupyter-labextension install --no-build $(shell cat labextensions.txt | xargs)" > postBuild
	@echo "jupyter lab build --dev-build=False --minimize=False" >> postBuild

release:
	git add .
	git status
	git commit -m "Latest release: $(CURRENT_VERSION)" && echo ""
	git tag -a v$(CURRENT_VERSION) -m "Latest release: $(CURRENT_VERSION)"

install: dist
	@echo "=> Installing jupyter_cadquery"
	@pip install --upgrade .

check_dist:
	@twine check dist/*

upload:
	@twine upload dist/*

docker:
	@rm -fr docker/examples
	@cp -R examples docker/
	@cd docker && docker build -t bwalter42/jupyter_cadquery:$(CURRENT_VERSION) .
	@rm -fr docker/examples

upload_docker: 
	@docker push bwalter42/jupyter_cadquery:$(CURRENT_VERSION)