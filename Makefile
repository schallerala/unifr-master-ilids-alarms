help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

.PHONY: help


#########################
# Utility Variables
#########################


## Has GPUs and if yes, how many?
HAS_NVIDIA_SMI_CMD := $(shell if which nvidia-smi > /dev/null; then echo "YES"; fi)

ifneq ($(HAS_NVIDIA_SMI_CMD),)
GPU_COUNT := $(shell nvidia-smi --query-gpu=count --format=csv,noheader | wc -l)
else
GPU_COUNT := 12
endif


# Used in case want to run multiple experiment on different GPUs in parallel
SHARE_GPU_SERVER_PORT := 9084


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

SZTE_METADATA_OUTPUTS := $(addprefix $(SZTE_METADATA_FOLDER)/,meta.json clips.csv alarms.csv distractions.csv)

$(SZTE_METADATA_OUTPUTS) &:: data/SZTE/index.xml | $(SZTE_METADATA_FOLDER)
	poetry run ilids_cmd szte index all $< $(SZTE_METADATA_OUTPUTS)

	make $(SZTE_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(SZTE_METADATA_FOLDER)/*; do \
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

SZTR_METADATA_OUTPUTS := $(addprefix $(SZTR_METADATA_FOLDER)/,meta.json clips.csv alarms.csv distractions.csv)

$(SZTR_METADATA_OUTPUTS) &:: data/SZTR/index.xml | $(SZTR_METADATA_FOLDER)
	poetry run ilids_cmd sztr index all $< $(SZTR_METADATA_OUTPUTS)

	make $(SZTR_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(SZTR_METADATA_FOLDER)/*; do \
		sed -i '' 's/\.qtl/\.mov/g' $$file; \
	done

$(SZTR_METADATA_FOLDER)/videos.csv: data/SZTR/video | $(SZTR_METADATA_FOLDER)
	poetry run ilids_cmd sztr videos ffprobe data/SZTR/video > $@


sztr: $(SZTR_METADATA_OUTPUTS) $(SZTR_METADATA_FOLDER)/videos.csv  ## extract all metadata of SZTR

.PHONY: sztr



### Extra to extract data/SZTR/SZTR.mdb
HAS_MDB_TOOLS := $(shell if which mdb-tables > /dev/null && which mdb-export > /dev/null; then echo "OK"; fi)

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

ILIDS_METADATA_OUTPUTS := $(addprefix $(ILIDS_METADATA_FOLDER)/,meta.json clips.csv alarms.csv distractions.csv)

$(ILIDS_METADATA_OUTPUTS) &:: data/SZTE/index.xml data/SZTR/index.xml | $(ILIDS_METADATA_FOLDER)
	poetry run ilids_cmd ilids indexes all data/SZTE/index.xml data/SZTR/index.xml $(ILIDS_METADATA_OUTPUTS)
	make $(ILIDS_METADATA_FOLDER)/videos.csv

	# correct video extension to .mov as in the index.xml, they reference videos with .qtl
	for file in $(ILIDS_METADATA_FOLDER)/*; do \
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

$(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv: notebooks/generate-sequences-alarms-FP.ipynb $(HANDCRAFTED_METADATA_FOLDER)/szte_distractions.extended.corrected.csv $(ILIDS_METADATA_FOLDER)/alarms.csv $(ILIDS_METADATA_FOLDER)/clips.csv $(ILIDS_METADATA_FOLDER)/videos.csv | $(HANDCRAFTED_METADATA_FOLDER)
	@# as the paths are hardcoded in the jupyter notebook, need to mimic the same paths
	@# by changing to the notebooks directory
	cd notebooks && poetry run papermill --progress-bar $(notdir $<) - > /dev/null


sequences: $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv  ## produce sequences of short clips to feed into a model

.PHONY: sequences


# Adapt source of truth for actionclip processing
$(HANDCRAFTED_METADATA_FOLDER)/actionclip_sequences.csv: scripts/generate_data_sequences_actionclip_list_file.py $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv | $(HANDCRAFTED_METADATA_FOLDER)
	poetry run python scripts/generate_data_sequences_actionclip_list_file.py data/handcrafted-metadata/tp_fp_sequences.csv $@ 25 data/sequences 12


#########################
## SEQUENCES
## Extract all sequences from TP FP generation from above
## (make sequnces must have been run eariler on)

### Ease pattern matching by "gathering" all videos in a single folder with symbolic links
VIDEOS_SYMLINK_TARGET_FOLDER := $(DATA_FOLDER)/symlink-videos

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

$(SEQUENCES_TARGET_FOLDER)/%.mov: $(VIDEOS_SYMLINK_TARGET_FOLDER)/$$(call give_requirement_without_start_time,$$(@F)) $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv | $(SEQUENCES_TARGET_FOLDER)
	@# -m1: stop reading a file after 1 matching line
	@grep -m1 '$(@F)' $(HANDCRAFTED_METADATA_FOLDER)/tp_fp_sequences.csv | \
	awk -F',' '{ print "data/" $$2 " " $$3 " " $$4 " 12 -o $@" }' | \
	xargs -L 1 poetry run ilids_cmd videos frames extract

extract-all-sequences: $(ALL_SEQUENCES_FILES)
endif

.PHONY: extract-all-sequences



#########################
# checkpoints
#########################

CHECKPOINTS_FOLDER := ckpt


$(CHECKPOINTS_FOLDER):
	mkdir $@


# ActionClip


ACTIONCLIP_CHECKPOINT_FOLDER := $(CHECKPOINTS_FOLDER)/actionclip


$(ACTIONCLIP_CHECKPOINT_FOLDER): | $(CHECKPOINTS_FOLDER)
	mkdir $@


# Intermediate util to list checkpoints
list-actionclip-checkpoints:
ifeq ($(strip $(shell which gdrive > /dev/null && echo "has gdrive cli")),)
	$(error Expected to list the checkpoints from Google Drive using the 'gdrive' command. Install it first from https://github.com/prasmussen/gdrive)
else
	$(info using the Google Drive link in README.md of https://github.com/sallymmx/ActionCLIP)
	gdrive list --query "'1qs5SzQIl__qo2x9h0YudpGzHhNnPGqK6' in parents" | awk 'NR > 1 { print $$1 }' | xargs -L1 -I{} gdrive list --query "'{}' in parents" | awk 'NR == 1 || $$1 != "Id"'
endif

.PHONY: list-actionclip-checkpoints

# list produced with target 'list-actionclip-checkpoints'
ACTIONCLIP_CHECKPOINT_NAMES := vit-b-16-8f.pt vit-b-32-8f.pt vit-b-16-16f.pt vit-b-16-32f.pt
ACTIONCLIP_CHECKPOINTS := $(addprefix $(ACTIONCLIP_CHECKPOINT_FOLDER)/,$(ACTIONCLIP_CHECKPOINT_NAMES))

# list produced with target 'list-actionclip-checkpoints'
ACTIONCLIP_CHECKPOINTS_GDRIVE_ID := 1upZawWz_vbvzId8Jh_KWYiDu3EW7WkET 1cjDd1zFHmrNkAds30rBPH0MVgKJIk1y9 1_cZjE8NeC-1bMatVE1ydh3R2BH8HIR0R 1PLaNKiyI5VQoTZi_SG6mxgGDhi6rGoVK

$(ACTIONCLIP_CHECKPOINTS): | $(ACTIONCLIP_CHECKPOINT_FOLDER)
	poetry run gdown --output $@ $(call lookup,$(@F),$(ACTIONCLIP_CHECKPOINT_NAMES),$(ACTIONCLIP_CHECKPOINTS_GDRIVE_ID))


dl-all-checkpoints-actionclip: $(ACTIONCLIP_CHECKPOINTS)

.PHONY: dl-all-checkpoints-actionclip



#########################
# Features extraction
#########################

RESULTS_FOLDER := results


$(RESULTS_FOLDER):
	mkdir $@

# MoViNet
##########

MOVINET_MODEL_NAMES := movineta0 movineta1 movineta2 movineta3 movineta4 movineta5
MOVINET_RESULTS_FOLDER := $(RESULTS_FOLDER)/movinet

$(MOVINET_RESULTS_FOLDER): | $(RESULTS_FOLDER)
	mkdir $@

MOVINET_RESULTS_OUTPUT_SUFFIX := .pkl
MOVINET_FEATURES_TARGETS := $(addprefix $(MOVINET_RESULTS_FOLDER)/,$(addsuffix $(MOVINET_RESULTS_OUTPUT_SUFFIX),$(MOVINET_MODEL_NAMES)))

$(MOVINET_FEATURES_TARGETS): $(MOVINET_RESULTS_FOLDER)/%$(MOVINET_RESULTS_OUTPUT_SUFFIX): | $(MOVINET_RESULTS_FOLDER)
	poetry run ilids_cmd experiments movinet $* 'data/sequences/*.mov' $@

results-features-movinet: $(MOVINET_FEATURES_TARGETS)

.PHONY: results-features-movinet


# ActionCLIP
#############

# ACTIONCLIP_CHECKPOINT_NAMES := vit-b-16-8f.pt vit-b-32-8f.pt vit-b-16-16f.pt vit-b-16-32f.pt
ACTIONCLIP_MODEL_NAMES := $(subst .pt,,$(ACTIONCLIP_CHECKPOINT_NAMES))
ACTIONCLIP_FRAMES_TO_EXTRACT := 8 8 16 32
ACTIONCLIP_OPENAI_BASE_MODEL_NAMES := ViT-B-16 ViT-B-32 ViT-B-16 ViT-B-16
# ACTIONCLIP_CHECKPOINTS := ... Defined higher
ACTIONCLIP_RESULTS_FOLDER := $(RESULTS_FOLDER)/actionclip

$(ACTIONCLIP_RESULTS_FOLDER): | $(RESULTS_FOLDER)
	mkdir $@

ACTIONCLIP_RESULTS_OUTPUT_SUFFIX := .pkl
ACTIONCLIP_FEATURES_TARGETS := $(addprefix $(ACTIONCLIP_RESULTS_FOLDER)/,$(addsuffix $(ACTIONCLIP_RESULTS_OUTPUT_SUFFIX),$(ACTIONCLIP_MODEL_NAMES)))

# argument to parallize ACTIONCLIP_FEATURES_TARGETS
ifneq ($(GPU_COUNT),)
ACTIONCLIP_FEATURES_TARGETS_ARGS := --device-type cuda --distributed -h localhost -P $(SHARE_GPU_SERVER_PORT)
else
ACTIONCLIP_FEATURES_TARGETS_ARGS := --device-type cpu
endif

$(ACTIONCLIP_FEATURES_TARGETS): $(ACTIONCLIP_RESULTS_FOLDER)/%$(ACTIONCLIP_RESULTS_OUTPUT_SUFFIX): $(HANDCRAFTED_METADATA_FOLDER)/actionclip_sequences.csv | $(ACTIONCLIP_RESULTS_FOLDER) ilids.synchronization.share_gpu_command.lock
	poetry run ilids_cmd experiments actionclip $(call lookup,$*,$(ACTIONCLIP_MODEL_NAMES),$(ACTIONCLIP_OPENAI_BASE_MODEL_NAMES)) $(call lookup,$*,$(ACTIONCLIP_MODEL_NAMES),$(ACTIONCLIP_CHECKPOINTS)) $(HANDCRAFTED_METADATA_FOLDER)/actionclip_sequences.csv $(call lookup,$*,$(ACTIONCLIP_MODEL_NAMES),$(ACTIONCLIP_FRAMES_TO_EXTRACT)) $@ --notify $(ACTIONCLIP_FEATURES_TARGETS_ARGS)

results-features-actionclip: $(ACTIONCLIP_FEATURES_TARGETS)

.PHONY: results-features-actionclip


###### Utils for experiments

# Define it as a PHONY so it isn't required/called by the "child target"
spawn-share-gpu-server: ## spawn a sync server to give out GPUs with multiple jobs
ifeq ($(GPU_COUNT),)
	$(warning "Not possible to distribute GPUs, however, still running server for testing purposes!")
	poetry run ilids_sync --port $(SHARE_GPU_SERVER_PORT) --count 4
else
	poetry run ilids_sync --port $(SHARE_GPU_SERVER_PORT) --count $(GPU_COUNT)
endif

.PHONY: spawn-share-gpu-server


#########################
# Build & Install Decord
#########################

DECORD_CMAKE_USER_CUDA := $(shell if which nvcc > /dev/null; then echo "ON"; else echo "0"; fi)

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
	cd $@ && cmake .. $(DECORD_CMAKE_FLAGS) -DFFMPEG_DIR=/usr/local/opt/ffmpeg@5 -DCMAKE_BUILD_TYPE=Release

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


## Make utils

### Get index of word in a word list
### Source: https://stackoverflow.com/a/37483943/3771148
_pos = $(if $(findstring $1,$2),$(call _pos,$1,\
       $(wordlist 2,$(words $2),$2),x $3),$3)
pos = $(words $(call _pos,$1,$2))

### $(call lookup,word_a,wordlist_a,wordlist_b):
####   find the corresponding word_b in wordlist_b having
#### the same index as word_a in wordlist_a
####
#### Example:
####    ALPHA := a b c d e f g h i j k l m n o p q r s t u v w x y z
####    NATO := alpha beta charlie delta echo foxtrot gamma hotel india\
####            juliet kilo lima mike november oscar papa quebec romeo\
####            sierra tango uniform victor whisky yankee zulu
####    to-nato = $(call lookup,$1,$(ALPHA),$(NATO))
lookup = $(word $(call pos,$1,$2),$3)