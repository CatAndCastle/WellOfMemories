# Well of Memories #

Python 2.7 Serverless application for Well of Memories

## Packaged Dependencies ##
* FFmpeg
* ImageMagick
* python-opencv
* numpy

## Srverless Resources ##
* video_bucket: 
S3 Bucket where intermediate files and the final videos will be stored
* dynamo_table:
DynamoDB table for storing data during rendering


## Deployment ##
```serverless deploy [--aws-profile serverless]```