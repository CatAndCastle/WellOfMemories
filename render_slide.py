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

sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
COUNTER_TABLE = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

here = os.path.dirname(os.path.realpath(__file__))
IMG_PATH = "/tmp/img.jpg"
VIDEO_PATH = "/tmp/slide.mp4"

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, decimal.Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
		return super(DecimalEncoder, self).default(o)

def handler(event, context):
	common.cleanup()

	log.debug("Received event {}".format(json.dumps(event)))
	# message = json.loads(event['Records'][0]['Sns']['Message'])
	# log.debug("Parsed message {}".format(message))

	project_id = event["project_id"]

	s = Slide(event)
	s.render()
	
	# UPDATE COUNTER
	numSlidesLeft = updateCounter(project_id)

	if numSlidesLeft == 0:
		triggerTransitions(project_id, context)
		# # TODO: Send SNS to combine slides
		# print("DONE WITH SLIDES ----> ")
		# # print("TODO: send to combine queue")
		# topic_arn = "arn:aws:sns:us-east-1:%s:%s" % (context.invoked_function_arn.split(":")[4], os.environ['RENDER_VIDEO_SNS'])
		# response = sns_client.publish(
		#     TopicArn=topic_arn,
		#     Message=json.dumps({'default': json.dumps({"project_id":proj_id})}),
		#     Subject=proj_id,
		#     MessageStructure='json'
		# )

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
	num_pairs = 0
	chunk_idx = 0
	lambda_function_name = context.function_name.replace("render_slide", "render_transition")

	while chunk_idx < len(slides['Items'])-1:
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
		num_pairs+=1

def updateCounter(project_id):
	current = readCounter(project_id)

	print("Attempting conditional update...")
	try:
		response = COUNTER_TABLE.update_item(
			Key={
				'id': project_id,
				'item':'counter'
			},
			UpdateExpression="SET numSlides = numSlides - :incr",
			ConditionExpression="numSlides = :current",
			ExpressionAttributeValues={
				':incr': decimal.Decimal(1),
				':current': current
			},
			ReturnValues="UPDATED_NEW"
		)
	except ClientError as e:
		print("UpdateItem failed:")
		# print(json.dumps(e.response, indent=4, cls=DecimalEncoder))
		if e.response['Error']['Code'] == "ConditionalCheckFailedException":
			print(e.response['Error']['Message'])
			# Retry
			return updateCounter(proj_id)
		else:
			raise
	else:
		print("UpdateItem succeeded:")
		print(json.dumps(response, indent=4, cls=DecimalEncoder))
		return response["Attributes"]["numSlides"]

def readCounter(proj_id):
	try:
		response = COUNTER_TABLE.get_item(
			Key={
				'id': proj_id,
				'item':'counter'
			}
		)
	except ClientError as e:
		print(e.response['Error']['Message'])
	else:
		item = response['Item']
		print("GetItem succeeded:")
		print(json.dumps(item, indent=4, cls=DecimalEncoder))
		return item['numSlides']