#============================================================
# render_transition.py
# AWS Lambda function for Well Of Memories
# renders a transition chunk between two slides
#
#              [v-start]  [transition]
# slide_from |**************|******|  [v-middle]     [v-end]
# slide_to                  |******|****************|*******]
#
# CatAndCastle LLC, 2018
#============================================================

import os,json,urllib,sys
import src.common as common
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
dynamodb = boto3.resource('dynamodb')

import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

def handler(event, context):
	common.cleanup()
	# log.debug("Received event {}".format(json.dumps(event)))
	
	project_id = event["project_id"]
	slide_from = event["slide_from"]
	slide_to = event["slide_to"]
	chunk_idx = event["chunk_idx"]

	chunk_sub_idx = 0
	

	slide_from_data = getSlideData(project_id, slide_from)
	slide_to_data = getSlideData(project_id, slide_to)

	from_path = common.downloadFile(slide_from_data["renderedUrl"], "slide", "mp4")
	to_path = common.downloadFile(slide_to_data["renderedUrl"], "slide", "mp4")

	filters = []
	outs = []
	chunk_ids = []
	
	#
	# If no overlapping transition between slides:
	#                   [from]
	# slide_from |********************|          [to]
	# slide_to                        |****************************]
	#
	#
	if 'transitionOut' not in slide_from_data or slide_from_data["transitionOut"]!="fadeOutOverNext":
		if chunk_idx == 0:
			#                  *[from]*
			# slide_from |********************|       [to]
			# slide_to                        |**************************]
			#
			chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
			saveChunkData(project_id, chunk_id, slide_from_data["renderedUrl"])
			chunk_sub_idx+=1

		if 'transitionOut' in slide_to_data and slide_to_data["transitionOut"]=="fadeOutOverNext":
			#                  [from]
			# slide_from |********************|    *[to-start]*   [fadeOutOverNext]
			# slide_to                        |**********************|*******]
			#
			slide_to_start_t = 0.00
			slide_to_end_t = slide_to_data["transitionOutStart"]
			chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
			cmd = [
				common.FFMPEG_BIN,
				"-i %s" % to_path,
				"-vf trim=%.2f:%.2f" % (slide_to_start_t, slide_to_end_t),
				"-y /tmp/%s.mp4" % chunk_id]
			common.executeCmd(" ".join(cmd))
			chunk_url = uploadChunk(project_id, chunk_id, "/tmp/%s.mp4" % chunk_id)
			saveChunkData(project_id, chunk_id, chunk_url)
			chunk_sub_idx+=1

		else:
			#                  [from]
			# slide_from |********************|     *[to]*
			# slide_to                        |********************|
			#
			chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
			saveChunkData(project_id, chunk_id, slide_to_data["renderedUrl"])
			chunk_sub_idx+=1
		
		# Decrement counter in DB
		updateCounter(project_id, context)
		sys.exit()


	#
	#  Overlapping transition between slides:
	#
	#                 [from]       [transition]
	# slide_from |******************|******|     [to-middle]    [transition]
	# slide_to                      |******|*********************|*******]
	#
	#

	if chunk_idx == 0:
		#
		#                *[v0-start]*   [v0-end]
		# slide_from |******************|******|     
		# slide_to                      |******|*********************|*******]
		#
		#

		filters.append("[0:v]split[v0-start][v0-end];[v0-start]trim=0:%.2f[v0-start];[v0-end]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v0-end]" % 
			(slide_from_data["transitionOutStart"], slide_from_data["transitionOutStart"], slide_from_data["transitionOutStart"]+slide_from_data["transitionOutDuration"]))
		chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
		outs.append("-map \"[v0-start]\" -y /tmp/%s.mp4" % chunk_id)
		chunk_ids.append(chunk_id)
		chunk_sub_idx+=1
	else:
		#
		#                              *[v0-end]*
		# slide_from |******************|******|    
		# slide_to                      |******|*********************|*******]
		#
		#
		filters.append("[0:v]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v0-end]" % 
			(slide_from_data["transitionOutStart"], slide_from_data["duration"]))

	#
	#                
	# slide_from |******************|******|                      [fadeOutOverNext?]
	# slide_to                      |******|************************|*******]
	#                            *[v1-transition]*  *[v1-middle]*   
	#
	
	slide_to_end_t = slide_to_data["duration"]
	if 'transitionOut' in slide_to_data and slide_to_data["transitionOut"]=="fadeOutOverNext":
		slide_to_end_t = slide_to_data["transitionOutStart"]

	# filters.append(
	# 	"[1:v]split[v1-transition][v1-middle];\
	# 	[v1-transition]trim=0:%.2f[v1-transition];\
	# 	[v1-middle]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v1-middle]" 
	# 	% (slide_from_data["transitionOutDuration"],
	# 		slide_from_data["transitionOutDuration"],
	# 		slide_to_end_t
	# 		)
	# 	)
	filters.append(
		"[1:v]split[v1-transition][v1-middle];\
		[v1-transition]trim=0:%.2f[v1-transition];\
		[v1-middle]trim=%.2f:%.2f,setpts=PTS-STARTPTS[v1-middle]" 
		% (slide_from_data["transitionOutDuration"],
			slide_from_data["transitionOutDuration"],
			slide_to_end_t
			)
		)

	#
	#                     *[from-to-transition]*   
	# combined |***************|***********|********************| 
	#                [from]                         [to]
	#
	# if 'transitionOut' in slide_from_data and slide_from_data["transitionOut"]=="fadeOutOverNext":
	filters.append("[v0-end]fade=out:st=0:d=%.2f:alpha=1[v0-transition]" % slide_from_data["transitionOutDuration"])
	filters.append("[v1-transition][v0-transition]overlay=x=0:y=0:eof_action=pass[from-to-transition]")

	# save chunks
	chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
	outs.append("-map \"[from-to-transition]\" -y /tmp/%s.mp4" % chunk_id)
	chunk_ids.append(chunk_id)
	chunk_sub_idx+=1
	
	chunk_id = getChunkId(chunk_idx, chunk_sub_idx)
	outs.append("-map \"[v1-middle]\" -y /tmp/%s.mp4" % chunk_id)
	chunk_ids.append(chunk_id)
	chunk_sub_idx+=1

	cmd = [
			common.FFMPEG_BIN,
			"-i %s -i %s" % (from_path, to_path),
			"-filter_complex \"%s\"" % ";".join(filters),
			" ".join(outs)
		]
	common.executeCmd(" ".join(cmd))

	# Upload and save chunks data
	for cid in chunk_ids:
		chunk_url = uploadChunk(project_id, cid, "/tmp/%s.mp4" % cid)
		saveChunkData(project_id, cid, chunk_url)

	# Update counter_chunks
	numLeft = common.decrementCounter(project_id, 'counter_chunks')
	if numLeft == 0:
		render_video_function_name = context.function_name.replace("render_transition", "render_video")
		event = {'project_id': project_id}
		common.invokeLambda(render_video_function_name, event)

def updateCounter(project_id, context):
	# Update counter_chunks
	numLeft = common.decrementCounter(project_id, 'counter_chunks')
	if numLeft == 0:
		render_video_function_name = context.function_name.replace("render_transition", "render_video")
		event = {'project_id': project_id}
		common.invokeLambda(render_video_function_name, event)

def getChunkId(chunk_idx, chunk_sub_idx):
	return "chunk_%03d_%i" % (chunk_idx, chunk_sub_idx)
def uploadChunk(project_id, chunk_id, file):
	return common.uploadS3(file, "%s/%s.mp4" % (project_id,chunk_id))

def saveChunkData(project_id, chunk_id, chunk_url):
	common.saveToDynamo({"id":project_id, 'item':chunk_id, 'chunkData':{"url":chunk_url}})

def getSlideData(project_id, slide):
	try:
		response = dynamodb.Table(os.environ['DYNAMODB_TABLE']).get_item(
			Key={
				'id': project_id,
				'item': slide
			}
		)
	except ClientError as e:
		print(e.response['Error']['Message'])
		return {}
	else:
		return response['Item']['slideData']


# event={
# 	'project_id':"3Cpn9KsMyE52XnseCm8sVXKf",
# 	'slide_from':"slide_001",
# 	'slide_to':"slide_001",
# 	'chunk_idx':0
# }
# handler(event,{})