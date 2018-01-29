#============================================================
#
# CatAndCastle LLC, 2018
#============================================================

import os,json
import boto3
import logging
import random
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

	proj_id = event["id"]
	slides = event["slides"]
	animation = AnimationType()

	n=0
	for slide in slides:
		slide_id = "%s_%i" % (proj_id, n)
		slide["id"] = slide_id
		slide["project_id"] = proj_id
		if slide["slideType"] == "sectionHeader":
			a = animation.random()
		else:
			slide['animation'] = animation.next()
		# Push slide to render table.. or SNS?
		# print("Slide Json:")
		# print(json.dumps(slide, indent=4))
		log.debug("Slide JSON {}".format(json.dumps(slide)))

		topic_arn = "arn:aws:sns:us-east-1:%s:%s" % (context.invoked_function_arn.split(":")[4], os.environ['RENDER_SLIDE_SNS'])
		response = sns_client.publish(
		    TopicArn=topic_arn,
		    Message=json.dumps({'default': json.dumps(slide)}),
		    Subject=slide_id,
		    MessageStructure='json'
		)

		n=n+1
	

	num_slides = len(slides)
	setCounter(proj_id, num_slides)

	return {
        'statusCode': 200,
        'body': json.dumps({"numSlides":num_slides})
    }

# def validate(slide):


def setCounter(proj_id, num):
	table = dynamodb.Table(DYNAMODB_TABLE)
	table.put_item(
		Item={
		'id': proj_id,
		'numSlides': num
		})
		