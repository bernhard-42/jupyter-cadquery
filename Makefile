.PHONY: clean_notebooks wheel install tests check_version dist check_dist upload_test upload bump release create-release docker docker_upload

PYCACHE := $(shell find . -name '__pycache__')
EGGS := $(wildcard *.egg-info)
CURRENT_VERSION := $(shell awk '/current_version = / {print $$3}' pyproject.toml)

# https://github.com/jupyter/nbconvert/issues/637

JQ_RULES := '(.cells[] | select(has("outputs")) | .outputs) = [] \
| (.cells[] | select(has("execution_count")) | .execution_count) = null \
| .metadata = { \
	"language_info": {"name":"python", "pygments_lexer": "ipython3"}, \
	"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"} \
} \
| .cells[].metadata = {}'

clean_notebooks: ./examples/*.ipynb ./examples/assemblies/*.ipynb
	@for file in $^ ; do \
		echo "$${file}" ; \
		jq --indent 1 $(JQ_RULES) "$${file}" > "$${file}_clean"; \
		mv "$${file}_clean" "$${file}"; \
		python validate_nb.py "$${file}"; \
	done

clean: clean_notebooks
	@echo "=> Cleaning"
	@rm -fr build dist $(EGGS) $(PYCACHE)

prepare: clean
	git add .
	git status
	git commit -m "cleanup before release"

# Version commands

bump:
	@echo Current version: $(CURRENT_VERSION)
ifdef part
	bump-my-version bump $(part) --allow-dirty && grep current pyproject.toml
else ifdef version
	bump-my-version bump --allow-dirty --new-version $(version) && grep current pyproject.toml
else
	@echo "Provide part=major|minor|patch|release|build and optionally version=x.y.z..."
	exit 1
endif

# Dist commands

# `uv build` resolves the build backend (hatchling, hatch-jupyter-builder)
# in an isolated environment of its own, so the active env needs neither.
# `python -m build -n` wanted them installed wherever it ran.
dist:
	@rm -f dist/*
	@uv build

release:
	git add .
	git status
	git diff-index --quiet HEAD || git commit -m "Latest release: $(CURRENT_VERSION)"
	git tag -a v$(CURRENT_VERSION) -m "Latest release: $(CURRENT_VERSION)"
	
# Push, then a GitHub release under the tag `release` made, carrying what
# PyPI got. Both files must exist in dist/ - `make dist` builds them - or
# nothing is pushed. No `--target`: the tag exists and names the commit.
create-release:
	@for f in dist/jupyter_cadquery-$(CURRENT_VERSION)-py3-none-any.whl \
	         dist/jupyter_cadquery-$(CURRENT_VERSION).tar.gz; do \
	    test -f $$f || { echo "missing $$f - run make dist first"; exit 1; }; \
	done
	@git push
	@git push --tags
	@gh release create v$(CURRENT_VERSION) \
	    "dist/jupyter_cadquery-$(CURRENT_VERSION)-py3-none-any.whl#jupyter_cadquery $(CURRENT_VERSION) - wheel (PyPI)" \
	    "dist/jupyter_cadquery-$(CURRENT_VERSION).tar.gz#jupyter_cadquery $(CURRENT_VERSION) - source (PyPI)" \
	    --title "jupyter_cadquery $(CURRENT_VERSION)" \
	    --notes "jupyter_cadquery $(CURRENT_VERSION) on PyPI. See CHANGELOG.md."

install: dist
	@echo "=> Installing jupyter_cadquery"
	@pip install --upgrade .

check_dist:
	@twine check dist/*

upload:
	@twine upload dist/*

docker:
	@rm -fr docker/examples docker/requirements.txt
	@cp -R examples requirements.txt docker/
	@cd docker && docker build -t bwalter42/jupyter_cadquery:$(CURRENT_VERSION) .
	@rm -fr docker/examples docker/requirements.txt
	
upload_docker: 
	@docker push bwalter42/jupyter_cadquery:$(CURRENT_VERSION)
