#============================================================
# render_slide.py
# AWS Lamdda Function
#
# CatAndCastle LLC, 2018
#============================================================
import sys,os,json,urllib,decimal
import src.common as common
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from src.slide import Slide
from src.slide import SlideRenderError, SlideRenderDurationError
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')


def handler(event, context):
	# clear /tmp folder
	common.cleanup()
	log.debug("Received event {}".format(json.dumps(event)))
	
	project_id = event["project_id"]
	s = Slide(event)
	# try:
	s.render()

	if not s.error:
		# UPDATE COUNTER
		numSlidesLeft = common.decrementCounter(project_id, 'counter_slides')
		if numSlidesLeft == 0:
			triggerTransitions(project_id, context)

def noSlidesToRender(project_id):
	common.notifyWebhook(project_id, "", "error")


def triggerTransitions(project_id, context):
	# get all rendered slides	
	slides = dynamodb.Table(os.environ['DYNAMODB_TABLE']).query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').begins_with('slide_')
	)

	if len(slides['Items'])<1:
		# If all the slides failed, and this is being triggered from handle_deadletter() 
		# - end the render process
		noSlidesToRender(project_id)
	elif len(slides['Items'])==1:
		# If only one slide rendered -> save it as chunk_000_0 and trigger video render
		common.saveToDynamo({"id":project_id, 'item':'chunk_000_0', 'chunkData':{"url":slides['Items'][0]["slideData"]["renderedUrl"]}})
		render_video_function_name = context.function_name.replace("render_slide", "render_video")
		event = {'project_id': project_id}
		common.invokeLambda(render_video_function_name, event)
	else:
		# render transition for each pair
		chunk_idx = 0
		lambda_function_name = context.function_name.replace("render_slide", "render_transition")
		num_transitions = len(slides['Items'])-1
		
		# Set chunks counter
		dynamodb.Table(os.environ['DYNAMODB_TABLE']).put_item(
			Item={
			'id': project_id,
			'item':'counter_chunks',
			'num': num_transitions
			})

		# Trigger render_transition function for each pair of slides
		while chunk_idx < num_transitions:
			slide_from = slides['Items'][chunk_idx]['item']
			slide_to = slides['Items'][chunk_idx+1]['item']
			event = {
				'project_id': project_id,
				'slide_from': slide_from,
				'slide_to': slide_to,
				'chunk_idx': chunk_idx
			}
			common.invokeLambda(lambda_function_name, event)
			chunk_idx+=1

def handle_deadletter(event, context):
	log.debug("Received event {}".format(json.dumps(event)))
	message = json.loads(event['Records'][0]['Sns']['Message'])
	log.debug("Parsed message {}".format(message))

	# push error to dynamo
	common.saveToDynamo(
		{'id': message["project_id"],
		'item': "error_%03d" % message["idx"],
		'slideData': message
		})

	numSlidesLeft = common.decrementCounter(message["project_id"], 'counter_slides')
	if numSlidesLeft == 0:
		triggerTransitions(message["project_id"], context)

#
# Testing:
#
# event = {
# 	"slideType": "photo",
# 	"resourceUrl": "https://s3.amazonaws.com/wellofmemories.catandcastle.com/resources/2-AcademyYears/1-academyyears12.jpg",
# 	"renderedUrl": "https://s3.amazonaws.com/dev.wom.com/3Cpn9KsMyE52XnseCm8sVXKf/slide_1.mp4",
# 	"duration": 7.0,
# 	"transitionIn": "fadeIn",
# 	"transitionInStart": 1,
# 	"transitionInDuration": 2.2,
# 	"transitionInColor": "#000000",
# 	"transitionOutColor": "#000000",
# 	"transitionOut": "fadeToColor",
# 	"transitionOutStart": 5.0,
# 	"transitionOutDuration": 2.0,
# 	"animation":"panup",
# 	"idx":1,
# 	"id":"3Cpn9KsMyE52XnseCm8sVXKf_001",
# 	"project_id":"3Cpn9KsMyE52XnseCm8sVXKf"
# }
# event={
# 	"project_id":"aaaaaaaaaaaaaaaaaaaaaaaa",
# 	"animation":"panup",
# 	  "slideType": "photo",
# 	  "resourceUrl": "https://s3.amazonaws.com/wellofmemories.catandcastle.com/resources/7-Survivalist+_+Adventurer/9-wilderness4.jpg",
# 	  "duration": 7,
# 	  "transitionOut": "fadeOutOverNext",
# 	  "transitionOutDuration": 2,
# 	  "transitionOutStart": 5
# 	}
# handler(event, {})
# 