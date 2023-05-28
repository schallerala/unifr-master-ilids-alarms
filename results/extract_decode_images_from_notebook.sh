#!/bin/sh

# This script extracts images from a notebook by looking for cell tags starting
# with "image-".
#
# It then extracts the image data from the notebook and saves it to individual
# files names as follows:
#       <image-tag>-<image-index>.png
#
# where <image-tag> is the tag of the cell containing the image
# and <image-index> is the index of the image in output (as a cell can produce multiple
# outputs)

# For example:
#       image-activation-distribution-0.png

# give a notebook filename as an argument
notebook="$1"
# if a second argument is given, use it as a prefix for the images
image_prefix="$2"

# go through all cells, check for metadata tags to have "image-" and outputs of type image/png
#    if so, print the cell index and the image name
#       plus the number of output of type image/png
# Produces something like:
#   10,image-activation-distribution,0
#   13,image-roc,0
#   16,image-pr,0
#   21,image-cost-function,0
#   25,image-confusion-matrix-cost-function,0
#   ...
get_images_from_notebook_as_csv() {
    jq -r '.cells
        | to_entries[]
        | select(.value.metadata.tags[]? | select(startswith("image-")))
        | {cell_index: .key, image_name: .value.metadata.tags[0], outputs: .value.outputs} as $cell_obj
        | $cell_obj.outputs
        | to_entries[]
        | select(.value.data."image/png" != null)
        | {cell_index: $cell_obj.cell_index | tostring, image_name: $cell_obj.image_name, image_index: .key | tostring}
        | .cell_index + "," + .image_name + "," + .image_index' "$notebook"
}

get_images_from_notebook_as_csv \
    | while IFS=, read -r cell_index image_name image_index; do
        image_target="$image_prefix$image_name-$image_index.png";

        if [ -e "$image_target" ] && ! [ "$notebook" -nt "$image_target" ]; then
            echo "File $image_target exists. Skipped";
            continue;
        fi

        echo "Extracting $image_target";
        jq -r \
            --arg cell_index $cell_index \
            --arg image_index $image_index \
            '.cells['$cell_index'].outputs['$image_index'].data."image/png"' $notebook \
        | base64 -d > "$image_target";
    done