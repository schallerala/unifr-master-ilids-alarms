help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

#########################
# Data Preparation
#########################

# Extract metadata


SZTE_METADATA_FOLDER := szte-metadata

$(SZTE_METADATA_FOLDER):
	-mkdir $@

## SZTE ##########

SZTE_METADATA_OUTPUTS := $(shell echo $(SZTE_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(SZTE_METADATA_OUTPUTS): SZTE/index.xml $(SZTE_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py szte-index all $< $(SZTE_METADATA_OUTPUTS)
	make $(SZTE_METADATA_FOLDER)/videos.csv

# $(SZTE_METADATA_FOLDER)/clips.csv: SZTE/index.xml $(SZTE_METADATA_FOLDER)
# 	poetry run python scripts/extract_metadata.py szte-index clips SZTE/index.xml > $@

# $(SZTE_METADATA_FOLDER)/alarms.csv: SZTE/index.xml $(SZTE_METADATA_FOLDER)
# 	poetry run python scripts/extract_metadata.py szte-index alarms SZTE/index.xml > $@

# $(SZTE_METADATA_FOLDER)/distractions.csv: SZTE/index.xml $(SZTE_METADATA_FOLDER)
# 	poetry run python scripts/extract_metadata.py szte-index distractions SZTE/index.xml > $@

# $(SZTE_METADATA_FOLDER)/meta.json: SZTE/index.xml $(SZTE_METADATA_FOLDER)
# 	poetry run python scripts/extract_metadata.py szte-index meta SZTE/index.xml > $@

$(SZTE_METADATA_FOLDER)/videos.csv: SZTE/video $(SZTE_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py szte-videos merged SZTE/video > $@


szte: $(SZTE_METADATA_OUTPUTS) $(SZTE_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTE

.PHONY: szte

szte-clean:  ## clean szte-metadata folder
	rm $(SZTE_METADATA_FOLDER)/*
	rmdir $(SZTE_METADATA_FOLDER)

.PHONY: szte-clean


#########################
# Build & Install Decord
#########################

DECORD_CMAKE_USER_CUDA := $(shell if which -s nvcc; then echo "ON"; else echo "0"; fi)

build:
	-mkdir $@

build/decord: build
	test -d $@ || git clone --recursive https://github.com/schallerala/decord $@

build/decord/build: build/decord
	test -d $@ || mkdir $@
	@# https://github.com/dmlc/decord
	cd $@ && cmake .. -DUSE_CUDA=$(DECORD_CMAKE_USER_CUDA) -DCMAKE_BUILD_TYPE=Release

clean-decord:  ## clean everything related to decord and remove it from the depencendies
	-rm -rf build/decord
	-poetry remove decord

.PHONY: clean-decord

install-decord:  ## clone, build and add decord's dependency to the poetry project
	make build/decord/build
	cd build/decord/build && make
	cd build/decord/python && make clean && make build-wheel
	poetry add build/decord/python/decord*.whl

.PHONY: install-decord