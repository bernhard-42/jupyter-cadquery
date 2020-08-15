.PHONY: clean wheel install tests check_version dist check_dist upload_test upload dev_tools bump bump_ext release docker docker_upload

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
	bumpversion $(part) && grep current setup.cfg
endif
else
	@echo "Provide part=major|minor|patch|release|build and optionally version=x.y.z..."
	exit 1
endif

bump_ext:
ifdef part
	$(eval cur_version=$(shell cd js/ && npm version $(part) --preid=rc))
else
ifdef version
	$(eval cur_version := $(shell cd js/ && npm version $(version)))
else
	@echo "Provide part=major|minor|patch|premajor|preminor|prepatch|prerelease or version=x.y.z..."
	exit 1
endif
endif
	@echo "=> New version: $(cur_version:v%=%)"
	@sed -i.bak 's|jupyter_cadquery@.*|jupyter_cadquery@$(cur_version)|' labextensions.txt
	@sed -i.bak 's|__npm_version__.*|__npm_version__ = "$(cur_version)"|' jupyter_cadquery/_version.py
	@sed -i.bak 's|_model_module_version:.*|_model_module_version: "$(cur_version)",|' js/lib/tree_view.js
	@sed -i.bak 's|_view_module_version:.*|_view_module_version: "$(cur_version)",|' js/lib/tree_view.js
	@sed -i.bak 's|_model_module_version:.*|_model_module_version: "$(cur_version)",|' js/lib/image_button.js
	@sed -i.bak 's|_view_module_version:.*|_view_module_version: "$(cur_version)",|' js/lib/image_button.js
	@rm labextensions.txt.bak jupyter_cadquery/_version.py.bak js/lib/tree_view.js.bak js/lib/image_button.js.bak
	cat labextensions.txt
	git add labextensions.txt js/package.json js/package-lock.json jupyter_cadquery/_version.py js/lib/tree_view.js js/lib/image_button.js
	git commit -m "extension release $(cur_version)"

# Dist commands

dist:
	@python setup.py sdist bdist_wheel
	@echo "jupyter-labextension install --no-build $(shell cat labextensions.txt | xargs)" > postBuild
	@echo "jupyter lab build" >> postBuild

release:
	git add .
	git status
	git commit -m "Latest release: $(CURRENT_VERSION)"
	git tag -a v$(CURRENT_VERSION) -m "Latest release: $(CURRENT_VERSION)"

install: dist
	@echo "=> Installing jupyter_cadquery"
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

docker:
	@rm -fr docker/examples
	@rm -f docker/environment.yml docker/labextensions.txt
	@cp environment.yml labextensions.txt docker/
	@cd docker && docker build -t bwalter42/jupyter_cadquery:$(CURRENT_VERSION) .
	@rm -f docker/environment.yml docker/labextensions.txt

upload_docker: docker
	@docker push bwalter42/jupyter_cadquery:$(CURRENT_VERSION)