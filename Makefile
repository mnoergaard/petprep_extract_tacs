# Quickly run black on all python files in this repository, local version of the pre-commit hook
black:
	@for file in `find . -name "*.py"`; do \
		black $$file; \
	done

lint: black
	echo "Checking actions too"
	actionlint .github/workflows/*

# install python dependencies
pythondeps:
	pip install --upgrade pip && pip install  -e .

# create petdafec docker image with tag (petdeface:X.X.X) from toml file by using cat and grep to 
# extract the project name from the pyproject.toml file

USE_LOCAL_FREESURFER ?= False
dockerbuild:
	docker build --build-arg="USE_LOCAL_FREESURFER=$(USE_LOCAL_FREESURFER)" -t openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):$(shell cat pyproject.toml | grep version | head -n 1 | cut -d '"' -f 2) .
	docker build --build-arg="USE_LOCAL_FREESURFER=$(USE_LOCAL_FREESURFER)" -t openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):latest .

dockerpush: dockerbuild
	docker push openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):$(shell cat pyproject.toml | grep version | head -n 1 | cut -d '"' -f 2)
	docker push openneuropet/$(shell cat pyproject.toml | grep name | cut -d '"' -f 2):latest
