help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

#########################
# Data Preparation
#########################

DATA_FOLDER := data

$(DATA_FOLDER):
	mkdir $@

# Extract metadata

## SZTE ##########

SZTE_METADATA_FOLDER := $(DATA_FOLDER)/szte-metadata

$(SZTE_METADATA_FOLDER): $(DATA_FOLDER)
	mkdir $@

SZTE_METADATA_OUTPUTS := $(shell echo $(SZTE_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(SZTE_METADATA_OUTPUTS): SZTE/index.xml $(SZTE_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py szte-index all $< $(SZTE_METADATA_OUTPUTS)

	make $(SZTE_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(SZTE_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(SZTE_METADATA_FOLDER)/videos.csv: SZTE/video $(SZTE_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py szte-videos merged SZTE/video > $@

szte: $(SZTE_METADATA_OUTPUTS) $(SZTE_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTE

.PHONY: szte

szte-clean:  ## clean szte-metadata folder
	-rm $(SZTE_METADATA_FOLDER)/*
	-rmdir $(SZTE_METADATA_FOLDER)

.PHONY: szte-clean


## SZTR ##########

SZTR_METADATA_FOLDER := $(DATA_FOLDER)/sztr-metadata

$(SZTR_METADATA_FOLDER): $(DATA_FOLDER)
	-mkdir $@

SZTR_METADATA_OUTPUTS := $(shell echo $(SZTR_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(SZTR_METADATA_OUTPUTS): SZTR/index.xml $(SZTR_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py sztr-index all $< $(SZTR_METADATA_OUTPUTS)

	make $(SZTR_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(SZTR_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(SZTR_METADATA_FOLDER)/videos.csv: SZTR/video $(SZTR_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py sztr-videos ffprobe SZTR/video > $@


sztr: $(SZTR_METADATA_OUTPUTS) $(SZTR_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTR

.PHONY: sztr



### Extra to extract SZTR/SZTR.mdb
HAS_MDB_TOOLS := $(shell if which -s mdb-tables && which -s mdb-export; then echo "OK"; fi)

ifneq ($(strip $(HAS_MDB_TOOLS)),)
$(SZTR_METADATA_FOLDER)/mdb: SZTR/SZTR.mdb $(SZTR_METADATA_FOLDER)
	mkdir $@

SZTR_MDB_TABLES := $(shell mdb-tables --single-column SZTR/SZTR.mdb | awk '{ print  "$(SZTR_METADATA_FOLDER)/mdb/" $$1 ".csv"}' | xargs)

$(SZTR_MDB_TABLES): SZTR/SZTR.mdb $(SZTR_METADATA_FOLDER)/mdb
	mdb-export $< $(shell basename $@ .csv) > $@

sztr-mdb: $(SZTR_MDB_TABLES)  ## export tables from mdb file
else
sztr-mdb:
	echo "Missing mdb-tables and mdb-export CLI tools: https://github.com/mdbtools/mdbtools/"
endif

.PHONE: sztr-mdb



sztr-clean:  ## clean sztr-metadata folder
	-rm $(SZTR_METADATA_FOLDER)/*
	-rmdir $(SZTR_METADATA_FOLDER)

.PHONY: sztr-clean


###################
## ILIDS ##########
## Produce a merged result (and keep only what both SZTE and SZTR can produce as
## they aren't structured the same way)

ILIDS_METADATA_FOLDER := $(DATA_FOLDER)/ilids-metadata

$(ILIDS_METADATA_FOLDER): $(DATA_FOLDER)
	-mkdir $@

ILIDS_METADATA_OUTPUTS := $(shell echo $(ILIDS_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(ILIDS_METADATA_OUTPUTS): SZTE/index.xml SZTR/index.xml $(ILIDS_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py ilids-indexes all SZTE/index.xml SZTR/index.xml $(ILIDS_METADATA_OUTPUTS)
	make $(ILIDS_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(ILIDS_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(ILIDS_METADATA_FOLDER)/videos.csv: SZTE/video SZTR/video $(ILIDS_METADATA_FOLDER)
	poetry run python scripts/extract_metadata.py ilids-videos ffprobe SZTE/video SZTR/video > $@

ilids: $(ILIDS_METADATA_OUTPUTS) $(ILIDS_METADATA_FOLDER)/videos.csv  ## extract all metadata of ILIDS

.PHONY: ilids

ilids-clean:  ## clean ilids-metadata folder
	-rm $(ILIDS_METADATA_FOLDER)/*
	-rmdir $(ILIDS_METADATA_FOLDER)

.PHONY: ilids-clean


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