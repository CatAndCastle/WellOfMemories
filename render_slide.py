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
import logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

dynamodb = boto3.resource('dynamodb')
sys.path.append(os.environ['LAMBDA_TASK_ROOT'] + "/dependencies/")


def handler(event, context):
	common.cleanup()
	log.debug("Received event {}".format(json.dumps(event)))

	project_id = event["project_id"]
	s = Slide(event)
	s.render()
	
	# UPDATE COUNTER
	numSlidesLeft = common.decrementCounter(project_id, 'counter_slides')
	if numSlidesLeft == 0:
		triggerTransitions(project_id, context)

	return {
        'statusCode': 200,
        'body': json.dumps({"message": "OK"})
    }

def triggerTransitions(project_id, context):
	# get all rendered slides	
	slides = dynamodb.Table(os.environ['DYNAMODB_TABLE']).query(
		KeyConditionExpression=Key('id').eq(project_id) & Key('item').begins_with('slide_')
	)
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
# handler(event, {})
