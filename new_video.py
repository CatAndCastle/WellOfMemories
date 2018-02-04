#============================================================
#
# CatAndCastle LLC, 2018
#============================================================

import sys,os,json,random
import boto3
import logging
import src.common as common
import src.validate as Validator
log = logging.getLogger()
log.setLevel(logging.DEBUG)

sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

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

	# Validate input	
	try:
		Validator.parse(event)
	except ValueError as e:
		print(json.dumps(e.args[0], indent=4))
		return {
	        'statusCode': 400,
	        'body': json.dumps(e.args[0])
	    }
	# print(json.dumps(event, indent=4))
	# sys.exit(0)

	project_id = event["id"]
	slides = event["slides"]
	animation = AnimationType()

	setCounter(project_id, len(slides))

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
		render_slide_function = context.function_name.replace("new_video", "render_slide")
		common.invokeLambda(render_slide_function, slide)
		n=n+1
		
	saveProjectInfo(event)

	return {
        'statusCode': 200,
        'body': json.dumps({"numSlides":len(slides)})
    }

def saveProjectInfo(data):
	table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
	table.put_item(
		Item={
		'id': data['id'],
		'item':'info',
		'data': {
			'webhookUrl': data['webhookUrl'],
			'fileName': data['fileName'],
			'folderName': data['folderName'],
			"audioUrl": data['audioUrl']
			}
		})

def setCounter(project_id, num):
	table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
	table.put_item(
		Item={
		'id': project_id,
		'item':'counter_slides',
		'num': num
		})

# test
# event = json.load(open(os.environ['LAMBDA_TASK_ROOT']+'/new_video.json'))
# handler(event,{})
