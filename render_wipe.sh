#!/bin/bash
#
# render_wipe.sh [input] [wipe_duration] [duration] [output]

export PATH="$LAMBDA_TASK_ROOT/bin:$PATH"

ffmpeg -loop 1 -i $1 -i assets/white_mask.png \
-filter_complex "\
[0]fade=in:st=0:d=0.5:c=white,scale=w=trunc(iw/2)*2:h=trunc(ih/2)*2[v];\
[1][v]scale2ref[c1][v1];\
[v1][c1]overlay=x='(t/$2)*W':y='(H-h)/2',trim=duration=$3,setpts=PTS-STARTPTS[vf]" -map "[vf]" -pix_fmt yuv420p -y $4