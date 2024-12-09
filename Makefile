# Quickly run black on all python files in this repository, local version of the pre-commit hook
black:
	@for file in `find . -name "*.py"`; do \
		black $$file; \
	done

check-black:
	black --check . --exclude="dist/*" --exclude="build/*" --exclude="docs/*";

# install python dependencies
pythondeps:
	pip install --upgrade pip && pip install  -e .

# create petdafec docker image with tag (petdeface:X.X.X) from toml file by using cat and grep to 
# extract the project name from the pyproject.toml file

USE_LOCAL_FREESURFER ?= False
dockerbuild:
	docker build --build-arg="USE_LOCAL_FREESURFER=$(USE_LOCAL_FREESURFER)" -t martinnoergaard$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):$(shell cat pyproject.toml | grep version | head -n 1 | cut -d '"' -f 2) .
	docker build --build-arg="USE_LOCAL_FREESURFER=$(USE_LOCAL_FREESURFER)" -t martinnoergaard/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):latest .

dockerpush: dockerbuild
	docker push openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):$(shell cat pyproject.toml | grep version | head -n 1 | cut -d '"' -f 2)
	docker push openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):latest

.PHONY: docs
docs:
	poetry run sphinx-build -b html docs docs/_build/html

.PHONY: docs-serve
docs-serve:
	poetry run sphinx-autobuild docs docs/_build/html

# runs github actions ci locally using nektos/act
# needs to be installed with brew install act on mac
# install instructions for other platforms can be found here:
# https://nektosact.com/installation/index.html
ci:
	act push