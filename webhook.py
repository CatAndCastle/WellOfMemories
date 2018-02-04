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
		        'msg': 'Invalid JSON input'
		    }
	else:
		data = event
	# Do something with video_url here!
	common.saveToDynamo({'id':data['project_id'], 'item':'result', 'video':data['video_url']})


	return {
        'statusCode': 200,
        'body': json.dumps({'video': data['video_url']})
    }