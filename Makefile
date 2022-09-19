help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

.PHONY: help


#########################
# Data Preparation
#########################

DATA_FOLDER := data

$(DATA_FOLDER):
	mkdir $@


# Extract metadata from *intermediate*
######################################

## SZTE ##########

SZTE_METADATA_FOLDER := $(DATA_FOLDER)/szte-metadata

$(SZTE_METADATA_FOLDER): | $(DATA_FOLDER)
	-mkdir $@

SZTE_METADATA_OUTPUTS := $(shell echo $(SZTE_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(SZTE_METADATA_OUTPUTS) &:: data/SZTE/index.xml | $(SZTE_METADATA_FOLDER)
	poetry run ilids_cmd szte index all $< $(SZTE_METADATA_OUTPUTS)

	make $(SZTE_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(SZTE_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(SZTE_METADATA_FOLDER)/videos.csv: data/SZTE/video | $(SZTE_METADATA_FOLDER)
	poetry run ilids_cmd szte videos merged data/SZTE/video > $@

szte: $(SZTE_METADATA_OUTPUTS) $(SZTE_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTE

.PHONY: szte

szte-clean:  ## clean szte-metadata folder
	-rm $(SZTE_METADATA_FOLDER)/*
	-rmdir $(SZTE_METADATA_FOLDER)

.PHONY: szte-clean


## SZTR ##########

SZTR_METADATA_FOLDER := $(DATA_FOLDER)/sztr-metadata

$(SZTR_METADATA_FOLDER): | $(DATA_FOLDER)
	mkdir $@

SZTR_METADATA_OUTPUTS := $(shell echo $(SZTR_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(SZTR_METADATA_OUTPUTS) &:: data/SZTR/index.xml | $(SZTR_METADATA_FOLDER)
	poetry run ilids_cmd sztr index all $< $(SZTR_METADATA_OUTPUTS)

	make $(SZTR_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(SZTR_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(SZTR_METADATA_FOLDER)/videos.csv: data/SZTR/video | $(SZTR_METADATA_FOLDER)
	poetry run ilids_cmd sztr videos ffprobe data/SZTR/video > $@


sztr: $(SZTR_METADATA_OUTPUTS) $(SZTR_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTR

.PHONY: sztr



### Extra to extract data/SZTR/SZTR.mdb
HAS_MDB_TOOLS := $(shell if which -s mdb-tables && which -s mdb-export; then echo "OK"; fi)

ifneq ($(strip $(HAS_MDB_TOOLS)),)
$(SZTR_METADATA_FOLDER)/mdb: data/SZTR/SZTR.mdb | $(SZTR_METADATA_FOLDER)
	-mkdir $@

SZTR_MDB_TABLES := $(shell mdb-tables --single-column data/SZTR/SZTR.mdb | awk '{ print  "$(SZTR_METADATA_FOLDER)/mdb/" $$1 ".csv"}' | xargs)

$(SZTR_MDB_TABLES): data/SZTR/SZTR.mdb | $(SZTR_METADATA_FOLDER)/mdb
	mdb-export $< $(patsubst %.csv,%,$(@F)) > $@

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

$(ILIDS_METADATA_FOLDER): | $(DATA_FOLDER)
	mkdir $@

ILIDS_METADATA_OUTPUTS := $(shell echo $(ILIDS_METADATA_FOLDER)/{meta.json,clips.csv,alarms.csv,distractions.csv})

$(ILIDS_METADATA_OUTPUTS) &:: data/SZTE/index.xml data/SZTR/index.xml | $(ILIDS_METADATA_FOLDER)
	poetry run ilids_cmd ilids indexes all data/SZTE/index.xml data/SZTR/index.xml $(ILIDS_METADATA_OUTPUTS)
	make $(ILIDS_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(shell echo $(ILIDS_METADATA_FOLDER)/*); do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(ILIDS_METADATA_FOLDER)/videos.csv: data/SZTE/video data/SZTR/video | $(ILIDS_METADATA_FOLDER)
	poetry run ilids_cmd ilids videos ffprobe data/SZTE/video data/SZTR/video > $@

ilids: $(ILIDS_METADATA_OUTPUTS) $(ILIDS_METADATA_FOLDER)/videos.csv  ## extract all metadata of ILIDS

.PHONY: ilids

ilids-clean:  ## clean ilids-metadata folder
	-rm $(ILIDS_METADATA_FOLDER)/*
	-rmdir $(ILIDS_METADATA_FOLDER)

.PHONY: ilids-clean


###################
## TP/FP ##########
## Produce sequences of video to feed into a model

HANDCRAFTED_METADATA_FOLDER := $(DATA_FOLDER)/handcrafted-metadata

$(HANDCRAFTED_METADATA_FOLDER): | $(DATA_FOLDER)
	mkdir $@

scripts/generate-sequences-alarms-FP.py: notebooks/generate-sequences-alarms-FP.ipynb
	poetry run jupyter nbconvert notebooks/generate-sequences-alarms-FP.ipynb --stdout --to python > $@


$(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv: scripts/generate-sequences-alarms-FP.py $(HANDCRAFTED_METADATA_FOLDER)/szte_distractions.extended.corrected.csv $(ILIDS_METADATA_FOLDER)/alarms.csv $(ILIDS_METADATA_FOLDER)/clips.csv $(ILIDS_METADATA_FOLDER)/videos.csv | $(HANDCRAFTED_METADATA_FOLDER)
	@# as the paths are hardcoded in the jupyter notebook, need to mimic the same paths
	@# by changing to the scripts directory
	cd scripts && poetry run python generate-sequences-alarms-FP.py


sequences: $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv  ## produce sequences of short clips to feed into a model

.PHONY: sequences

sequences-clean:
	rm $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv

.PHONY: sequences-clean


#########################
## SEQUENCES
## Extract all sequences from TP FP generation from above
## (make sequnces must have been run eariler on)

### Ease pattern matching by "gathering" all videos in a single folder with symbolic links
VIDEOS_SYMLINK_TARGET_FOLDER := $(DATA_FOLDER)/videos

$(VIDEOS_SYMLINK_TARGET_FOLDER): | $(DATA_FOLDER)
	mkdir $@

ifeq (,$(wildcard $(ILIDS_METADATA_FOLDER)/videos.csv))
symlink-videos:
	$(warning All i-LIDS metadata not extracted yet)
else
# i-LIDS videos.csv exists
ALL_VIDEOS := $(shell awk -F',' 'NR > 1 && $$1 { print "data/" $$1 }' $(ILIDS_METADATA_FOLDER)/videos.csv)

ALL_VIDEOS_SYMLINK_SZTE := $(patsubst data/SZTE/video/%,$(VIDEOS_SYMLINK_TARGET_FOLDER)/%,$(filter data/SZTE/%,$(ALL_VIDEOS)))
ALL_VIDEOS_SYMLINK_SZTR := $(patsubst data/SZTR/video/%,$(VIDEOS_SYMLINK_TARGET_FOLDER)/%,$(filter data/SZTR/%,$(ALL_VIDEOS)))

# Matches all SZTE files
$(VIDEOS_SYMLINK_TARGET_FOLDER)/SZTE%.mov: $(DATA_FOLDER)/SZTE/video/SZTE%.mov | $(VIDEOS_SYMLINK_TARGET_FOLDER)
	cd $(dir $@) && ln -s $(patsubst data/%,../%,$<) $(@F)
# Matches all SZTR files
$(VIDEOS_SYMLINK_TARGET_FOLDER)/SZTR%.mov: $(DATA_FOLDER)/SZTR/video/SZTR%.mov | $(VIDEOS_SYMLINK_TARGET_FOLDER)
	cd $(dir $@) && ln -s $(patsubst data/%,../%,$<) $(@F)

symlink-videos: $(ALL_VIDEOS_SYMLINK_SZTE) $(ALL_VIDEOS_SYMLINK_SZTR)
endif

.PHONY: symlink-videos

######################
### Proper extraction of sequences

SEQUENCES_TARGET_FOLDER := $(DATA_FOLDER)/sequences

$(SEQUENCES_TARGET_FOLDER): | $(DATA_FOLDER)
	mkdir $@

ifeq (,$(wildcard $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv))
# File doesn't exist yet
extract-all-sequences:
	$(error '$(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv' doesn't exist yet, run 'make sequences' first)
else

# Field 1 is the output file
ALL_SEQUENCES_FILES := $(shell awk -F',' 'NR > 1 && $$1 { print "$(SEQUENCES_TARGET_FOLDER)/" $$1 }' $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv)

.SECONDEXPANSION:

# Gets $(1): %.mov -> SZTEA101a_00_02_42.mov
# returns SZTEA101a.mov
define give_requirement_without_start_time
$(shell echo $(1) | sed -E 's/(_[0-9]{2}){3}//')
endef

$(SEQUENCES_TARGET_FOLDER)/%.mov: data/videos/$$(call give_requirement_without_start_time,$$(@F)) $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv | $(SEQUENCES_TARGET_FOLDER)
	@# -m1: stop reading a file after 1 matching line
	@grep -m1 '$(@F)' $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv | \
	awk -F',' '{ print "data/" $$2 " " $$3 " " $$4 " 12 -o $@" }' | tee /dev/stderr | \
	xargs -L 1 poetry run ilids_cmd videos frames extract

extract-all-sequences: $(ALL_SEQUENCES_FILES)
endif

.PHONY: extract-all-sequences

#########################
# Build & Install Decord
#########################

DECORD_CMAKE_USER_CUDA := $(shell if which -s nvcc; then echo "ON"; else echo "0"; fi)

ifeq ($(OS),Windows_NT)
    # CCFLAGS += -D WIN32
    # ifeq ($(PROCESSOR_ARCHITEW6432),AMD64)
    #     CCFLAGS += -D AMD64
    # else
    #     ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
    #         CCFLAGS += -D AMD64
    #     endif
    #     ifeq ($(PROCESSOR_ARCHITECTURE),x86)
    #         CCFLAGS += -D IA32
    #     endif
    # endif
$(error Windows isn't supported to install Decord)
else
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Darwin)
        DECORD_CMAKE_FLAGS :=
    endif
    ifeq ($(UNAME_S),Linux)
        DECORD_CMAKE_FLAGS := -DUSE_CUDA=$(DECORD_CMAKE_USER_CUDA)
    endif
endif


build:
	-mkdir $@

build/decord: build
	test -d $@ || git clone --recursive https://github.com/schallerala/decord $@

build/decord/build: build/decord
	test -d $@ || mkdir $@
	@# https://github.com/dmlc/decord
	cd $@ && cmake .. $(DECORD_CMAKE_FLAGS) -DCMAKE_BUILD_TYPE=Release

clean-decord:  ## clean everything related to decord and remove it from the depencendies
	-rm -rf build/decord
	-poetry remove decord

.PHONY: clean-decord

install-decord:  ## clone, build and add decord's dependency to the poetry project
	make build/decord/build
	cd build/decord/build && make
	cd build/decord/python && make clean && make build-wheel
	poetry add build/decord/python

.PHONY: install-decord




#########################
# Utils
#########################

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
cpu_count:
	@sysctl -n hw.ncpu
endif
ifeq ($(UNAME_S),Linux)
cpu_count:
	@nproc
endif

.PHONY: cpu_count
