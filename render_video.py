#============================================================
# render_video.py
# AWS Lambda function for Well Of Memories
# concatenates previously rendered video segments and renders out the final video 
#
# CatAndCastle LLC, 2018
#============================================================
import os,json,urllib
import src.common as common
import boto3
import subprocess
from subprocess import call,check_output
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')
TABLE = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
# TABLE = dynamodb.Table('WellOfMemories')
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# FFMPEG_BIN = os.environ['LAMBDA_TASK_ROOT']+'/bin/ffmpeg'
FFMPEG_BIN = "ffmpeg"


def handler(event, context):
	common.cleanup()

	project_id = event["project_id"]

	# project info
	response = TABLE.query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').eq('info'),
	)
	project_data = response['Items'][0]['data']
	print(project_data)

	# slides	
	chunks = TABLE.query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').begins_with('chunk_')
	)
	
	paths = []
	for i in chunks['Items']:
		print i
		# download files to disk
		local_path = common.downloadFile(i['chunkData']["url"], "chunk", "mp4")
		paths.append("file '%s" % local_path)
		
	with open('/tmp/concat.txt', 'w') as the_file:
		the_file.write("\n".join(paths))



	video_file = "/tmp/concat.mp4"
	cmd = "%s -f concat -safe 0 -i /tmp/concat.txt -c copy -y %s" % (FFMPEG_BIN, video_file)
	common.executeCmd(cmd)

	cmd = "ffmpeg -i /tmp/concat.mp4 2>&1 | grep \"Duration\"| cut -d ' ' -f 4 | sed s/,// | sed 's@\..*@@g' | awk '{ split($1, A, \":\"); split(A[3], B, \".\"); print 3600*A[1] + 60*A[2] + B[1] }'"
	duration = check_output(cmd, shell=True,stderr=subprocess.STDOUT).replace("\n","")
	print "duration = %s" % duration

	final_file = "/tmp/%s" % project_data['fileName']
	cmd = "%s -i %s -i %s -c:v copy -c:a aac -t %s -y %s" % (FFMPEG_BIN, video_file, project_data['audioUrl'], duration, final_file)
	common.executeCmd(cmd)

	# res = comp.render(video_file)
	# combo_file = "/tmp/%s" % project_data['fileName']
	# res = comp.addAudio(project_data['audioUrl'], combo_file)
	# if res['error'] is False:
	# 	common.uploadS3(combo_file, "%s/%s" % (project_id, project_data['fileName']))
	# 	# deleteProjectData(proj_id, slides)

def download(url):
		path = '/tmp/chunk-' + common.randomString(10) +'.mp4'
		urllib.urlretrieve(url, path)
		return path

def deleteProjectData(project_id, slides):

	TABLE.delete_item(
		Key={
		'id': project_id,
		'item':'counter'
		})
	
	TABLE.delete_item(
		Key={
		'id': project_id,
		'item':'info'
		})

	for i in slides['Items']:
		TABLE.delete_item(
		    Key={
		        'id': project_id,
				'item':i['item']
		    })

handler({"project_id":"3Cpn9KsMyE52XnseCm8sVXKf"},{})