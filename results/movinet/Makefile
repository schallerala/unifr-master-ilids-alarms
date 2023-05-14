PKL_FILES := $(wildcard *.pkl)

NOTEBOOK_FILES := $(patsubst %.pkl,%.ipynb,$(PKL_FILES))
JSON_FILES := $(patsubst %.pkl,%.json,$(PKL_FILES))

all: $(NOTEBOOK_FILES) $(JSON_FILES) all-results.json

%.ipynb: %.pkl
	@echo "Producing $@ from $< using template file"
	poetry run papermill _template_movinet_results.ipynb $@ -p movinet_variation $* -p normalize_features False


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