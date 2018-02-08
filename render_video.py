#============================================================
# render_video.py
# AWS Lambda function for Well Of Memories
# concatenates previously rendered video segments and renders out the final video 
#
# CatAndCastle LLC, 2018
#============================================================
import os,json,urllib
import urllib2
import src.common as common
from src.common import DecimalEncoder
import boto3
import subprocess
from subprocess import call,check_output
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')
TABLE = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

FFMPEG_BIN = os.environ['LAMBDA_TASK_ROOT']+'/bin/ffmpeg'
# FFMPEG_BIN = "ffmpeg"


def handler(event, context):
	common.cleanup()

	project_id = event["project_id"]

	# project info
	response = TABLE.query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').eq('info'),
	)
	project_data = response['Items'][0]['data']
	print(project_data)

	# chunks	
	chunks = TABLE.query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').begins_with('chunk_')
	)
	
	paths = []
	for i in chunks['Items']:
		print i
		# download files to disk
		local_path = common.downloadFile(i['chunkData']["url"], "chunk", "mp4")
		paths.append("file '%s" % local_path)
	
	# concat.txt file		
	with open('/tmp/concat.txt', 'w') as the_file:
		the_file.write("\n".join(paths))

	# Concatenate segments
	video_file = "/tmp/concat.mp4"
	cmd = "%s -f concat -safe 0 -i /tmp/concat.txt -c copy -y %s" % (FFMPEG_BIN, video_file)
	common.executeCmd(cmd)

	# Get final video duration
	cmd = FFMPEG_BIN + " -i /tmp/concat.mp4 2>&1 | grep \"Duration\"| cut -d ' ' -f 4 | sed s/,// | sed 's@\..*@@g' | awk '{ split($1, A, \":\"); split(A[3], B, \".\"); print 3600*A[1] + 60*A[2] + B[1] }'"
	res = common.executeCmd(cmd)
	duration = res["result"].replace("\n", "")
	# duration = check_output(cmd, shell=True,stderr=subprocess.STDOUT).replace("\n","")
	# print "duration = %s" % duration

	# Add audio track - with 3 second audio fade out
	final_file = "/tmp/%s" % project_data['fileName']
	cmd = [FFMPEG_BIN,
		"-i %s -i %s" % (video_file, project_data['audioUrl']),
		"-filter_complex \"[1]afade=t=out:st=%.2f:d=3[a]\" -map 0:0 -map \"[a]\"" % (int(duration)-3),
		"-c:v copy -c:a aac -t %s -y %s" % (duration, final_file)
		]
	common.executeCmd(" ".join(cmd))

	# upload final file to S3
	video_url = common.uploadS3(final_file, "%s/%s" % (project_data['folderName'], project_data['fileName']))

	# post result to webhook
	common.notifyWebhook(project_id, video_url, "ready")



# handler({"project_id":"3Cpn9KsMyE52XnseCm8sVXKf"},{})
# deleteProjectData("3Cpn9KsMyE52XnseCm8sVXKf")
