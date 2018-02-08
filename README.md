# Well of Memories #

Python 2.7 Serverless application for Well of Memories.
The application consists of a POST API endpoint that accepts JSON data with a list of slides to render.
Each slide is rendered in parallel on AWS Lambda.

## Packaged Dependencies ##
* FFmpeg
* ImageMagick
* python-opencv
* numpy

## Usage ##
Instal plugin for handling Lambda dead letter queue
```
npm install serverless-plugin-lambda-dead-letter
```
Deploy application on your AWS account
```
serverless deploy [--aws-profile serverless]
```

Trigger video creation process with a POST request to the [/new_video](https://github.com/CatAndCastle/WellOfMemories/wiki/New-Video) endpoint. Some examples of json video data can be found int he /examples folder.
```
curl -X POST -H "Content-Type: application/json" -d @examples/sample_video.json https://65omk9x4r6.execute-api.us-east-1.amazonaws.com/dev/new_video
```

## Development API Endpoint ##
https://65omk9x4r6.execute-api.us-east-1.amazonaws.com/dev/new_video


## Serverless Resources ##
The app creates the following resources in yor AWS account:
* `video_bucket`: S3 Bucket where intermediate files and the final videos will be stored
* `dynamo_table`: DynamoDB table for sharing data between lambda functions during rendering
* `dead_letter_sns`: SNS topics that acts as a dead letter queue when slides fail to render

The name of each resource can be customized in `serverless.yml`
```
# you can overwrite the bucket and database names here:
custom:
  video_bucket: dev.wom.com
  dynamo_table: WellOfMemories
  dead_letter_sns: render-slide-deadletter
```

## Lambda Functions ##
* **new_video**: starts video creation, triggers the render_slide function for each slide in the video.
* **render_slide**: renders one slide, uploads it to S3. When all slides have rendered - triggers the render_transition function to render overlapping transitions between slides.
* **render_slide_deadletter**: handles sildes that fail to render and are pushed to an SNS dead letter queue. Function stores errors in the database.
* **render_transition**: renders one transition, uploads it to S3. When all transitions have rendered - triggers the render_video function.
* **render_video**: concatenates all slides and transitions together, adds audio, renders the final video and uploads it to S3. Posts the video_url to the provided /webhook API endpoint.
* **webhook**: receives the video url when video is ready for viewing. Saves project_id and video_url in database.

## Pricing ##
* DynamoDB table - $5.32 per month for 5 reads & 10 writes per second
* S3 Storage - $0.023 per GB
* Lambda

| Function         | Memory   | Cost/second  | Average execution time | Average Cost / Video |
| -----------------|----------|--------------|------------------------|----------------------|
|new_video         |1024 MB   | $0.00001667  | 8s/request             |$0.00013336           |
|render_slide      |3008 MB   | $0.00004897  | 10s/photo, 30s/header  |$0.09543              |
|render_transition |3008 MB   | $0.00004897  | 8s/transition          |$0.0588               |
|render_video      |3008 MB   | $0.00004897  |  TBD                   |                      |
| **TOTAL**         |          |              |                       | **$0.154**           |

*assume an average video = 15 chapters with 10 photos/chapter
**assume all the slides render on the first try

## Limitations ##
* Lambda: allows up to 1000 concurrent lambda functions running at a time.
* DynamoDB: 5 reads, 10 writes per second. May need to increase the number of writes, or have it scale dynamically based on your traffic.


