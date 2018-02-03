#============================================================
#
# CatAndCastle LLC, 2018
#============================================================

import os,json
import boto3
import logging
import random
import src.common as common
log = logging.getLogger()
log.setLevel(logging.DEBUG)

sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']

class AnimationType:
	def __init__(self):
		self.a = self.random()
	def random(self):
		if random.random() > 0.5:
			self.a = 'panup'
		else:
			self.a = 'pandown'
		return self.a
	def next(self):
		if self.a == 'pandown':
			self.a = 'panup'
		else:
			self.a = 'pandown'
		return self.a


def handler(event, context):
	log.debug("Received event {}".format(json.dumps(event)))
	print context.function_name

	project_id = event["id"]
	slides = event["slides"]
	animation = AnimationType()

	n=0
	for slide in slides:
		slide_id = "%s_%03d" % (project_id, n)
		slide["id"] = slide_id
		slide["idx"] = n
		slide["project_id"] = project_id
		if slide["slideType"] == "sectionHeader":
			a = animation.random()
		else:
			slide['animation'] = animation.next()
		
		log.debug("Slide JSON {}".format(json.dumps(slide)))
		#Invoke Lambda to render slide
		function_name = context.function_name.replace("new_video", "render_slide")
		common.invokeLambda(function_name, slide)

		# topic_arn = "arn:aws:sns:us-east-1:%s:%s" % (context.invoked_function_arn.split(":")[4], os.environ['RENDER_SLIDE_SNS'])
		# response = sns_client.publish(
		#     TopicArn=topic_arn,
		#     Message=json.dumps({'default': json.dumps(slide)}),
		#     Subject=slide_id,
		#     MessageStructure='json'
		# )

		n=n+1
	

	num_slides = len(slides)
	setCounter(project_id, num_slides)
	saveProjectInfo(event)

	return {
        'statusCode': 200,
        'body': json.dumps({"numSlides":num_slides})
    }

# def validate(slide):


def saveProjectInfo(data):
	table = dynamodb.Table(DYNAMODB_TABLE)
	table.put_item(
		Item={
		'id': data['id'],
		'item':'info',
		'data': {
			'webhookUrl': data['webhookUrl'],
			'fileName': data['fileName'],
			"audioUrl": data['audioUrl']
			}
		})

def setCounter(project_id, num):
	table = dynamodb.Table(DYNAMODB_TABLE)
	table.put_item(
		Item={
		'id': project_id,
		'item':'counter',
		'numSlides': num
		})
		