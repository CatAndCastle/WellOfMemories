# Well of Memories #

Python 2.7 Serverless application for Well of Memories.
The application consists of a POST API endpoint that accepts JSON data with a list of slides to render.
Each slide is rendered in parallel on AWS Lambda.

## Development API Endpoint##
https://65omk9x4r6.execute-api.us-east-1.amazonaws.com/dev/new_video

## Packaged Dependencies ##
* FFmpeg
* ImageMagick
* python-opencv
* numpy

## Usage ##
Deploy application on your AWS account
```
serverless deploy [--aws-profile serverless]
```

Trigger video creation process with a POST request to the /new_video endpoint. Refer to new_video.json for example json data to POST
```
curl -X POST -H "Content-Type: application/json" -d @new_video.json https://65omk9x4r6.execute-api.us-east-1.amazonaws.com/dev/new_video
```

## Srverless Resources ##
* video_bucket: 
S3 Bucket where intermediate files and the final videos will be stored
* dynamo_table:
DynamoDB table for storing data during rendering


## Lambda Functions ##
* new_video
* render_slide
* render_transition
* render_video
* webhook