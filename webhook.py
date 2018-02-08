#============================================================
# webhook.py
# Sample endpoint that receives a POST request 
# when a video is ready for viewing
#
# CatAndCastle LLC, 2018
#============================================================
import json
import src.common as common

def handler(event, context):
	
	if 'body' in  event:
		try:
			data = json.loads(event['body'])
		except ValueError:
			return {
		        'statusCode': 400,
		        'body': 'Invalid JSON input'
		    }
	else:
		data = event

	status = data['status']
	project_id = data['project_id']
	video_url = data['video_url']
	errors = data['errors']

	# Do something with video_url here:
	if status=="ready":
		common.saveToDynamo({'id':project_id, 'item':'result', 'video':video_url})

	# Process errors here:
	# (pushing them back to dynamoDB for now)
	print errors
	for err in errors:

		common.saveToDynamo(
			{'id': project_id,
			'item': "error_%03d" % err["slideData"]["idx"],
			'slideData': err["slideData"]
			})

	# Must return something
	return {
        'statusCode': 200,
        'body': json.dumps({'msg': 'received'})
    }
