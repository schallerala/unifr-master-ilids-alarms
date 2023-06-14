# Source files: the result file of the actionclip experiments
PKL_FILES := $(wildcard *.pkl)

EXPERIMENT_NAMES := $(patsubst %.pkl,%,$(PKL_FILES))

# The results files: notebooks, JSONs and images
#   Each experiment has its folder
NOTEBOOK_FILES := $(patsubst %.pkl,%/actionclip-eval-notebook.ipynb,$(PKL_FILES))
JSON_FILES := $(patsubst %.pkl,%/results.json,$(PKL_FILES))
IMAGES_FOLDERS := $(patsubst %.pkl,%/images,$(PKL_FILES))




# Set the default plotly renderer to notebook_connected
#
# For example, in case wishes to extract all images as png, pass this variable
# as env variable as so:
#    $ make all PLOTLY_RENDERER=png
PLOTLY_RENDERER := notebook_connected



.PHONY: all
all: $(NOTEBOOK_FILES) $(JSON_FILES) $(IMAGES_FOLDERS) all-results.json all-best-results.json




# "Round Trip" images and interactive plots
.PHONY: all-round-images
all-round-images:
	make -j4 --always-make all PLOTLY_RENDERER=png
	make -j4 --always-make all



.PHONY: clean
clean:
	@rm -f $(NOTEBOOK_FILES) $(JSON_FILES)
	@rm -f {$(EXPERIMENT_NAMES)}/images/*.png
	@rmdir -f {$(EXPERIMENT_NAMES)}/images
	@rmdir -f $(EXPERIMENT_NAMES)



%/actionclip-eval-notebook.ipynb: %.pkl _template_actionclip_clips_texts_similarities.ipynb
	@-mkdir -p $(@D)
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_actionclip_clips_texts_similarities.ipynb $@ -p actionclip_variation $* -p plotly_renderer $(PLOTLY_RENDERER)


%/results.json: %/actionclip-eval-notebook.ipynb
	@echo "Extracting results from cells with tag 'result-json-...' and output metadata of type 'application/json' and metadata tags 'extract-json'"
	jq '[ \
		.cells[] \
		| select(.metadata.tags[]? | select(startswith("result-json-"))) \
		| .outputs[] \
		| select(.data."application/json" != null and (.metadata."application/json".tags[]? | contains("extract-json"))) \
		| .data."application/json" \
	]' $< > $@


%/images: %/actionclip-eval-notebook.ipynb
	@-mkdir -p $@
	@echo "Extracting images from cells with tag 'result-image-...' and output metadata of type 'image/png' and metadata tags 'extract-image'"
	../extract_decode_images_from_notebook.sh $< $@/



#### Aggregate targets

all-results.json: $(JSON_FILES)
	jq '[ \
			reduce inputs as $$s (.; . += $$s) \
		| .[] \
		| select(has("best") | not) \
	] | sort_by(.TN)' $(JSON_FILES) > $@


all-best-results.json: $(JSON_FILES)
	jq '[ \
			reduce inputs as $$s (.; . += $$s) \
		| .[] \
		| select(.best != null) \
		| .best \
	] | sort_by(.roc_auc)' $(JSON_FILES) > $@



gen-result-table: all-results.json
	@node scripts/join-results.js all-results.json




# hparam search

all-hparam: $(patsubst %, %/hparam.log, $(EXPERIMENT_NAMES)) $(patsubst %, %/hparam-trials.log, $(EXPERIMENT_NAMES))


%/hparam.log %/hparam-trials.log: %.pkl hparam.py hparam
	poetry run python hparam.py $* > $*/hparam.log 2> $*/hparam-trials.log