PKL_FILES := $(wildcard *.pkl)

NOTEBOOK_FILES := $(patsubst %.pkl,%.ipynb,$(PKL_FILES))
JSON_FILES := $(patsubst %.pkl,%.json,$(PKL_FILES))


CLASSES_NOTEBOOK_FILES := $(patsubst %.pkl,%-classes-for-walk-with-ladder.ipynb,$(PKL_FILES))


# Set the default plotly renderer to notebook_connected
#
# For example, in case wishes to extract all images as png, pass this variable
# as env variable as so:
#    $ make all PLOTLY_RENDERER=png
PLOTLY_RENDERER := notebook_connected


# All

all: all-not-normalized all-normalized best-results.json
.PHONY: all

all-not-normalized: $(NOTEBOOK_FILES) $(JSON_FILES) all-results.json $(CLASSES_NOTEBOOK_FILES) $(patsubst %.ipynb,%.csv,$(CLASSES_NOTEBOOK_FILES))
.PHONY: all-not-normalized

all-normalized: $(patsubst %.pkl,%-normalized.ipynb,$(PKL_FILES)) $(patsubst %.pkl,%-normalized.json,$(PKL_FILES)) all-results-normalized.json $(patsubst %.pkl,%-classes-for-walk-with-ladder-normalized.csv,$(PKL_FILES))
.PHONY: all-normalized


# Clean
clean:
	@rm -f $(NOTEBOOK_FILES) $(JSON_FILES) all-results.json \
		$(patsubst %.pkl,%-normalized.ipynb,$(PKL_FILES)) $(patsubst %.pkl,%-normalized.json,$(PKL_FILES)) all-results-normalized.json \
		best-results.json \
		$(CLASSES_NOTEBOOK_FILES) $(patsubst %.ipynb,%.csv,$(CLASSES_NOTEBOOK_FILES)) \
		$(patsubst %.pkl,%-classes-for-walk-with-ladder-normalized.csv,$(PKL_FILES))
.PHONY: clean



##### not normalized results #####

%.ipynb: %.pkl _template_movinet_results.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_movinet_results.ipynb $@ -p movinet_variation $* -p normalize_features False -p plotly_renderer $(PLOTLY_RENDERER)


%.json: %.ipynb
	@echo "Getting results from $< using the cell tags named 'result-...'"
	jq -r '.cells \
		| map( \
			select(.metadata.tags[] \
				| select(startswith("result-")) \
			) \
			| { \
				(.metadata.tags[0] | sub("result-"; "")): \
					.outputs \
						| map(.text | join(" ")) \
						| join(" ") \
						| capture("(?<result>[0-9]+(.[0-9]+)?)") \
						| .result \
						| tonumber \
			  } \
		  ) \
		| add' $< > $@

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




##### alarm classification targets #####

%-classes-for-walk-with-ladder.ipynb: %.pkl _template_predicted_classes_for_walk_with_ladder.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_predicted_classes_for_walk_with_ladder.ipynb $@ -p movinet_variation $* -p normalize_features False -p plotly_renderer $(PLOTLY_RENDERER)


%-classes-for-walk-with-ladder-normalized.ipynb: %.pkl _template_predicted_classes_for_walk_with_ladder.ipynb
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_predicted_classes_for_walk_with_ladder.ipynb $@ -p movinet_variation $* -p normalize_features True -p plotly_renderer $(PLOTLY_RENDERER)

%.csv: %.ipynb
	jq -r '.cells[] | select(.metadata.tags[]? | select(startswith("result-"))) | .outputs | map(.text | join("")) | join("\n")' $< > $@



##### extract all images #####

images: *.ipynb extract_decode_images_from_notebook.sh
	-mkdir -p images/normalized/movineta{0..5}
	-mkdir -p images/movineta{0..5}
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
		| sort -t, -k2 -n \
		| clickhouse local --input-format "CSV" -q "SELECT model_name, class, score, bar(score, 0, 1, 100) FROM table FORMAT PrettyCompact"

display-sorted-best-working-classes-for-walk-with-ladder-mean-class:
	awk 'FNR==1 && NR != 1{next}NF{print}' *.csv \
		| sort -t, -k2 -n \
		| clickhouse local --input-format "CSV" -q "SELECT class, avg(score), bar(avg(score), 0, 1, 300), groupArray(model_name) FROM table GROUP BY class ORDER BY avg(score) FORMAT PrettyCompact"

else # when clickhouse is not installed
display-sorted-best-working-classes-for-walk-with-ladder:
	awk 'FNR==1 && NR != 1{next}NF{print}' *.csv | sort -t, -k2 -n
endif
