# Source files: the result file of the movinet experiments
PKL_FILES := $(wildcard *.pkl)

# The results files: notebooks, JSONs and CSVs
## Extract the metrics
NOTEBOOK_FILES := $(patsubst %.pkl,%.ipynb,$(PKL_FILES))
JSON_FILES := $(patsubst %.pkl,%.json,$(PKL_FILES))
CSV_FILES := $(patsubst %.pkl,%.csv,$(PKL_FILES))

NOTEBOOK_NORM_FILES := $(patsubst %.pkl,%-normalized.ipynb,$(PKL_FILES))
JSON_NORM_FILES := $(patsubst %.pkl,%-normalized.json,$(PKL_FILES))
CSV_NORM_FILES := $(patsubst %.pkl,%-normalized.csv,$(PKL_FILES))

## Extracting the classification targets
CLASSES_NOTEBOOK_FILES := $(patsubst %.pkl,%-classes-for-walk-with-ladder.ipynb,$(PKL_FILES))
CLASSES_CSV_FILES := $(patsubst %.ipynb,%.csv,$(CLASSES_NOTEBOOK_FILES))

CLASSES_NOTEBOOK_NORM_FILES := $(patsubst %.pkl,%-classes-for-walk-with-ladder-normalized.ipynb,$(PKL_FILES))
CLASSES_CSV_NORM_FILES := $(patsubst %.ipynb,%.csv,$(CLASSES_NOTEBOOK_NORM_FILES))


# Set the default plotly renderer to notebook_connected
#
# For example, in case wishes to extract all images as png, pass this variable
# as env variable as so:
#    $ make all PLOTLY_RENDERER=png
PLOTLY_RENDERER := notebook_connected




# All

.PHONY: all
all: all-not-normalized all-normalized best-results.json all-classes-for-walk-with-ladder.ipynb

.PHONY: all-not-normalized
all-not-normalized: $(NOTEBOOK_FILES) $(JSON_FILES) all-results.json $(CSV_FILES) all-results-FN-equals-0.csv $(CLASSES_NOTEBOOK_FILES) $(CLASSES_CSV_FILES) all-classes-for-walk-with-ladder.csv

.PHONY: all-normalized
all-normalized: $(NOTEBOOK_NORM_FILES) $(JSON_NORM_FILES) all-results-normalized.json $(CSV_NORM_FILES) all-results-FN-equals-0.csv $(CLASSES_NOTEBOOK_NORM_FILES) $(CLASSES_CSV_NORM_FILES) all-classes-for-walk-with-ladder.csv


# "Round Trip" images and interactive plots
.PHONY: all-round-images
all-round-images:
	make -j9 --always-make all PLOTLY_RENDERER=png
	make images
	make -j9 --always-make all


# Clean
clean:
	@rm -f \
		$(NOTEBOOK_FILES) \
		$(JSON_FILES) \
		$(NOTEBOOK_NORM_FILES) \
		$(JSON_NORM_FILES) \
		$(CLASSES_NOTEBOOK_FILES) \
		$(CLASSES_CSV_FILES) \
		$(CLASSES_NOTEBOOK_NORM_FILES) \
		$(CLASSES_CSV_NORM_FILES) \
		all-results.json all-results-normalized.json best-results.json
.PHONY: clean




##### common targets #####

%.json: %.ipynb
	@echo "Getting results from $< using the cell tags named 'json-result-...'"
	jq -r '.cells \
		| map( \
			select(.metadata.tags[] \
				| select(startswith("json-result-")) \
			) \
			| { \
				(.metadata.tags[0] | sub("json-result-"; "")): \
					.outputs \
						| map(.text | join(" ")) \
						| join(" ") \
						| capture("(?<result>[0-9]+(.[0-9]+)?)") \
						| .result \
						| tonumber \
			  } \
		  ) \
		| add' $< > $@

%.csv: %.ipynb
	@echo "Getting results from $< using the cell tags named 'csv-result...'"
	jq -r '.cells[] | select(.metadata.tags[]? | contains("csv-result")) | .outputs | map(.text | join("")) | join("\n")' $< > $@




##### not normalized results #####

%.ipynb: %.pkl _template_movinet_results.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_movinet_results.ipynb $@ -p movinet_variation $* -p normalize_features False -p plotly_renderer $(PLOTLY_RENDERER)


all-results.json: $(JSON_FILES)
	jq '{(input_filename | sub(".json$$"; "")): .}' $(JSON_FILES) | jq 'reduce inputs as $$s (.; . += $$s)' > $@




##### normalized results #####

%-normalized.ipynb: %.pkl _template_movinet_results.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_movinet_results.ipynb $@ -p movinet_variation $* -p normalize_features True -p plotly_renderer $(PLOTLY_RENDERER)

all-results-normalized.json: $(patsubst %.pkl,%-normalized.json,$(PKL_FILES))
	jq '{(input_filename | sub(".json$$"; "")): .}' $(patsubst %.pkl,%-normalized.json,$(PKL_FILES)) | jq 'reduce inputs as $$s (.; . += $$s)' > $@




##### all not- and normalized results csv #####
display-all-results-csv: all-results.json all-results-normalized.json
	jq 'reduce inputs as $$s (.; . += $$s)' $^


##### best results json #####

best-results.json: $(wildcard all-results*.json)
	# @echo "Getting max ROC and PR auc from all results"

	jq 'reduce inputs as $$s (.; . += $$s)' all-results*.json \
		| jq 'to_entries \
			| { \
				"max-roc": max_by(.value."roc-auc") \
					| {best: .key, value: .value."roc-auc"}, \
				"max-pr": max_by(.value."pr-auc") \
					| {best: .key, value: .value."pr-auc"} \
			  }' > $@




##### merge csv #####

all-results-FN-equals-0.csv: $(CSV_FILES) $(CSV_NORM_FILES)
	awk 'FNR==1 && NR != 1{next} \
		FNR==1 && NR == 1{printf $$0 ", model_name\n"; next} \
		NF{sub(/\.csv$$/, "", FILENAME); printf $$0 ", " FILENAME "\n"}' $^ > $@


all-classes-for-walk-with-ladder.csv: $(CLASSES_CSV_FILES) $(CLASSES_CSV_NORM_FILES)
	awk 'FNR==1 && NR != 1{next}NF{print}' $^ > $@




##### rerun all-classes notebook #####

all-classes-for-walk-with-ladder.ipynb: all-classes-for-walk-with-ladder.csv
	poetry run papermill $@ $@.running -p plotly_renderer $(PLOTLY_RENDERER)
	mv $@.running $@
	./extract_decode_images_from_notebook.sh $@ images/;




##### alarm classification targets #####

%-classes-for-walk-with-ladder.ipynb: %.pkl _template_predicted_classes_for_walk_with_ladder.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_predicted_classes_for_walk_with_ladder.ipynb $@ -p movinet_variation $* -p normalize_features False -p plotly_renderer $(PLOTLY_RENDERER)


%-classes-for-walk-with-ladder-normalized.ipynb: %.pkl _template_predicted_classes_for_walk_with_ladder.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_predicted_classes_for_walk_with_ladder.ipynb $@ -p movinet_variation $* -p normalize_features True -p plotly_renderer $(PLOTLY_RENDERER)




##### extract all images #####

images: *.ipynb extract_decode_images_from_notebook.sh
	-mkdir -p images/normalized
	for i in {0..5}; do \
		./extract_decode_images_from_notebook.sh movineta$$i.ipynb images/movineta$$i-; \
		./extract_decode_images_from_notebook.sh movineta$$i-normalized.ipynb images/normalized/movineta$$i-; \
		./extract_decode_images_from_notebook.sh movineta$$i-classes-for-walk-with-ladder.ipynb images/movineta$$i-; \
		./extract_decode_images_from_notebook.sh movineta$$i-classes-for-walk-with-ladder-normalized.ipynb images/normalized/movineta$$i-; \
	done




##### more phony targets #####

display-all-results:
	jq 'reduce inputs as $$s (.; . += $$s)' all-results*.json
.PHONY: display-all-results


HAS_CLICKHOUSE_TOOLS := $(shell if which clickhouse > /dev/null; then echo "OK"; fi)

ifneq ($(strip $(HAS_CLICKHOUSE_TOOLS)),) # when clickhouse is installed

display-sorted-best-working-classes-for-walk-with-ladder: all-classes-for-walk-with-ladder.csv
	clickhouse local -q "SELECT model_name, normalize_features, class, score, bar(score, 0, 1, 100) FROM file('$<') ORDER BY score FORMAT PrettyCompact" \

display-sorted-best-working-classes-for-walk-with-ladder-mean-class: all-classes-for-walk-with-ladder.csv
	clickhouse local -q "SELECT class, count(*), avg(score), bar(avg(score), 0, 1, 300), groupArray(CONCAT(model_name, '-', normalize_features)) FROM file('$<') GROUP BY class ORDER BY avg(score) FORMAT PrettyCompact" \

display-sorted-best-working-classes-for-walk-with-ladder-mean-class-by-count: all-classes-for-walk-with-ladder.csv
	clickhouse local -q "SELECT class, count(*), avg(score), bar(avg(score), 0, 1, 300), groupArray(CONCAT(model_name, '-', normalize_features)) FROM file('$<') GROUP BY class ORDER BY count(*) FORMAT PrettyCompact" \

else # when clickhouse is not installed
display-sorted-best-working-classes-for-walk-with-ladder:
	$(warning "clickhouse is not installed, cannot display sorted best working classes for walk with ladder")
endif


HAS_CSVQ_TOOLS := $(shell if which csvq > /dev/null; then echo "OK"; fi)

ifneq ($(strip $(HAS_CSVQ_TOOLS)),) # when csvq is installed


display-highest-class-presence-by-variation: all-classes-for-walk-with-ladder.csv
	# order by count
	csvq -q 'SELECT model_name, normalize_features, class, count(*), min(score), avg(score), max(score) FROM `$<` WHERE score > 0 GROUP BY model_name, normalize_features, class ORDER BY count(*);'
display-highest-avg-by-variation: all-classes-for-walk-with-ladder.csv
	# highest avg with count by model variation > 1
	csvq -q 'SELECT model_name, normalize_features, class, count(*), min(score), avg(score), max(score) FROM `$<` WHERE score > 0 GROUP BY model_name, normalize_features, class HAVING count(*) > 2 ORDER BY avg(score);'
display-highest-class-presence: all-classes-for-walk-with-ladder.csv
	# most present classes across all models variations
	csvq -q 'SELECT class, count(*), min(score), avg(score), max(score) FROM `$<` WHERE score > 0 GROUP BY class ORDER BY count(*);'
display-highest-avg: all-classes-for-walk-with-ladder.csv
	# highest avg with count by model variation > 1 and score > 0.1 across all models variations
	csvq -q 'SELECT class, count(*), min(score), avg(score), max(score) FROM `$<` WHERE score > 0.1 GROUP BY class HAVING count(*) > 2 ORDER BY avg(score);'

display-all-csvq: display-highest-class-presence-by-variation display-highest-avg-by-variation display-highest-class-presence display-highest-avg

else # when csvq is not installed
display-highest-class-presence-by-variation:
	$(warning "csvq is not installed, cannot display sorted best working classes for walk with ladder")
display-highest-avg-by-variation:
	$(warning "csvq is not installed, cannot display sorted best working classes for walk with ladder")
display-highest-class-presence:
	$(warning "csvq is not installed, cannot display sorted best working classes for walk with ladder")
display-highest-avg:
	$(warning "csvq is not installed, cannot display sorted best working classes for walk with ladder")
endif
