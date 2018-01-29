#!/bin/bash
#
# render_label.sh [text] [fontfile.ttf] [fill hex] [pointSize] [kerning] [file]
# title size = 1280x260

export MAGICK_HOME="$LAMBDA_TASK_ROOT/ImageMagick-7.0.7"
# export MAGICK_HOME="/usr/local/ImageMagick-7.0.7"
export PATH="$MAGICK_HOME/bin:$PATH"
export DYLD_LIBRARY_PATH="$MAGICK_HOME/lib/"

# TITLE
convert \
-background "#ffffff" \
-font "$2" \
-fill "$3" \
-pointsize "$4" \
-kerning "$5" \
-density 90 \
-gravity center \
label:"$1" \
"$6"