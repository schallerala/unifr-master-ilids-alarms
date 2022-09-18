help: ## print this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-40s\033[0m %s\n", $$1, $$2}'

.PHONY: help

# TODO add help messages of phony targets

#########################
# Data Preparation
#########################



# Initial ILIDS to intermediate
###############################



## SZTE & SZTR metadata
#######################

SZTE_INITIAL_FOLDER := SZTE
SZTR_INITIAL_FOLDER := SZTR

SZTE_INTERMEDIATE_FOLDER := ../SZTE
SZTR_INTERMEDIATE_FOLDER := ../SZTR


SZTE_INITIAL_VIDEOS_METADATA := $(wildcard $(SZTE_INITIAL_FOLDER)/video/*.xml)

SZTE_INTERMEDIATE_VIDEOS := $(patsubst $(SZTE_INITIAL_FOLDER)/%,$(SZTE_INTERMEDIATE_FOLDER)/%,$(SZTE_INITIAL_VIDEOS_METADATA))


$(SZTE_INTERMEDIATE_FOLDER) $(SZTR_INTERMEDIATE_FOLDER):
	-mkdir $@


$(SZTE_INTERMEDIATE_FOLDER)/index.xml: $(SZTE_INITIAL_FOLDER)/index.xml | $(SZTE_INTERMEDIATE_FOLDER)
	cp $< $@

$(SZTE_INTERMEDIATE_FOLDER)/video/%.xml: $(SZTE_INITIAL_FOLDER)/video/%.xml | $(SZTE_INTERMEDIATE_VIDEO_FOLDER)
	cp $< $@

$(SZTR_INTERMEDIATE_FOLDER)/index.xml: $(SZTR_INITIAL_FOLDER)/index.xml | $(SZTR_INTERMEDIATE_FOLDER)
	cp $< $@

$(SZTR_INTERMEDIATE_FOLDER)/SZTR.mdb: $(SZTR_INITIAL_FOLDER)/SZTR.mdb | $(SZTR_INTERMEDIATE_FOLDER)
	cp $< $@


copy-initial-metadata-szte: $(SZTE_INTERMEDIATE_FOLDER)/index.xml $(SZTE_INTERMEDIATE_VIDEOS)

copy-initial-metadata-sztr: $(SZTR_INTERMEDIATE_FOLDER)/index.xml $(SZTR_INTERMEDIATE_FOLDER)/SZTR.mdb

copy-initial-metadata: copy-initial-metadata-szte copy-initial-metadata-sztr

.PHONY: copy-initial-metadata copy-initial-metadata-szte copy-initial-metadata-sztr


## Scale & Compress videos
##########################

SZTE_INTERMEDIATE_VIDEO_FOLDER := $(SZTE_INTERMEDIATE_FOLDER)/video
SZTR_INTERMEDIATE_VIDEO_FOLDER := $(SZTR_INTERMEDIATE_FOLDER)/video


SZTE_INITIAL_VIDEOS := $(wildcard $(SZTE_INITIAL_FOLDER)/video/*.mov)
SZTR_INITIAL_VIDEOS := $(wildcard $(SZTR_INITIAL_FOLDER)/video/*.mov)


SZTE_INTERMEDIATE_VIDEOS := $(patsubst $(SZTE_INITIAL_FOLDER)/%,$(SZTE_INTERMEDIATE_FOLDER)/%,$(SZTE_INITIAL_VIDEOS))
SZTR_INTERMEDIATE_VIDEOS := $(patsubst $(SZTR_INITIAL_FOLDER)/%,$(SZTR_INTERMEDIATE_FOLDER)/%,$(SZTR_INITIAL_VIDEOS))


$(SZTE_INTERMEDIATE_VIDEO_FOLDER): | $(SZTE_INTERMEDIATE_FOLDER)
	-mkdir $@
$(SZTR_INTERMEDIATE_VIDEO_FOLDER): | $(SZTR_INTERMEDIATE_FOLDER)
	-mkdir $@


$(SZTE_INTERMEDIATE_VIDEO_FOLDER)/%.mov: $(SZTE_INITIAL_FOLDER)/video/%.mov | $(SZTE_INTERMEDIATE_VIDEO_FOLDER)
	poetry run ilids_cmd videos compress single $< $(@D)

$(SZTR_INTERMEDIATE_VIDEO_FOLDER)/%.mov: $(SZTR_INITIAL_FOLDER)/video/%.mov | $(SZTR_INTERMEDIATE_VIDEO_FOLDER)
	poetry run ilids_cmd videos compress single $< $(@D)


compress-initial-szte: $(SZTE_INTERMEDIATE_VIDEOS)
compress-initial-sztr: $(SZTR_INTERMEDIATE_VIDEOS)

compress-initial: compress-initial-szte compress-initial-sztr

.PHONY: compress-initial-szte compress-initial-sztr compress-initial



## Intermediate general phony

szte-intermediate: copy-initial-metadata-szte compress-initial-szte
sztr-intermediate: copy-initial-metadata-sztr compress-initial-sztr

.PHONY: szte-intermediate sztr-intermediate



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
