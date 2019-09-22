.PHONY: clean wheel install tests check_version dist check_dist upload_test upload dev_tools bump bump_ext release

NO_COLOR = \x1b[0m
OK_COLOR = \x1b[32;01m
ERROR_COLOR = \x1b[31;01m

PYCACHE := $(shell find . -name '__pycache__')
EGGS := $(wildcard *.egg-info)
CURRENT_VERSION := $(shell awk '/current_version/ {print $$3}' .bumpversion.cfg)

clean:
	@echo "$(OK_COLOR)=> Cleaning$(NO_COLOR)"
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
	bumpversion $(part) && grep current setup.cfg
endif
else
	@echo "$(ERROR_COLOR)Provide part=major|minor|patch|release|build and optionally version=x.y.z...$(NO_COLOR)"
	exit 1
endif

bump_ext:
ifdef part
	$(eval cur_version=$(shell cd js/ && npm version $(part) --preid=rc))
else
ifdef version
	$(eval cur_version := $(shell cd js/ && npm version $(version)))
else
	@echo "$(ERROR_COLOR)Provide part=major|minor|patch|premajor|preminor|prepatch|prerelease or version=x.y.z...$(NO_COLOR)"
	exit 1
endif
endif
	@echo "$(OK_COLOR)=> New version: $(cur_version:v%=%)$(NO_COLOR)"
	@sed -i.bak 's|databrickslabs-jupyterlab-statusbar@.*|databrickslabs-jupyterlab-statusbar@$(cur_version)|' labextensions.txt
	cat labextensions.txt
	git add labextensions.txt extensions/databrickslabs_jupyterlab_statusbar/package.json
	git commit -m "extension release $(cur_version)"

# Dist commands

dist:
	@python setup.py sdist bdist_wheel

release:
	git add .
	git status
	git commit -m "Latest release: $(CURRENT_VERSION)"
	git tag -a v$(CURRENT_VERSION) -m "Latest release: $(CURRENT_VERSION)"

install:
	@echo "$(OK_COLOR)=> Installing jupyter_cadquery$(NO_COLOR)"
	@pip install --upgrade .

check_dist:
	@twine check dist/*

upload:
	@twine upload dist/*

upload_ext:
	cd js && npm publish

# dev tools

dev_tools:
	pip install twine bumpversion yapf pylint pyYaml

