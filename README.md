# Well of Memories #

Python 2.7 Serverless application for Well of Memories

## Packaged Dependencies ##
* FFmpeg
* ImageMagick
* python-opencv
* numpy

## Srverless Resources ##
* RendersBucket
S3 Bucket where the rendered videos will be stored
* WellOfMemoriesCounterTable
DynamoDB table 
* RenderSlideSnsTopic
SNS topic that triggers individual slide renedering process
* FinalVideoSnsTopic
SNS topic that triggers concatenation of slides and final video rendering

## Deployment ##
```serverless deploy --aws-profile serverless```