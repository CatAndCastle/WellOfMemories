#!/bin/bash
#
# tojpeg.sh [inputfile]

export MAGICK_HOME="$LAMBDA_TASK_ROOT/ImageMagick-7.0.7"
# export MAGICK_HOME="/usr/local/ImageMagick-7.0.7"/
export PATH="$MAGICK_HOME/bin:$PATH"
export DYLD_LIBRARY_PATH="$MAGICK_HOME/lib/"

convert "$1" "$1.jpg"
