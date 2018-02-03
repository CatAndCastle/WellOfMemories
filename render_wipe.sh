#!/bin/bash
#
# render_wipe.sh [input] [wipe_duration] [duration] [output]

export PATH="$LAMBDA_TASK_ROOT/bin:$PATH"

ffmpeg -f lavfi -i color=white:d="$3" \
-loop 1 -i $1 \
-i assets/white_mask.png \
-filter_complex "\
[1]fade=in:st=0:d=0.5:alpha=1,scale=w=trunc(iw/2)*2:h=trunc(ih/2)*2[txt];\
[2][txt]scale2ref[wipe][txt1];\
[0][txt1]scale2ref[bg][txt2];\
[bg][txt2]overlay=x=0:y=0,setpts=PTS-STARTPTS[bg2];\
[bg2][wipe]overlay=x='(t/$2)*W':y='(H-h)/2',trim=duration=$3,setpts=PTS-STARTPTS[vf]" -map "[vf]" -pix_fmt yuv420p -y $4


# WITHOUT WHITE BACKGROUND:
# ffmpeg -loop 1 -i $1 -i assets/white_mask.png \
# -filter_complex "\
# [0]fade=in:st=0:d=0.5:c=white,scale=w=trunc(iw/2)*2:h=trunc(ih/2)*2[v];\
# [1][v]scale2ref[c1][v1];\
# [v1][c1]overlay=x='(t/$2)*W':y='(H-h)/2',trim=duration=$3,setpts=PTS-STARTPTS[vf]" -map "[vf]" -pix_fmt yuv420p -y $4

