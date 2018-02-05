# Well of Memories #

Python 2.7 Serverless application for Well of Memories.
The application consists of a POST API endpoint that accepts JSON data with a list of slides to render.
Each slide is rendered in parallel on AWS Lambda.

## Development API Endpoint ##
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
DynamoDB table for sharing data between lambda functions during rendering


## Lambda Functions ##
* **new_video**: starts video creation, triggers the render_slide function for each slide in the video.
* **render_slide**: renders one slide, uploads it to S3. When all slides have rendered - triggers the render_transition function to render overlapping transitions between slides.
* **render_transition**: renders one transition, uploads it to S3. When all transitions have rendered - triggers the render_video function.
* **render_video**: concatenates all slides and transitions together, adds audio, renders the final video and uploads it to S3. Posts the video_url to the provided /webhook API endpoint.
* **webhook**: example webhook API endpoint