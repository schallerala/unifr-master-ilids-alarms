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
all: all-not-normalized all-normalized best-results.json

.PHONY: all-not-normalized
all-not-normalized: $(NOTEBOOK_FILES) $(JSON_FILES) all-results.json $(CSV_FILES) all-results-FN-equals-0.csv $(CLASSES_NOTEBOOK_FILES) $(CLASSES_CSV_FILES)

.PHONY: all-normalized
all-normalized: $(NOTEBOOK_NORM_FILES) $(JSON_NORM_FILES) all-results.json $(CSV_NORM_FILES) all-results-FN-equals-0.csv $(CLASSES_NOTEBOOK_NORM_FILES) $(CLASSES_CSV_NORM_FILES)


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
		NF{sub(/\.csv$$/, "", FILENAME); printf $$0 ", " FILENAME "\n"}' $^ | sort -k5 -n -r -t, > $@




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
		./extract_decode_images_from_notebook.sh movineta$$i-normalized.ipynb images/normalized/movineta$$i-; \
		./extract_decode_images_from_notebook.sh movineta$$i.ipynb images/movineta$$i-; \
		./extract_decode_images_from_notebook.sh movineta$$i-classes-for-walk-with-ladder.ipynb images/movineta$$i-; \
	done




##### more phony targets #####

display-all-results:
	jq 'reduce inputs as $$s (.; . += $$s)' all-results*.json
.PHONY: display-all-results


HAS_CLICKHOUSE_TOOLS := $(shell if which clickhouse > /dev/null; then echo "OK"; fi)

ifneq ($(strip $(HAS_CLICKHOUSE_TOOLS)),) # when clickhouse is installed

display-sorted-best-working-classes-for-walk-with-ladder:
	awk 'FNR==1 && NR != 1{next}NF{print}' *.csv \
		| sort -t, -k1 -n \
		| clickhouse local --input-format "CSV" -q "SELECT model_name, class, score, bar(score, 0, 1, 100) FROM table FORMAT PrettyCompact"

display-sorted-best-working-classes-for-walk-with-ladder-mean-class:
	awk 'FNR==1 && NR != 1{next}NF{print}' *.csv \
		| sort -t, -k1 -n \
		| clickhouse local --input-format "CSV" -q "SELECT class, avg(score), bar(avg(score), 0, 1, 300), groupArray(model_name) FROM table GROUP BY class ORDER BY avg(score) FORMAT PrettyCompact"

else # when clickhouse is not installed
display-sorted-best-working-classes-for-walk-with-ladder:
	awk 'FNR==1 && NR != 1{next}NF{print}' *.csv | sort -t, -k1 -n
endif
